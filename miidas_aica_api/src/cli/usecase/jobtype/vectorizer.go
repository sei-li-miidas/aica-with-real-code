package jobtype

import (
	"aica/api/domain/jobtype"
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
	jobtypes, err := jobtype.NewJobTypeRepository(uc.semanticSearchDB).All()
	if err != nil {
		uc.logger.Error("Failed to retrieve job types", "error", err)
		return err
	}

	if jobtypes == nil {
		uc.logger.Error("job types not found")
		return errors.New("job types not found")
	}

	startTime := time.Now()

	numChunks, err := uc.embedAndWrite(jobtypes)
	if err != nil {
		return err
	}

	endTime := time.Now()
	uc.logger.Info("Processing stats", "Total processing time", endTime.Sub(startTime), "numChunks", numChunks)

	return nil
}

func (uc *VectorizerUseCase) embedAndWrite(jobtypes []*jobtype.JobTypeSmall) (int, error) {
	if err := jobtype.NewJobTypeRepository(uc.semanticSearchDB).DeleteAll(); err != nil {
		return 0, err
	}

	vectorizerProvider, err := vectorizer.NewVectorizerRepository(uc.provider, uc.logger)
	if err != nil {
		return 0, err
	}

	targets := lo.Map(jobtypes, func(j *jobtype.JobTypeSmall, _ int) *vectorizer.EmbeddingTarget {
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
			"job_type_small_id": result.ID,
			"chunk_seq":         result.ChunkSeq,
			"chunk":             result.Chunk,
			"embedding":         result.Embedding,
		}
	})

	return uc.semanticSearchDB.Model(jobtype.JobTypeSmallVector{}).Create(records).Error
}
