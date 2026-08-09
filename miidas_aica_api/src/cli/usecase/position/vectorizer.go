package position

import (
	"aica/api/cli/domain/aica"
	"aica/api/domain/position"
	"aica/api/domain/provider"
	miidasPosition "aica/api/domain/user/apply/position"
	"aica/api/domain/vectorizer"
	"aica/api/sdk/logger"
	"encoding/json"
	"time"

	"github.com/samber/lo"
)

type migrationRepository interface {
	GetLastImportedAtAndSourceID(tableName string) (*time.Time, *int, error)
	Save(migration *aica.Migrations) error
}
type miidasPositionRepository interface {
	GetLatest(importedAt time.Time, sourceID int, chunkSize int) (miidasPosition.Positions, error)
}

type positionVectorRepository interface {
	Create(positionVectors []*position.PositionVector) error
	Delete(positionID []miidasPosition.ID) error
}

type (
	VectorizerUseCase struct {
		logger                   logger.LevelLogger
		migrationRepository      migrationRepository
		miidasPositionRepository miidasPositionRepository
		positionVectorRepository positionVectorRepository
		vectorizerFactory        vectorizer.VectorizerFactory
		provider                 provider.Provider
		batchSize                int
	}

	MigrationResultDetail struct {
		Errors               []string         `json:"errors"`
		PublishedPositions   []map[string]any `json:"published_positions"`
		UnpublishedPositions []map[string]any `json:"unpublished_positions"`
	}
)

func NewVectorizerUseCase(
	logger logger.LevelLogger,
	migrationRepository migrationRepository,
	miidasPositionRepository miidasPositionRepository,
	positionVectorRepository positionVectorRepository,
	vectorizerFactory vectorizer.VectorizerFactory,
	provider provider.Provider,
	batchSize int,
) *VectorizerUseCase {
	return &VectorizerUseCase{
		logger:                   logger,
		migrationRepository:      migrationRepository,
		miidasPositionRepository: miidasPositionRepository,
		positionVectorRepository: positionVectorRepository,
		vectorizerFactory:        vectorizerFactory,
		provider:                 provider,
		batchSize:                batchSize,
	}
}

func (uc *VectorizerUseCase) Execute() error {
	migrationDetail := MigrationResultDetail{
		Errors:               []string{},
		PublishedPositions:   []map[string]any{},
		UnpublishedPositions: []map[string]any{},
	}

	currentMigration := &aica.Migrations{
		Name:           "position",
		LastImportedAt: time.Time{},
		LastSourceID:   0,
	}

	lastImportedAt, lastSourceID, err := uc.migrationRepository.GetLastImportedAtAndSourceID("position")
	if err != nil {
		uc.logger.Error("Failed to retrieve last_imported_at and source_id", "error", err)
		return err
	}

	if lastImportedAt != nil {
		currentMigration.LastImportedAt = *lastImportedAt
	}

	if lastSourceID != nil {
		currentMigration.LastSourceID = *lastSourceID
	}

	uc.logger.Info("last_imported_at and source_id", "lastImportedAt", lastImportedAt, "lastSourceID", lastSourceID)

	for {
		positions, err := uc.miidasPositionRepository.GetLatest(currentMigration.LastImportedAt, currentMigration.LastSourceID, uc.batchSize)
		if err != nil {
			scpErr := uc.saveCheckPoint(currentMigration, &migrationDetail, err)
			if scpErr != nil {
				return scpErr
			}

			uc.logger.Error("Failed to retrieve positions", "error", err)
			return err
		}

		uc.logger.Info(
			"positions chunk fetched",
			"count", len(positions),
			"lastImportedAt", currentMigration.LastImportedAt,
			"lastSourceID", currentMigration.LastSourceID,
			"batchSize", uc.batchSize,
		)

		if len(positions) == 0 {
			uc.logger.Info(
				"positions not found",
				"lastImportedAt", currentMigration.LastImportedAt,
				"lastSourceID", currentMigration.LastSourceID,
				"batchSize", uc.batchSize,
			)
			break
		}

		publishedPositions := lo.Filter(positions, func(p *miidasPosition.Position, _ int) bool {
			return p.PublishedAt != nil
		})

		uc.logger.Info(
			"published positions",
			"count", len(publishedPositions),
			"lastImportedAt", currentMigration.LastImportedAt,
			"lastSourceID", currentMigration.LastSourceID,
			"batchSize", uc.batchSize,
		)

		if len(publishedPositions) > 0 {
			err = uc.processPublishedChunk(publishedPositions)
			if err != nil {
				scpErr := uc.saveCheckPoint(currentMigration, &migrationDetail, err)
				if scpErr != nil {
					return scpErr
				}

				return err
			}

			mappedPublishedPositions := lo.Map(publishedPositions, func(p *miidasPosition.Position, _ int) map[string]any {
				return map[string]any{
					"id":          p.ID,
					"imported_at": p.ImportedAt,
				}
			})
			migrationDetail.PublishedPositions = append(migrationDetail.PublishedPositions, mappedPublishedPositions...)
		}

		unPublishedPositions := lo.Filter(positions, func(p *miidasPosition.Position, _ int) bool {
			return p.PublishedAt == nil
		})

		uc.logger.Info(
			"unpublished positions",
			"count", len(unPublishedPositions),
			"lastImportedAt", currentMigration.LastImportedAt,
			"lastSourceID", currentMigration.LastSourceID,
			"batchSize", uc.batchSize,
		)

		if len(unPublishedPositions) > 0 {
			err = uc.processUnpublishedChunk(unPublishedPositions)
			if err != nil {
				scpErr := uc.saveCheckPoint(currentMigration, &migrationDetail, err)
				if scpErr != nil {
					return scpErr
				}

				return err
			}

			mappedUnpublishedPositions := lo.Map(unPublishedPositions, func(p *miidasPosition.Position, _ int) map[string]any {
				return map[string]any{
					"id":          p.ID,
					"imported_at": p.ImportedAt,
				}
			})
			migrationDetail.UnpublishedPositions = append(migrationDetail.UnpublishedPositions, mappedUnpublishedPositions...)
		}

		lastRecord := positions[len(positions)-1]
		currentMigration.LastImportedAt = lastRecord.ImportedAt
		currentMigration.LastSourceID = int(lastRecord.ID)

		err = uc.saveCheckPoint(currentMigration, &migrationDetail, nil)
		if err != nil {
			return err
		}
	}

	return nil
}

func (uc *VectorizerUseCase) processPublishedChunk(positions []*miidasPosition.Position) error {
	startTime := time.Now()

	targetPositionIDs := lo.Map(positions, func(p *miidasPosition.Position, _ int) miidasPosition.ID {
		return p.ID
	})

	if err := uc.positionVectorRepository.Delete(targetPositionIDs); err != nil {
		uc.logger.Error("Failed to delete position vectors before overwrite", "error", err)
		return err
	}

	numChunks, err := uc.embedAndWrite(positions)
	if err != nil {
		return err
	}

	endTime := time.Now()
	uc.logger.Info("Processing stats", "Total processing time", endTime.Sub(startTime), "numChunks", numChunks)

	return nil
}

func (uc *VectorizerUseCase) processUnpublishedChunk(positions []*miidasPosition.Position) error {
	positionIDs := lo.Map(positions, func(p *miidasPosition.Position, _ int) miidasPosition.ID {
		return p.ID
	})

	err := uc.positionVectorRepository.Delete(positionIDs)
	if err != nil {
		uc.logger.Error("Failed to delete position vectors chunk", "error", err)
		return err
	}
	return nil
}

func (uc *VectorizerUseCase) saveCheckPoint(migration *aica.Migrations, migrationDetail *MigrationResultDetail, err error) error {
	if err != nil {
		migrationDetail.Errors = append(migrationDetail.Errors, err.Error())
	}

	migration.Detail, err = json.Marshal(migrationDetail)
	if err != nil {
		uc.logger.Error("Failed to marshal migration detail", "error", err)
		return err
	}
	migration.FinishedAt = time.Now()

	err = uc.migrationRepository.Save(migration)
	if err != nil {
		uc.logger.Error("Failed to save migration", "error", err)
		return err
	}
	return nil
}

func (uc *VectorizerUseCase) embedAndWrite(positions []*miidasPosition.Position) (int, error) {
	vectorizerProvider, err := uc.vectorizerFactory(uc.provider, uc.logger)
	if err != nil {
		return 0, err
	}

	targets := lo.Map(positions, func(p *miidasPosition.Position, _ int) *vectorizer.EmbeddingTarget {
		return &vectorizer.EmbeddingTarget{
			ID:   int(p.ID),
			Text: p.MainJobText,
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
	records := lo.Map(embeddingResults, func(result *vectorizer.EmbeddingResult, _ int) *position.PositionVector {
		return &position.PositionVector{
			PositionID: miidasPosition.ID(result.ID),
			ChunkSeq:   result.ChunkSeq,
			Chunk:      result.Chunk,
			Embedding:  result.Embedding,
		}
	})
	err := uc.positionVectorRepository.Create(records)
	if err != nil {
		uc.logger.Error("Failed to create position vectors", "error", err)
		return err
	}

	return nil
}
