package vectorizer

import (
	"aica/api/domain/provider"
	"aica/api/sdk/logger"
	"errors"

	"github.com/pgvector/pgvector-go"
	"github.com/tmc/langchaingo/textsplitter"
)

const (
	defaultDimensions   = 1024
	defaultChunkSize    = 800
	defaultChunkOverlap = 400
)

var (
	defaultSeparators                           = []string{"\n\n", "\n", ".", "?", "!", " ", ""}
	splitter          textsplitter.TextSplitter = textsplitter.NewRecursiveCharacter()
)

func init() {
	options := textsplitter.DefaultOptions()
	textsplitter.WithChunkSize(defaultChunkSize)(&options)
	textsplitter.WithChunkOverlap(defaultChunkOverlap)(&options)
	textsplitter.WithSeparators(defaultSeparators)(&options)
}

type EmbeddingTarget struct {
	ID   int
	Text string
}

type EmbeddingResult struct {
	ID        int
	ChunkSeq  int
	Chunk     string
	Embedding pgvector.Vector `pg:"type:vector(1024)"`
}

type VectorizerRepository interface {
	GenerateEmbedding(text string) (*pgvector.Vector, error)
	GenerateEmbeddings(embeddingTargets []*EmbeddingTarget) ([]*EmbeddingResult, error)
}

type VectorizerFactory func(p provider.Provider, logger logger.LevelLogger) (VectorizerRepository, error)

func NewVectorizerRepository(p provider.Provider, logger logger.LevelLogger) (VectorizerRepository, error) {
	switch p {
	case provider.ProviderBedrock:
		logger.Info("Using Bedrock vectorizer")
		return NewBedrockVectorizerRepository(logger), nil
	case provider.ProviderOpenAI:
		logger.Info("Using OpenAI vectorizer")
		return NewOpenAIVectorizerRepository(logger), nil
	default:
		logger.Error("Unknown vectorizer provider", "provider", p)
		return nil, errors.New("unknown vectorizer provider")
	}
}
