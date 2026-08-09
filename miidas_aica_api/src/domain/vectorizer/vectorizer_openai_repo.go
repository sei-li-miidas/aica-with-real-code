package vectorizer

import (
	"aica/api/sdk/logger"
	"context"
	"errors"
	"math"
	"net"
	"os"
	"syscall"
	"time"

	"github.com/cenkalti/backoff/v5"
	"github.com/pgvector/pgvector-go"
	"github.com/pkoukk/tiktoken-go"
	"github.com/samber/lo"
	"github.com/sashabaranov/go-openai"
)

const (
	// "001"で終わる非推奨のモデルは使用しないでください
	// 参照: https://github.com/openai/openai-python/issues/418#issuecomment-1525939500
	defaultModel = "text-embedding-3-small"

	openaiMaxChunksPerBatch = 1024
	openaiMaxTokensPerChunk = 8192
	maxRetryCount           = 3 // 最大リトライ回数
)

var apiKey = os.Getenv("OPENAI_API_KEY")

type OpenAIVectorizerRepository struct {
	logger   logger.LevelLogger
	encoding *tiktoken.Tiktoken
}

func NewOpenAIVectorizerRepository(logger logger.LevelLogger) *OpenAIVectorizerRepository {
	encoding, err := tiktoken.EncodingForModel(defaultModel)
	if err != nil {
		logger.Warn("Failed to initialize tiktoken encoding", "error", err)
	}
	return &OpenAIVectorizerRepository{
		logger:   logger,
		encoding: encoding,
	}
}

func (o *OpenAIVectorizerRepository) GenerateEmbedding(text string) (*pgvector.Vector, error) {
	embeddings, err := o.doEmbed([]string{text})
	if err != nil {
		o.logger.Error("Generating embeddings failed", "error", err)
		return nil, err
	}
	o.logger.Info("embeddings", "count", len(embeddings))

	if len(embeddings) != 1 {
		o.logger.Error("len(*embeddings) is NOT 1", "len(embeddings)", len(embeddings))
		return nil, errors.New("len(*embeddings) is NOT 1")
	}

	embedding := pgvector.NewVector((embeddings)[0])

	return &embedding, nil
}

func (o *OpenAIVectorizerRepository) GenerateEmbeddings(embeddingTargets []*EmbeddingTarget) ([]*EmbeddingResult, error) {
	recordsWithoutEmbeddings := []*EmbeddingResult{}

	documents := []string{}
	for _, target := range embeddingTargets {
		chunks, err := splitter.SplitText(target.Text)

		if err != nil {
			o.logger.Error("Splitting failed", "ID", target.ID, "error", err)
		}

		for i, chunk := range chunks {
			if tokenCount, err := o.countTokens(chunk); err != nil {
				o.logger.Warn("Failed to count tokens for chunk", "ID", target.ID, "chunkSeq", i, "error", err)
			} else if tokenCount > openaiMaxTokensPerChunk {
				o.logger.Warn("Chunk exceeds max token limit", "ID", target.ID, "chunkSeq", i, "tokenCount", tokenCount, "chunk", chunk)
			}

			recordsWithoutEmbeddings = append(recordsWithoutEmbeddings, &EmbeddingResult{
				ID:       target.ID,
				ChunkSeq: i,
				Chunk:    chunk,
			})

			documents = append(documents, chunk)
		}
	}

	embeddings, err := o.doEmbed(documents)
	if err != nil {
		ids := lo.Map(embeddingTargets, func(target *EmbeddingTarget, _ int) int { return target.ID })
		o.logger.Error("Generating embeddings failed", "IDs", ids, "error", err)
		return nil, err
	}

	if len(documents) != len(embeddings) {
		o.logger.Error("Mismatch between embeddings and documents", "len(embeddings)", len(embeddings), "len(records)", len(documents))
		return nil, errors.New("mismatch between embeddings and documents")
	}

	records := []*EmbeddingResult{}
	for _, record := range lo.Zip2(recordsWithoutEmbeddings, embeddings) {
		records = append(records, &EmbeddingResult{
			ID:        record.A.ID,
			ChunkSeq:  record.A.ChunkSeq,
			Chunk:     record.A.Chunk,
			Embedding: pgvector.NewVector(record.B),
		})
	}

	return records, nil
}

// リトライすべきエラーかどうかをチェックします
func (o *OpenAIVectorizerRepository) isRetryableError(err error) bool {
	var apiError *openai.APIError
	if errors.As(err, &apiError) {
		switch apiError.HTTPStatusCode {
		case 429: // Too Many Requests — レート制限超過またはクォータ超過
			return true
		case 500: // Internal Server Error — OpenAI側の内部エラー
			return true
		case 502: // Bad Gateway — アップストリーム/ゲートウェイ障害
			return true
		case 503: // Service Unavailable — 過負荷または一時的にダウン
			return true
		case 504: // Gateway Timeout — サーバーが時間内に応答しなかった
			return true
		default:
			return false
		}
	}

	// ネットワーク/トランスポートエラーをチェック
	var netError net.Error
	if errors.As(err, &netError) {
		// タイムアウトエラーのみリトライ対象とする
		return netError.Timeout()
	}

	// 接続関連のエラーをチェック
	var opError *net.OpError
	if errors.As(err, &opError) {
		return true
	}

	// システムコールエラーをチェック（接続リセットなど）
	var syscallError *os.SyscallError
	if errors.As(err, &syscallError) {
		switch syscallError.Err {
		case syscall.ECONNRESET, syscall.ECONNREFUSED, syscall.ETIMEDOUT:
			return true
		}
	}

	// コンテキストのデッドライン超過またはキャンセル（ただし、ユーザー主導のキャンセルではない）
	if errors.Is(err, context.DeadlineExceeded) {
		return true
	}

	return false
}

func (o *OpenAIVectorizerRepository) doEmbed(documents []string) ([][]float32, error) {
	if apiKey == "" {
		o.logger.Error("Set OPENAI_API_KEY")
		return nil, errors.New("set OPENAI_API_KEY")
	}

	client := openai.NewClient(apiKey)

	embeddings := [][]float32{}
	numOfBatches := math.Ceil(float64(len(documents)) / float64(openaiMaxChunksPerBatch))
	totalDuration := 0.0
	for i := 0; i < int(numOfBatches); i += openaiMaxChunksPerBatch {
		batchNum := i/openaiMaxChunksPerBatch + 1
		batch := lo.Subset(documents, i, uint(lo.Min([]int{i + openaiMaxChunksPerBatch, len(documents)})))

		o.logger.Info("OpenAI Request initiated", "batchNum", batchNum, "numOfBatches", numOfBatches)
		o.logger.Info("Chunks for this batch", "len(batch)", len(batch))
		startTime := time.Now()

		// ユーザークエリ用のEmbeddingRequestを作成
		req := openai.EmbeddingRequest{
			Input:      batch,
			Model:      defaultModel,
			Dimensions: defaultDimensions,
		}

		// ベクトル作成リクエスト（最大試行回数制限付き）
		res, err := backoff.Retry(context.TODO(), func() (openai.EmbeddingResponse, error) {
			res, err := client.CreateEmbeddings(context.Background(), req)

			if err != nil {
				o.logger.Error("Error creating query embedding", "error", err)

				if o.isRetryableError(err) {
					o.logger.Warn("Retryable error encountered, will retry", "error", err)
					return openai.EmbeddingResponse{}, err
				} else {
					o.logger.Error("Non-retryable error encountered", "error", err)
					return openai.EmbeddingResponse{}, backoff.Permanent(err)
				}
			}

			return res, nil
		}, backoff.WithBackOff(backoff.NewExponentialBackOff()), backoff.WithMaxTries(uint(maxRetryCount+1)))

		if err != nil {
			o.logger.Error("Error creating query embedding after retries", "error", err, "maxRetries", maxRetryCount)
			return nil, err
		}

		requestDuration := time.Since(startTime).Seconds()
		totalDuration += requestDuration
		o.logger.Info("OpenAI Request completed", "batchNum", batchNum, "numOfBatches", numOfBatches, "requestDuration", requestDuration, "Tokens usage", res.Usage.TotalTokens)

		embeddings = append(embeddings, lo.Map(res.Data, func(embedding openai.Embedding, _ int) []float32 {
			return embedding.Embedding
		})...)
	}
	o.logger.Info("Total duration for all requests", "totalDuration", totalDuration)

	return embeddings, nil
}

func (o *OpenAIVectorizerRepository) countTokens(text string) (int, error) {
	if o.encoding == nil {
		return 0, errors.New("tiktoken encoding is not initialized")
	}
	tokens := o.encoding.Encode(text, nil, nil)
	return len(tokens), nil
}
