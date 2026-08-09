package support

import (
	pinterfaces "aica/api/api/mcptool/usecase/position/interfaces"
	pmodel "aica/api/api/mcptool/usecase/position/model"
	"aica/api/domain/position"
	"aica/api/domain/search"
	mposition "aica/api/domain/user/apply/position"
	"aica/api/domain/vectorizer"
	"aica/api/sdk/aws/s3"
	merr "aica/api/sdk/error"
	"aica/api/sdk/grpc"
	"aica/api/sdk/http"
	"aica/api/sdk/logger"
	"miidas/m2/user/marketvalue/grpc/iface"
	"time"

	"github.com/samber/lo"

	"gorm.io/gorm"
)

// MV2の検索結果からポジションの意味情報検索の距離順の結果を返す
// 意味情報検索のパラメータがなければMV2の結果のまま
func GetPositionSearchResultsFromPositionIDs(
	keyword string,
	vectorizerRepository vectorizer.VectorizerRepository,
	positionVectorRepository search.SemanticSearchRepository[*position.PositionSearchResult],
	positionIDs []mposition.ID,
) ([]*position.PositionSearchResult, error) {
	if len(keyword) == 0 {
		// 意味情報検索のパラメータがなければMV2の検索結果の順番のまま
		result := lo.Map(positionIDs, func(id mposition.ID, _ int) *position.PositionSearchResult {
			return &position.PositionSearchResult{ID: id}
		})
		return result, nil
	}

	positionVectorsParams := http.NewDefaultVectorSearchParams(keyword)
	positionSearchResult, err := SemanticSearch(vectorizerRepository, positionVectorRepository, &positionVectorsParams, positionIDs)
	if err != nil {
		return nil, err
	}

	seen := make(map[mposition.ID]struct{}, len(positionSearchResult))
	uniquePositions := make([]*position.PositionSearchResult, 0, len(positionSearchResult))
	for _, p := range positionSearchResult {
		if _, found := seen[p.ID]; found {
			continue
		}

		seen[p.ID] = struct{}{}
		uniquePositions = append(uniquePositions, p)
	}

	return uniquePositions, nil

}

func FillPositionData(positionRepository pinterfaces.PositionGetter, logger logger.LevelLogger, positionIds []mposition.ID) ([]*pmodel.PositionSummary, error) {
	if len(positionIds) == 0 {
		return []*pmodel.PositionSummary{}, nil
	}

	miidasPositions, err := positionRepository.GetByIDs(positionIds)
	if err != nil {
		return nil, err
	}

	var positions []*pmodel.PositionSummary
	for _, pId := range positionIds {
		p, ok := lo.Find(miidasPositions, func(p *mposition.Position) bool {
			return p.ID == pId
		})

		if !ok {
			logger.Warn("ポジションが見つかりませんでした。", "positionID", pId)
			continue
		}

		rp := &pmodel.PositionSummary{
			ID:          pId,
			Title:       p.Title,
			MainJobText: p.MainJobText,
		}
		if p.GuaranteedIncome != nil {
			rp.SalaryFrom = p.GuaranteedIncome.BulkIncomeFrom
			rp.SalaryTo = p.GuaranteedIncome.BulkIncomeTo
		}

		if len(p.Images) > 0 {
			images := lo.Filter(p.Images, func(i mposition.Image, _ int) bool {
				return i.DisplayType == 1
			})
			if len(images) > 0 {
				url, err := s3.GetImageUrl(images[0].FilePath)
				if err != nil {
					logger.Warn("画像URLの生成に失敗しました。", "filePath", images[0].FilePath, "error", err)
				} else {
					rp.Image = url.String()
				}
			}
		}

		positions = append(positions, rp)
	}

	return positions, nil
}

func SemanticSearch(vectorizerProvider vectorizer.VectorizerRepository, positionVectorRepository search.SemanticSearchRepository[*position.PositionSearchResult], params *http.VectorSearchParams, positionIds []mposition.ID) ([]*position.PositionSearchResult, error) {
	embeddings, err := vectorizerProvider.GenerateEmbedding(params.Keyword)
	if err != nil {
		return nil, err
	}

	var addConditions func(*gorm.DB) *gorm.DB
	if len(positionIds) > 0 {
		addConditions = func(query *gorm.DB) *gorm.DB {
			return query.Where("position_id IN ?", lo.Map(positionIds, func(id mposition.ID, _ int) int {
				return int(id)
			}))
		}
	}

	positionVectors, err := positionVectorRepository.SemanticSearch(embeddings.String(), params.Distance, addConditions)
	if err != nil {
		return nil, err
	}

	return positionVectors, nil
}

func ExecutePositionSearch(
	logger logger.LevelLogger,
	getWillPositionList func(companyWill *iface.Company, businessWill *iface.Business, positionWill *iface.Position) ([]*iface.PositionListEntry, error),
	companyWill *iface.Company,
	businessWill *iface.Business,
	positionWill *iface.Position,
	keyword string,
	vectorizerRepository vectorizer.VectorizerRepository,
	positionVectorRepository search.SemanticSearchRepository[*position.PositionSearchResult],
	positionRepository pinterfaces.PositionGetter,
) ([]mposition.ID, []*pmodel.PositionSummary, error) {
	startTime := time.Now()

	list, err := getWillPositionList(companyWill, businessWill, positionWill)
	if err != nil {
		if grpc.ShouldIgnoreErr(err) {
			return nil, nil, merr.ErrClientClosedRequest.WithStack()
		}
		logger.Error("マッチングサーバーとの通信に失敗", "err", err)
		return nil, nil, merr.ErrInternalServer.WithCause(err)
	}

	logger.Info("analyze_position_search_time", "duration", time.Since(startTime).Milliseconds(), "job_type_small_id_count", len(positionWill.Job.Value.Smalls))
	logger.Info("ポジション検索結果件数", "count", len(list))
	if len(list) == 0 {
		return nil, nil, nil
	}

	allPositionIds := lo.Map(list, func(p *iface.PositionListEntry, _ int) mposition.ID { return mposition.ID(p.PositionId) })

	positionSearchResult, err := GetPositionSearchResultsFromPositionIDs(
		keyword,
		vectorizerRepository,
		positionVectorRepository,
		allPositionIds,
	)
	if err != nil {
		return nil, nil, err
	}

	allPositionIds = lo.Map(positionSearchResult, func(p *position.PositionSearchResult, _ int) mposition.ID {
		return p.ID
	})
	positionIDs := lo.Subset(allPositionIds, 0, http.POSITION_SEARCH_DEFAULT_LIMIT)

	positions, err := FillPositionData(positionRepository, logger, positionIDs)
	if err != nil {
		return nil, nil, err
	}

	logger.Info("ポジション検索結果", "allPositionIds", allPositionIds, "positions_count", len(positions))

	return allPositionIds, positions, nil
}
