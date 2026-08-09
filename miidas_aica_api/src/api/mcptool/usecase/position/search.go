package position

import (
	pbuilder "aica/api/api/mcptool/usecase/position/builder"
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	pinterfaces "aica/api/api/mcptool/usecase/position/interfaces"
	pmodel "aica/api/api/mcptool/usecase/position/model"
	psupport "aica/api/api/mcptool/usecase/position/support"
	address "aica/api/api/mcptool/usecase/shared"
	"aica/api/domain/position"
	"aica/api/domain/search"
	mposition "aica/api/domain/user/apply/position"
	"aica/api/domain/vectorizer"
	merr "aica/api/sdk/error"
	"aica/api/sdk/logger"
	"context"
	"errors"
	"fmt"
	"miidas/m2/user/marketvalue/grpc/iface"

	"github.com/samber/lo"
)

type willPositionGetter interface {
	GetWillPositionList(companyWill *iface.Company, businessWill *iface.Business, positionWill *iface.Position) ([]*iface.PositionListEntry, error)
}

// GenericSearchUseCase
type GenericSearchUseCase struct {
	logger                   logger.LevelLogger
	mvGateway                willPositionGetter
	vectorizerRepository     vectorizer.VectorizerRepository
	positionVectorRepository search.SemanticSearchRepository[*position.PositionSearchResult]
	positionRepository       pinterfaces.PositionGetter
	validator                pinterfaces.PositionSearchValidator
	locationLookup           pinterfaces.LocationLookup
}

// NewGenericSearchUseCase は汎用求人検索ユースケースを生成する。
// 検証、勤務地解決、検索実行、セマンティック検索補助に必要な依存を受け取り、1 つのユースケースへ束ねる。
func NewGenericSearchUseCase(
	l logger.LevelLogger,
	mvGateway willPositionGetter,
	vectorizerRepository vectorizer.VectorizerRepository,
	positionVectorRepository search.SemanticSearchRepository[*position.PositionSearchResult],
	positionRepository pinterfaces.PositionGetter,
	validator pinterfaces.PositionSearchValidator,
	locationLookup pinterfaces.LocationLookup,
) *GenericSearchUseCase {
	return &GenericSearchUseCase{
		logger:                   l,
		mvGateway:                mvGateway,
		vectorizerRepository:     vectorizerRepository,
		positionVectorRepository: positionVectorRepository,
		positionRepository:       positionRepository,
		validator:                validator,
		locationLookup:           locationLookup,
	}
}

// ExecuteByInputWithResolvedJobTypeIDs は外部入力に近い検索パラメータを受け取り、前処理を行った上で検索を実行する。
// 入力検証、休日・残業条件の妥当性確認、勤務地 ID 解決を済ませ、解決済み職種 ID とともに Execute へ処理を委譲する。
func (uc *GenericSearchUseCase) ExecuteByInputWithResolvedJobTypeIDs(
	ctx context.Context,
	params *pmodel.GenericPositionSearchParams,
	resolvedJobTypeSmallIDs []int,
	theme pcontracts.PositionRecommendationTheme,
) ([]mposition.ID, []*pmodel.PositionSummary, error) {
	if uc.validator == nil {
		return nil, nil, merr.ErrInternalServer.WithCause(errors.New("position search validator is not configured"))
	}
	if uc.locationLookup == nil {
		return nil, nil, merr.ErrInternalServer.WithCause(errors.New("position search dependencies are not configured"))
	}
	if err := uc.validator.ValidatePositionSearchParams(params); err != nil {
		return nil, nil, merr.ErrInvalidRequest.WithCause(err)
	}
	if _, err := psupport.ConvertDayOffs(params.DayOffs); err != nil {
		return nil, nil, merr.ErrInvalidRequest.WithCause(err)
	}
	if _, err := psupport.ConvertAverageOvertime(params.AverageOvertime); err != nil {
		return nil, nil, merr.ErrInvalidRequest.WithCause(err)
	}

	cityIDs, err := psupport.ResolveLocationIDs(uc.locationLookup, params)
	if err != nil {
		return nil, nil, err
	}

	if len(resolvedJobTypeSmallIDs) == 0 {
		return nil, nil, merr.ErrInvalidRequest.WithCause(
			fmt.Errorf("正しい職種名を指定してください。"),
		)
	}

	return uc.Execute(ctx, params, cityIDs, resolvedJobTypeSmallIDs, theme)
}

// Execute は検索に必要な数値 ID 群がそろった状態から、検索条件の will を構築して検索本体へ渡す。
// テーマ検索でない場合だけ休日・残業条件を will に反映し、フルリモート条件の有無も含めて executeSearch を呼び出す。
func (uc *GenericSearchUseCase) Execute(
	ctx context.Context,
	params *pmodel.GenericPositionSearchParams,
	cityIDs []int,
	jobTypeSmallIDs []int,
	theme pcontracts.PositionRecommendationTheme,
) ([]mposition.ID, []*pmodel.PositionSummary, error) {
	will := &pcontracts.PositionSearchWill{
		Salary:          params.Salary,
		CityIDs:         toInt32IDs(cityIDs),
		JobTypeSmallIDs: toInt32IDs(jobTypeSmallIDs),
	}
	if theme == "" {
		dayOffs, err := psupport.ConvertDayOffs(params.DayOffs)
		if err != nil {
			return nil, nil, merr.ErrInvalidRequest.WithCause(err)
		}
		averageOvertime, err := psupport.ConvertAverageOvertime(params.AverageOvertime)
		if err != nil {
			return nil, nil, merr.ErrInvalidRequest.WithCause(err)
		}
		will.DayOffs = dayOffs
		will.AverageOvertime = averageOvertime
	}

	return uc.executeSearch(
		will,
		params.PositionKeyword,
		theme,
		hasFullRemoteLocation(params.Locations),
	)
}

// executeSearch は will から実際の検索条件オブジェクトを作り、ポジション検索を実行する中核処理である。
// テーマ有無で base/theme 用の will を作り分け、フルリモート指定時は勤務地条件を上書きしてから検索実行ヘルパーへ委譲する。
func (uc *GenericSearchUseCase) executeSearch(
	will *pcontracts.PositionSearchWill,
	semanticKeyword string,
	theme pcontracts.PositionRecommendationTheme,
	isFullyRemoteWork bool,
) ([]mposition.ID, []*pmodel.PositionSummary, error) {
	var companyWill *iface.Company
	var businessWill *iface.Business
	var positionWill *iface.Position
	if len(theme) > 0 {
		companyWill = pbuilder.CreateCompanyWillForTheme(will, theme)
		businessWill = pbuilder.CreateBusinessWillForTheme(will, theme)
		positionWill = pbuilder.CreatePositionWillForTheme(will, theme)
	} else {
		companyWill = pbuilder.CreateBaseCompanyWill(will)
		businessWill = pbuilder.CreateBaseBusinessWill(will)
		positionWill = pbuilder.CreateBasePositionWill(will)
	}

	if isFullyRemoteWork {
		positionWill.WorkAddress.Importance = 0
		positionWill.WorkAddress.Value = &iface.WorkAddressValue{}
		positionWill.RemoteWork.Importance = 3
		positionWill.RemoteWork.Value = &iface.RemoteWorkValue{
			Exists:          []int32{2, 3},
			OfficeFrequency: []int32{1},
		}
	}

	uc.logger.Info("ポジション検索条件", "will", will)
	uc.logger.Info("ポジション検索条件", "theme", theme)
	uc.logger.Info("ポジション検索条件", "companyWill", companyWill)
	uc.logger.Info("ポジション検索条件", "businessWill", businessWill)
	uc.logger.Info("ポジション検索条件", "positionWill", positionWill)

	return psupport.ExecutePositionSearch(
		uc.logger,
		uc.mvGateway.GetWillPositionList,
		companyWill,
		businessWill,
		positionWill,
		semanticKeyword,
		uc.vectorizerRepository,
		uc.positionVectorRepository,
		uc.positionRepository,
	)
}

// toInt32IDs は int 配列を検索 API が要求する int32 配列へ変換する。
// ID リストの型だけを揃えるための単純な変換を行う補助関数である。
func toInt32IDs(values []int) []int32 {
	return lo.Map(values, func(v int, _ int) int32 { return int32(v) })
}

// hasFullRemoteLocation は勤務地条件の中にフルリモート勤務指定が含まれているかを判定する。
// 1 件でも完全リモートの location type が見つかった時点で true を返し、検索条件調整に利用する。
func hasFullRemoteLocation(locations []*address.LocationRequest) bool {
	for _, location := range locations {
		if location.LocationType == address.LOCATION_TYPE_FULL_REMOTE_WORK {
			return true
		}
	}
	return false
}
