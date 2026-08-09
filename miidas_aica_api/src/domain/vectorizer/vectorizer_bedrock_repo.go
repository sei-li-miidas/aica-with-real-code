package vectorizer

import (
	"context"
	"encoding/json"

	"aica/api/sdk/logger"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/bedrockruntime"
	"github.com/cenkalti/backoff/v5"
	"github.com/pgvector/pgvector-go"
	"github.com/samber/lo"
)

const (
	titanEmbeddingModelID = "amazon.titan-embed-text-v2:0" //https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids-arns.html
	region                = "ap-northeast-1"
)

type (
	BedrockVectorizerRepository struct {
		brc    *bedrockruntime.Client
		logger logger.LevelLogger
	}

	Request struct {
		InputText  string `json:"inputText"`
		Dimensions int    `json:"dimensions,omitempty"`
		Normalize  bool   `json:"normalize,omitempty"`
	}

	Response struct {
		Embedding           []float64 `json:"embedding"`
		InputTextTokenCount int       `json:"inputTextTokenCount"`
	}
)

func NewBedrockVectorizerRepository(logger logger.LevelLogger) *BedrockVectorizerRepository {
	return &BedrockVectorizerRepository{
		logger: logger,
	}
}

func (b *BedrockVectorizerRepository) init() error {
	if b.brc == nil {
		cfg, err := config.LoadDefaultConfig(context.Background(), config.WithRegion(region))
		if err != nil {
			b.logger.Error("Failed to load AWS config", "error", err)
			return err
		}

		b.brc = bedrockruntime.NewFromConfig(cfg)
	}

	return nil

}

func (b *BedrockVectorizerRepository) GenerateEmbedding(text string) (*pgvector.Vector, error) {
	err := b.init()
	if err != nil {
		return nil, err
	}

	payload := Request{
		InputText:  text,
		Dimensions: defaultDimensions,
		Normalize:  true,
	}

	payloadBytes, err := json.Marshal(payload)
	if err != nil {
		b.logger.Error("Failed to marshal payload", "error", err)
		return nil, err
	}

	output, err := b.brc.InvokeModel(context.Background(), &bedrockruntime.InvokeModelInput{
		Body:        payloadBytes,
		ModelId:     aws.String(titanEmbeddingModelID),
		ContentType: aws.String("application/json"),
	})
	if err != nil {
		b.logger.Error("Failed to invoke model", "error", err)
		return nil, err
	}

	var resp Response
	err = json.Unmarshal(output.Body, &resp)
	if err != nil {
		b.logger.Error("Failed to unmarshal response", "error", err)
		return nil, err
	}

	// TODO: float64 to float32は、間違った結果ができる可能性？
	embedding := pgvector.NewVector(lo.Map(resp.Embedding, func(v float64, _ int) float32 {
		return float32(v)
	}))
	return &embedding, nil
}

// TODO: OpenAIのようなバッチEmbeddings生成できるみたい
// https://huggingface.co/amazon/Titan-text-embeddings-v2#bedrock-titan-text-embeddings-v2
func (b *BedrockVectorizerRepository) GenerateEmbeddings(embeddingTargets []*EmbeddingTarget) ([]*EmbeddingResult, error) {
	err := b.init()
	if err != nil {
		return nil, err
	}

	records := []*EmbeddingResult{}
	for _, target := range embeddingTargets {
		chunks, err := splitter.SplitText(target.Text)
		if err != nil {
			b.logger.Error("Splitting failed", "ID", target.ID, "error", err)
		}

		for i, chunk := range chunks {
			embedding, err := backoff.Retry(context.Background(), func() (*pgvector.Vector, error) {
				return b.GenerateEmbedding(chunk)
			}, backoff.WithBackOff(backoff.NewExponentialBackOff()))

			if err != nil {
				b.logger.Error("Generating embedding failed", "ID", target.ID, "error", err)
				break
			}

			records = append(records, &EmbeddingResult{
				ID:        target.ID,
				ChunkSeq:  i,
				Chunk:     chunk,
				Embedding: *embedding,
			})
		}
	}

	return records, nil
}
