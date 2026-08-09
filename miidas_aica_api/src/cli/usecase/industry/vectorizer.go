package industry

import (
	"aica/api/domain/industry"
	"aica/api/domain/provider"
	"aica/api/domain/vectorizer"
	"aica/api/sdk/logger"
	"errors"
	"time"

	"github.com/samber/lo"
	"gorm.io/gorm"
)

type VectorizerUseCase struct {
	logger           logger.LevelLogger
	semanticSearchDB *gorm.DB
	provider         provider.Provider
}

func NewVectorizerUseCase(
	logger logger.LevelLogger,
	semanticSearchDB *gorm.DB,
	provider provider.Provider,
) *VectorizerUseCase {
	return &VectorizerUseCase{
		logger:           logger,
		semanticSearchDB: semanticSearchDB,
		provider:         provider,
	}
}

func (uc *VectorizerUseCase) Execute() error {
	industries, err := industry.NewIndustrySmallRepository(uc.semanticSearchDB).All()
	if err != nil {
		uc.logger.Error("Failed to retrieve industries", "error", err)
		return err
	}

	if industries == nil {
		uc.logger.Error("industries not found")
		return errors.New("industries not found")
	}

	startTime := time.Now()

	numChunks, err := uc.embedAndWrite(industries)
	if err != nil {
		return err
	}

	endTime := time.Now()
	uc.logger.Info("Processing stats", "Total processing time", endTime.Sub(startTime), "numChunks", numChunks)

	return nil
}

func (uc *VectorizerUseCase) embedAndWrite(industries []*industry.IndustrySmall) (int, error) {
	if err := industry.NewIndustrySmallRepository(uc.semanticSearchDB).DeleteAll(); err != nil {
		return 0, err
	}

	vectorizerProvider, err := vectorizer.NewVectorizerRepository(uc.provider, uc.logger)
	if err != nil {
		return 0, err
	}

	targets := lo.Map(industries, func(j *industry.IndustrySmall, _ int) *vectorizer.EmbeddingTarget {
		return &vectorizer.EmbeddingTarget{
			ID:   j.ID,
			Text: j.Description,
		}
	})
	records, err := vectorizerProvider.GenerateEmbeddings(targets)
	if err != nil {
		return 0, err
	}

	if err = uc.copyEmbeddings(records); err != nil {
		return 0, err
	}

	return len(records), nil
}

func (uc *VectorizerUseCase) copyEmbeddings(embeddingResults []*vectorizer.EmbeddingResult) error {
	records := lo.Map(embeddingResults, func(result *vectorizer.EmbeddingResult, _ int) map[string]any {
		return map[string]any{
			"industry_small_id": result.ID,
			"chunk_seq":         result.ChunkSeq,
			"chunk":             result.Chunk,
			"embedding":         result.Embedding,
		}
	})

	return uc.semanticSearchDB.Model(industry.IndustrySmallVector{}).Create(records).Error
}
