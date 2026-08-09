package position

import (
	positionDTO "aica/api/api/mcptool/http/position/dto"
	positionMapper "aica/api/api/mcptool/http/position/mapper"
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	pinterfaces "aica/api/api/mcptool/usecase/position/interfaces"
	pmodel "aica/api/api/mcptool/usecase/position/model"
	jobSpecificParams "aica/api/api/mcptool/usecase/position/params"
	address "aica/api/api/mcptool/usecase/shared"
	jobfilter "aica/api/domain/jobfilter"
	"aica/api/domain/public/master"
	mPosition "aica/api/domain/user/apply/position"
	mecho "aica/api/sdk/echo"
	mectx "aica/api/sdk/echo/context"
	merr "aica/api/sdk/error"
	"aica/api/sdk/logger"
	"context"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"strings"

	"github.com/labstack/echo/v4"
)

type (
	GenericSearchUseCase interface {
		ExecuteByInputWithResolvedJobTypeIDs(ctx context.Context, params *pmodel.GenericPositionSearchParams, resolvedJobTypeIDs []int, theme pcontracts.PositionRecommendationTheme) ([]mPosition.ID, []*pmodel.PositionSummary, error)
	}

	DetailUseCase interface {
		Execute(ctx context.Context, id mPosition.ID) (*pmodel.PositionDetail, error)
	}

	SummariesUseCase interface {
		Execute(positionIDs []mPosition.ID) ([]*pmodel.PositionSummary, error)
	}

	SearchWithJobTypeUseCase interface {
		Execute(sessionID string, input *pcontracts.JobSpecificSearchInput) ([]mPosition.ID, []*pmodel.PositionSummary, *jobfilter.JobSearchFilter, error)
		ExecuteWithThemeBySession(sessionID string, jobTypeLargeID master.JobTypeLargeID, theme pcontracts.PositionRecommendationTheme) ([]mPosition.ID, []*pmodel.PositionSummary, error)
	}

	JobTypesSelectedUseCase interface {
		Execute(sessionID string, req *pmodel.JobTypesSelection) (*pmodel.JobTypesSelectionResult, error)
	}

	JobTypeSearchFilterUseCase interface {
		Execute(sessionID string, req *pmodel.JobTypeSearchFilterQuery) (*pmodel.JobTypeSearchFilter, error)
	}
)

type HandlerDependencies struct {
	NewGenericSearchUseCase         func(l logger.LevelLogger) GenericSearchUseCase
	NewJobTypeSmallIDResolver       func(l logger.LevelLogger) pcontracts.JobSpecificSearchResolver
	NewDetailUseCase                func(l logger.LevelLogger) DetailUseCase
	NewSummariesUseCase             func(l logger.LevelLogger) SummariesUseCase
	NewSearchWithJobTypeUseCase     func(l logger.LevelLogger, enablePersistence bool) (SearchWithJobTypeUseCase, error)
	NewGenericSearchFilterPersister func(l logger.LevelLogger) pinterfaces.JobSearchFilterGenericPersister
	NewJobSearchFilterReader        func(l logger.LevelLogger) pinterfaces.JobSearchFilterReader
	NewJobTypesSelectedUseCase      func(l logger.LevelLogger) JobTypesSelectedUseCase
	NewJobTypeSearchFilterUseCase   func(l logger.LevelLogger) JobTypeSearchFilterUseCase
	JobTypeSearchToolResolver       pinterfaces.JobTypeSearchToolResolver
}

type Handler struct {
	newGenericSearchUseCase         func(l logger.LevelLogger) GenericSearchUseCase
	newJobTypeSmallIDResolver       func(l logger.LevelLogger) pcontracts.JobSpecificSearchResolver
	newDetailUseCase                func(l logger.LevelLogger) DetailUseCase
	newSummariesUseCase             func(l logger.LevelLogger) SummariesUseCase
	newSearchWithJobTypeUseCase     func(l logger.LevelLogger, enablePersistence bool) (SearchWithJobTypeUseCase, error)
	newGenericSearchFilterPersister func(l logger.LevelLogger) pinterfaces.JobSearchFilterGenericPersister
	newJobSearchFilterReader        func(l logger.LevelLogger) pinterfaces.JobSearchFilterReader
	newJobTypesSelectedUseCase      func(l logger.LevelLogger) JobTypesSelectedUseCase
	newJobTypeSearchFilterUseCase   func(l logger.LevelLogger) JobTypeSearchFilterUseCase
	jobTypeSearchToolResolver       pinterfaces.JobTypeSearchToolResolver
}

const sessionIDHeader = "X-SESSION-ID"

// NewHandler は HTTP ハンドラに必要な依存オブジェクトをまとめて保持する Handler を生成する。
// 各ユースケースやリゾルバはここで注入され、実際のリクエスト処理時に必要に応じて利用される。
func NewHandler(deps HandlerDependencies) *Handler {
	return &Handler{
		newGenericSearchUseCase:         deps.NewGenericSearchUseCase,
		newJobTypeSmallIDResolver:       deps.NewJobTypeSmallIDResolver,
		newDetailUseCase:                deps.NewDetailUseCase,
		newSummariesUseCase:             deps.NewSummariesUseCase,
		newSearchWithJobTypeUseCase:     deps.NewSearchWithJobTypeUseCase,
		newGenericSearchFilterPersister: deps.NewGenericSearchFilterPersister,
		newJobSearchFilterReader:        deps.NewJobSearchFilterReader,
		newJobTypesSelectedUseCase:      deps.NewJobTypesSelectedUseCase,
		newJobTypeSearchFilterUseCase:   deps.NewJobTypeSearchFilterUseCase,
		jobTypeSearchToolResolver:       deps.JobTypeSearchToolResolver,
	}
}

// search は検索リクエストの入口で、ToolName に応じて適切な検索処理へ振り分ける。
// まずリクエストボディ全体を読み込み、ToolName だけを先に取り出してどのリクエスト型で解釈すべきかを判定する。
// その後、判定結果に対応する構造体へ同じ JSON を再度デコードし、各検索実行メソッドへ処理を委譲する。
func (h *Handler) search(c echo.Context) error {
	// ボディは一度読むと再利用できないため、最初に全体をメモリへ取り込んで後続の判定とデコードで使い回す。
	rawBody, err := io.ReadAll(c.Request().Body)
	if err != nil {
		return echo.NewHTTPError(http.StatusBadRequest, err.Error())
	}

	// まず ToolName だけを確認し、どの検索種別として扱うべきかを決める。
	var probe struct {
		ToolName string `json:"ToolName"`
	}
	if err := json.Unmarshal(rawBody, &probe); err != nil {
		return echo.NewHTTPError(http.StatusBadRequest, err.Error())
	}

	// ToolName ごとに期待するリクエスト型が異なるため、分岐後に適切な DTO へデコードし直して専用処理へ渡す。
	switch strings.TrimSpace(probe.ToolName) {
	case pcontracts.ToolNameSearchJobPostingsForITEngineer:
		var req positionDTO.ITEngineerSearchRequest
		if err := json.Unmarshal(rawBody, &req); err != nil {
			return echo.NewHTTPError(http.StatusBadRequest, err.Error())
		}
		return h.executeITEngineerSearch(c, &req)
	case pcontracts.ToolNameSearchJobPostingsForSalesFinancialSales:
		var req positionDTO.FinancialSalesSearchRequest
		if err := json.Unmarshal(rawBody, &req); err != nil {
			return echo.NewHTTPError(http.StatusBadRequest, err.Error())
		}
		return h.executeFinancialSalesSearch(c, &req)
	default:
		var req positionDTO.PositionSearchRequest
		if err := json.Unmarshal(rawBody, &req); err != nil {
			return echo.NewHTTPError(http.StatusBadRequest, err.Error())
		}
		return h.executeGenericSearch(c, &req)
	}
}

// executeGenericSearch は汎用の検索リクエストを共通検索処理へ流し込み、必要に応じて検索条件も保存する。
// DTO を検索パラメータへ変換し、職種 ID 解決と検索実行を行った後、永続化結果の有無で返却するレスポンス形式を切り替える。
func (h *Handler) executeGenericSearch(c echo.Context, req *positionDTO.PositionSearchRequest) error {
	genericParams := positionMapper.ToGenericSearchParams(req)
	var persistedFilter *jobfilter.JobSearchFilter
	resolvedJobTypeIDs, err := h.resolveJobTypeIDs(c, genericParams.JobtypeNames)
	if err != nil {
		mectx.Logger(c).Error("failed to resolve jobtype small ids", "error", err)
		return err
	}

	allPositionIds, positions, err := h.commonSearch(c, genericParams, resolvedJobTypeIDs, pcontracts.PositionRecommendationTheme(""))
	if err != nil {
		mectx.Logger(c).Info("ポジション検索失敗しました。", "error", err)
		return err
	}
	if h.newGenericSearchFilterPersister != nil {
		persister := h.newGenericSearchFilterPersister(mectx.Logger(c))
		if persister != nil {
			persistedFilter, err = persister.PersistFromGenericSearchParams(sessionID(c), genericParams)
			if err != nil {
				mectx.Logger(c).Warn("failed to persist generic job_search_filter", "session_id", sessionID(c), "error", err)
			}
		}
	}

	if persistedFilter != nil {
		resp := positionMapper.ToSearchEnvelope(
			allPositionIds,
			positions,
			pmodel.PositionRecommendations(""),
			persistedFilter,
			pcontracts.ToolNameSearchJobPostings,
			h.jobtypeNamesWithSameSearchFilters(persistedFilter, pcontracts.ToolNameSearchJobPostings),
		)
		return c.JSON(http.StatusOK, resp)
	}

	resp := positionMapper.ToGenericSearchEnvelope(allPositionIds, positions, pmodel.PositionRecommendations(""), genericParams)
	return c.JSON(http.StatusOK, resp)
}

// detail は求人 ID を受け取り、対応する求人詳細を取得してレスポンスへ整形する。
// パスパラメータを検証してから詳細取得ユースケースを呼び出し、その結果を API 用 DTO に変換して返す。
func (h *Handler) detail(c echo.Context) error {
	id, err := mecho.GetFromParam[mPosition.ID](c, "position_id")
	if err != nil || id <= 0 {
		return merr.ErrInvalidRequest.WithStack()
	}

	uc := h.newDetailUseCase(mectx.Logger(c))
	if uc == nil {
		return merr.ErrInternalServer.WithCause(errors.New("detail usecase is not configured"))
	}
	detail, err := uc.Execute(c.Request().Context(), id)
	if err != nil {
		mectx.Logger(c).Error("failed to get position detail", "error", err, "position_id", id)
		return merr.ErrInternalServer.WithStack()
	}

	return c.JSON(http.StatusOK, positionMapper.ToDetailResponse(detail))
}

// commonSearch は汎用検索ユースケースの呼び出し部分を共通化するヘルパーである。
// 変換済みのドメイン用検索パラメータに、解決済み職種 ID と推薦テーマを付けて検索本体を実行する。
func (h *Handler) commonSearch(c echo.Context, params *pmodel.GenericPositionSearchParams, resolvedJobTypeIDs []int, theme pcontracts.PositionRecommendationTheme) ([]mPosition.ID, []*pmodel.PositionSummary, error) {
	uc := h.newGenericSearchUseCase(mectx.Logger(c))
	if uc == nil {
		return nil, nil, merr.ErrInternalServer.WithCause(errors.New("generic search usecase is not configured"))
	}
	return uc.ExecuteByInputWithResolvedJobTypeIDs(c.Request().Context(), params, resolvedJobTypeIDs, theme)
}

// recommendations はセッションに保存された直近の検索条件を再利用して、テーマ付きの推薦検索を行う。
// 保存済みフィルタを通常検索リクエストへ復元し、職種 ID 解決後に共通検索処理へ渡して結果を返す。
func (h *Handler) recommendations(c echo.Context) error {
	theme := c.Param("theme")

	reader := h.newJobSearchFilterReader(mectx.Logger(c))
	if reader == nil {
		return merr.ErrInternalServer.WithCause(errors.New("job search filter reader is not configured"))
	}

	filter, err := reader.GetBySessionID(sessionID(c))
	if err != nil {
		mectx.Logger(c).Error("failed to get job_search_filter for recommendations", "error", err, "session_id", sessionID(c))
		return err
	}
	if filter == nil {
		return merr.ErrInvalidRequest.WithCause(errors.New("job_search_filter is not found"))
	}
	req := genericSearchRequestFromFilter(filter)
	genericParams := positionMapper.ToGenericSearchParams(req)
	resolvedJobTypeIDs, err := h.resolveJobTypeIDs(c, genericParams.JobtypeNames)
	if err != nil {
		mectx.Logger(c).Error("failed to resolve jobtype small ids for recommendations", "error", err)
		return err
	}

	allPositionIds, positions, err := h.commonSearch(c, genericParams, resolvedJobTypeIDs, pcontracts.PositionRecommendationTheme(theme))
	if err != nil {
		mectx.Logger(c).Info("ポジション提案の検索に失敗しました。", "error", err)
		return err
	}

	resp := positionMapper.ToSearchEnvelope(allPositionIds, positions, nil, nil, "", nil)
	return c.JSON(http.StatusOK, resp)
}

// getBoundParamAs はコンテキストに格納されたバインド済みリクエストを指定型として取り出す。
// 型不一致や未バインド時はエラーを返し、ハンドラ側での入力取得を簡潔にしている。
func getBoundParamAs[T any](c echo.Context) (*T, error) {
	req, ok := mectx.BoundParam(c).(*T)
	if !ok || req == nil {
		return nil, merr.ErrBadParameter
	}
	return req, nil
}

// resolveJobTypeIDs は職種名の一覧を内部検索で扱う職種 ID の一覧へ変換する。
// リゾルバが未設定なら何もしないで nil を返し、設定済みなら small ID を int 配列へ詰め替えて返す。
func (h *Handler) resolveJobTypeIDs(c echo.Context, jobtypeNames []string) ([]int, error) {
	if h.newJobTypeSmallIDResolver == nil {
		return nil, nil
	}
	resolver := h.newJobTypeSmallIDResolver(mectx.Logger(c))
	if resolver == nil {
		return nil, nil
	}
	resolvedIDs, err := resolver.ResolveJobTypeSmallIDs(jobtypeNames)
	if err != nil {
		return nil, err
	}
	resolvedJobTypeIDs := make([]int, 0, len(resolvedIDs))
	for _, id := range resolvedIDs {
		resolvedJobTypeIDs = append(resolvedJobTypeIDs, int(id))
	}
	return resolvedJobTypeIDs, nil
}

// summaries は複数の求人 ID に対応する求人サマリ一覧を取得する。
// バインド済みリクエストから ID 群を取り出し、サマリ取得ユースケースの結果を検索レスポンス形式で返却する。
func (h *Handler) summaries(c echo.Context) error {
	params, err := getBoundParamAs[positionDTO.PositionSummariesRequest](c)
	if err != nil {
		return err
	}
	uc := h.newSummariesUseCase(mectx.Logger(c))
	if uc == nil {
		return merr.ErrInternalServer.WithCause(errors.New("summaries usecase is not configured"))
	}
	positions, err := uc.Execute(params.PositionIDs)
	if err != nil {
		mectx.Logger(c).Error("ポジションサマリ取得に失敗しました。", "error", err)
		return err
	}

	resp := positionMapper.ToSearchEnvelope(nil, positions, nil, nil, "", nil)
	return c.JSON(http.StatusOK, resp)
}

// searchITEngineer は IT エンジニア向け検索の入口で、入力取得だけを担当する。
// リクエストをバインド済み DTO として取り出し、実際の検索ロジックは executeITEngineerSearch に委譲する。
func (h *Handler) searchITEngineer(c echo.Context) error {
	req, err := getBoundParamAs[positionDTO.ITEngineerSearchRequest](c)
	if err != nil {
		return err
	}
	return h.executeITEngineerSearch(c, req)
}

// executeITEngineerSearch は IT エンジニア専用の検索条件を job-specific 検索入力へ変換して実行する。
// 共通条件と IT 固有条件をまとめた入力を作り、検索と検索条件保存を行うユースケースを呼び出して専用レスポンスを返す。
func (h *Handler) executeITEngineerSearch(c echo.Context, req *positionDTO.ITEngineerSearchRequest) error {
	logger := mectx.Logger(c)
	input := &pcontracts.JobSpecificSearchInput{
		JobTypeLargeID:           master.JobTypeLargeIDITSpecialist,
		JobTypeNames:             req.JobtypeNames,
		SelectedFilterOptionsKey: pcontracts.ToolNameSearchJobPostingsForITEngineer,
		Salary:                   req.Salary,
		Locations:                req.Locations,
		DayOffs:                  req.DayOffs,
		AverageOvertime:          req.AverageOvertime,
		Custom: &jobSpecificParams.ITEngineerParams{
			RemoteWorkPossible:      req.RemoteWorkPossible,
			PositionKeyword:         getString(req.PositionKeyword),
			ProgrammingLanguages:    getStringSlice(req.ProgrammingLanguages),
			ProjectScales:           getStringSlice(req.ProjectScales),
			ApplicationFrameworks:   getStringSlice(req.ApplicationFrameworks),
			CloudServices:           getStringSlice(req.CloudServices),
			Phases:                  getStringSlice(req.Phases),
			Positions:               getStringSlice(req.Positions),
			SystemScales:            getStringSlice(req.SystemScales),
			DevelopmentProjectTypes: getStringSlice(req.DevelopmentProjectTypes),
		},
	}

	uc, err := h.newSearchWithJobTypeUseCase(logger, true)
	if err != nil {
		return err
	}

	allPositionIds, positions, searchFilters, err := uc.Execute(sessionID(c), input)
	if err != nil {
		logger.Info("ポジション検索失敗しました。", "error", err)
		return err
	}

	resp := positionMapper.ToSearchEnvelope(
		allPositionIds,
		positions,
		pmodel.PositionRecommendations("it_engineer/"),
		searchFilters,
		pcontracts.ToolNameSearchJobPostingsForITEngineer,
		h.jobtypeNamesWithSameSearchFilters(searchFilters, pcontracts.ToolNameSearchJobPostingsForITEngineer),
	)
	return c.JSON(http.StatusOK, resp)
}

// searchITEngineerTheme は保存済みの IT エンジニア検索条件に対してテーマ付き推薦検索を実行する。
// セッション単位の条件を前提に、指定テーマだけを差し替えて job-specific ユースケースへ処理を委譲する。
func (h *Handler) searchITEngineerTheme(c echo.Context) error {
	logger := mectx.Logger(c)
	uc, err := h.newSearchWithJobTypeUseCase(logger, false)
	if err != nil {
		return err
	}
	allPositionIds, positions, err := uc.ExecuteWithThemeBySession(
		sessionID(c),
		master.JobTypeLargeIDITSpecialist,
		pcontracts.PositionRecommendationTheme(c.Param("theme")),
	)
	if err != nil {
		logger.Info("ポジション検索失敗しました。", "error", err)
		return err
	}

	resp := positionMapper.ToSearchEnvelope(allPositionIds, positions, nil, nil, "", nil)
	return c.JSON(http.StatusOK, resp)
}

// searchFinancialSales は金融営業向け検索の入口で、入力取得だけを行う薄いラッパーである。
// バインド済み DTO を取り出した後、検索本体は executeFinancialSalesSearch に任せる。
func (h *Handler) searchFinancialSales(c echo.Context) error {
	req, err := getBoundParamAs[positionDTO.FinancialSalesSearchRequest](c)
	if err != nil {
		return err
	}
	return h.executeFinancialSalesSearch(c, req)
}

// executeFinancialSalesSearch は金融営業専用の検索条件を検索入力へ変換して求人検索を実行する。
// 金融営業向けの custom 条件を組み立て、job-specific ユースケースで検索と条件保存を行い、専用レスポンスへ整形する。
func (h *Handler) executeFinancialSalesSearch(c echo.Context, req *positionDTO.FinancialSalesSearchRequest) error {
	logger := mectx.Logger(c)
	input := &pcontracts.JobSpecificSearchInput{
		JobTypeNames:             req.JobtypeNames,
		SelectedFilterOptionsKey: pcontracts.ToolNameSearchJobPostingsForSalesFinancialSales,
		Salary:                   req.Salary,
		Locations:                req.Locations,
		JobTypeLargeID:           master.JobTypeLargeIDFinancialSpecialist,
		DayOffs:                  req.DayOffs,
		AverageOvertime:          req.AverageOvertime,
		Custom: &jobSpecificParams.FinancialSalesParams{
			PositionKeyword:          getString(req.PositionKeyword),
			SalesStyleDive:           req.SalesStyleDive,
			HandledFinancialProducts: getStringSlice(req.HandledFinancialProducts),
			SalesMethodStyles:        getStringSlice(req.SalesMethodStyles),
			TargetCustomerTypes:      getStringSlice(req.TargetCustomerTypes),
			Qualifications:           getStringSlice(req.Qualifications),
			IndividualSalesStyles:    getStringSlice(req.IndividualSalesStyles),
			IncentiveSystem:          getString(req.IncentiveSystem),
		},
	}

	uc, err := h.newSearchWithJobTypeUseCase(logger, true)
	if err != nil {
		return err
	}

	allPositionIds, positions, searchFilters, err := uc.Execute(sessionID(c), input)
	if err != nil {
		logger.Info("ポジション検索失敗しました。", "error", err)
		return err
	}

	resp := positionMapper.ToSearchEnvelope(
		allPositionIds,
		positions,
		pmodel.PositionRecommendations("financial_sales/"),
		searchFilters,
		pcontracts.ToolNameSearchJobPostingsForSalesFinancialSales,
		h.jobtypeNamesWithSameSearchFilters(searchFilters, pcontracts.ToolNameSearchJobPostingsForSalesFinancialSales),
	)
	return c.JSON(http.StatusOK, resp)
}

// searchJobTypeSpecific は JobtypeNames から検索種別を推定して、適切な検索処理へ振り分ける入口である。
// まず職種名一覧だけを読み取ってツール名を分類し、その結果に応じた DTO へ再デコードして各実行メソッドへ委譲する。
func (h *Handler) searchJobTypeSpecific(c echo.Context) error {
	rawBody, err := io.ReadAll(c.Request().Body)
	if err != nil {
		return echo.NewHTTPError(http.StatusBadRequest, err.Error())
	}
	var probe struct {
		JobtypeNames []string `json:"JobtypeNames"`
	}
	if err := json.Unmarshal(rawBody, &probe); err != nil {
		return echo.NewHTTPError(http.StatusBadRequest, err.Error())
	}

	toolName, valid := h.classifyToolNameForJobtypes(probe.JobtypeNames)
	if !valid {
		return merr.ErrInvalidRequest.WithCause(errors.New("JobtypeNames must contain at least one non-empty element"))
	}

	switch toolName {
	case pcontracts.ToolNameSearchJobPostingsForITEngineer:
		var req positionDTO.ITEngineerSearchRequest
		if err := json.Unmarshal(rawBody, &req); err != nil {
			return echo.NewHTTPError(http.StatusBadRequest, err.Error())
		}
		return h.executeITEngineerSearch(c, &req)
	case pcontracts.ToolNameSearchJobPostingsForSalesFinancialSales:
		var req positionDTO.FinancialSalesSearchRequest
		if err := json.Unmarshal(rawBody, &req); err != nil {
			return echo.NewHTTPError(http.StatusBadRequest, err.Error())
		}
		return h.executeFinancialSalesSearch(c, &req)
	default:
		var req positionDTO.PositionSearchRequest
		if err := json.Unmarshal(rawBody, &req); err != nil {
			return echo.NewHTTPError(http.StatusBadRequest, err.Error())
		}
		return h.executeGenericSearch(c, &req)
	}
}

// classifyToolNameForJobtypes は職種名一覧が単一の専用検索ツールにまとまるかを判定する。
// 空文字を除いた各職種名を ToolName へ変換し、全て同じツールならその名前を返し、混在や未解決時は空文字へ寄せる。
func (h *Handler) classifyToolNameForJobtypes(jobtypeNames []string) (string, bool) {
	var toolName string
	hasNonEmpty := false
	for _, rawName := range jobtypeNames {
		name := strings.TrimSpace(rawName)
		if name == "" {
			continue
		}
		hasNonEmpty = true
		current := h.jobTypeSearchToolName(name)
		if current == "" {
			return "", true
		}
		if toolName == "" {
			toolName = current
			continue
		}
		if toolName != current {
			return "", true
		}
	}
	return toolName, hasNonEmpty
}

// searchFinancialSalesTheme は保存済みの金融営業検索条件に対してテーマ付き推薦検索を実行する。
// セッションに紐づく条件を前提に、金融営業の大分類 ID とテーマを指定してユースケースへ渡す。
func (h *Handler) searchFinancialSalesTheme(c echo.Context) error {
	logger := mectx.Logger(c)
	uc, err := h.newSearchWithJobTypeUseCase(logger, true)
	if err != nil {
		return err
	}
	allPositionIds, positions, err := uc.ExecuteWithThemeBySession(
		sessionID(c),
		master.JobTypeLargeIDFinancialSpecialist,
		pcontracts.PositionRecommendationTheme(c.Param("theme")),
	)
	if err != nil {
		logger.Info("ポジション検索失敗しました。", "error", err)
		return err
	}

	resp := positionMapper.ToSearchEnvelope(allPositionIds, positions, nil, nil, "", nil)
	return c.JSON(http.StatusOK, resp)
}

// jobTypesSelected はセッションに保存されている選択職種を更新する。
// リクエストをドメイン入力へ変換してユースケースへ渡し、更新後の状態をレスポンス DTO として返却する。
func (h *Handler) jobTypesSelected(c echo.Context) error {
	req, err := getBoundParamAs[positionDTO.JobTypesSelectionRequest](c)
	if err != nil {
		return err
	}
	uc := h.newJobTypesSelectedUseCase(mectx.Logger(c))
	if uc == nil {
		return merr.ErrInternalServer.WithCause(errors.New("job types selected usecase is not configured"))
	}

	requestSessionID := sessionID(c)
	result, err := uc.Execute(requestSessionID, positionMapper.ToJobTypesSelectedRequest(req))
	if err != nil {
		mectx.Logger(c).Error("failed to overwrite job_search_filter.jobtypes", "error", err, "session_id", requestSessionID)
		return err
	}

	return c.JSON(http.StatusOK, positionMapper.ToJobTypesSelectedResponse(result))
}

// jobTypesClear は現在セッションに保存されている職種選択を空に戻す。
// 既存の保存内容を確認し、選択済み職種がある場合だけ空の選択で上書きしてクリアする。
func (h *Handler) jobTypesClear(c echo.Context) error {
	requestSessionID := sessionID(c)
	if requestSessionID == "" {
		return merr.ErrInvalidRequest.WithCause(errors.New("X-Session-Id is required"))
	}
	reader := h.newJobSearchFilterReader(mectx.Logger(c))

	filter, err := reader.GetBySessionID(requestSessionID)
	if err != nil {
		mectx.Logger(c).Error("failed to get job_search_filter for clear", "error", err, "session_id", requestSessionID)
		return err
	}

	jobtypeNames := jobtypeNamesFromItems(filter)
	if len(jobtypeNames) == 0 {
		return c.JSON(http.StatusOK, map[string]any{})
	}

	uc := h.newJobTypesSelectedUseCase(mectx.Logger(c))
	if uc == nil {
		return merr.ErrInternalServer.WithCause(errors.New("job types selected usecase is not configured"))
	}

	if _, err := uc.Execute(requestSessionID, &pmodel.JobTypesSelection{}); err != nil {
		mectx.Logger(c).Error("failed to clear job_search_filter.jobtypes selection", "error", err, "session_id", requestSessionID)
		return err
	}

	return c.JSON(http.StatusOK, map[string]any{})
}

// jobTypeSearchFilter は指定された職種に対して利用可能な検索フィルタ定義を返す。
// 入力の職種名を検証した後、ユースケースからフィルタを取得し、その職種に対応する ToolName を付与して返却する。
func (h *Handler) jobTypeSearchFilter(c echo.Context) error {
	req, err := getBoundParamAs[positionDTO.JobTypeSearchFilterRequest](c)
	if err != nil {
		return err
	}
	if strings.TrimSpace(req.JobtypeName) == "" {
		return merr.ErrInvalidRequest.WithCause(errors.New("JobtypeName is required"))
	}
	uc := h.newJobTypeSearchFilterUseCase(mectx.Logger(c))
	if uc == nil {
		return merr.ErrInternalServer.WithCause(errors.New("job type search filter usecase is not configured"))
	}

	result, err := uc.Execute(sessionID(c), positionMapper.ToJobTypeSearchFilterRequest(req))
	if err != nil {
		mectx.Logger(c).Error("failed to get job type search filter", "error", err)
		return err
	}

	resp := positionMapper.ToJobTypeSearchFilterResponse(
		result.SearchFilter,
		h.jobTypeSearchToolName(req.JobtypeName),
	)
	return c.JSON(http.StatusOK, resp)
}

// currentJobTypeSearchFilter は現在セッションに保存されている職種特化検索フィルタを取得する。
// 未保存なら空レスポンスを返し、存在する場合は ToolName と同条件を共有する職種名一覧も合わせて組み立てる。
func (h *Handler) currentJobTypeSearchFilter(c echo.Context) error {
	uc := h.newJobTypeSearchFilterUseCase(mectx.Logger(c))
	if uc == nil {
		return merr.ErrInternalServer.WithCause(errors.New("job type search filter usecase is not configured"))
	}

	result, err := uc.Execute(sessionID(c), &pmodel.JobTypeSearchFilterQuery{})
	if err != nil {
		mectx.Logger(c).Error("failed to get current job type search filter", "error", err)
		return err
	}

	if result == nil {
		resp := positionMapper.ToCurrentJobTypeSearchFilterResponse(
			nil,
			"",
			nil,
		)
		return c.JSON(http.StatusOK, resp)
	} else {
		toolName := result.ToolName
		resp := positionMapper.ToCurrentJobTypeSearchFilterResponse(
			result.SearchFilter,
			toolName,
			h.jobtypeNamesWithSameSearchFilters(result.SearchFilter, toolName),
		)
		return c.JSON(http.StatusOK, resp)
	}
}

// jobTypeSearchToolName は職種名から対応する検索ツール名を取得する。
// リゾルバが利用できない場合は空文字を返し、利用できる場合は解決結果をそのまま返す。
func (h *Handler) jobTypeSearchToolName(jobTypeName string) string {
	if h == nil || h.jobTypeSearchToolResolver == nil {
		return ""
	}
	return h.jobTypeSearchToolResolver.ToolNameByJobtypeName(jobTypeName)
}

// jobtypeNamesByToolName は検索ツール名に紐づく職種名一覧を取得する。
// リゾルバ未設定時は nil を返し、設定済みなら対応する職種名の配列を返す。
func (h *Handler) jobtypeNamesByToolName(toolName string) []string {
	if h == nil || h.jobTypeSearchToolResolver == nil {
		return nil
	}
	return h.jobTypeSearchToolResolver.JobtypeNamesByToolName(toolName)
}

// jobtypeNamesWithSameSearchFilters は同じ検索フィルタ設定を共有する ToolName と職種名一覧の対応表を作る。
// 保存済みフィルタ内の Jobtypes を優先し、何も見つからない場合だけ fallback の ToolName から最低限の対応表を構成する。
func (h *Handler) jobtypeNamesWithSameSearchFilters(filter *jobfilter.JobSearchFilter, fallbackToolName string) map[string][]string {
	result := map[string][]string{}
	if filter != nil {
		for toolName := range filter.Jobtypes {
			normalizedToolName := strings.TrimSpace(toolName)
			if normalizedToolName == "" {
				continue
			}
			names := h.jobtypeNamesByToolName(normalizedToolName)
			if len(names) == 0 {
				continue
			}
			result[normalizedToolName] = names
		}
	}
	if len(result) > 0 {
		return result
	}

	normalizedToolName := strings.TrimSpace(fallbackToolName)
	if normalizedToolName == "" {
		return nil
	}
	names := h.jobtypeNamesByToolName(normalizedToolName)
	if len(names) == 0 {
		return nil
	}
	return map[string][]string{normalizedToolName: names}
}

func getStringSlice(values *[]string) []string {
	if values == nil {
		return nil
	}
	return *values
}

func sessionID(c echo.Context) string {
	return c.Request().Header.Get(sessionIDHeader)
}

func getString(value *string) string {
	if value == nil {
		return ""
	}
	return *value
}

// genericSearchRequestFromFilter は保存済み job_search_filter から汎用検索用リクエストを復元する。
// recommendations 系の再検索で使うため、汎用検索グループの職種・年収・勤務地を PositionSearchRequest に詰め替え、
// 共通キーワードが保存されていればそれも PositionKeyword として引き継ぐ。
func genericSearchRequestFromFilter(filter *jobfilter.JobSearchFilter) *positionDTO.PositionSearchRequest {
	if filter == nil {
		return &positionDTO.PositionSearchRequest{}
	}
	req := &positionDTO.PositionSearchRequest{
		PositionSearchCommonRequest: positionDTO.PositionSearchCommonRequest{
			JobtypeNames: selectedOrAllJobtypes(filter.Jobtypes[pcontracts.ToolNameSearchJobPostings]),
			Salary:       int32(filter.Salary),
			Locations:    genericSearchLocationsFromFilter(filter.Locations),
		},
	}

	if filter.PositionKeyword != nil {
		req.PositionSearchCommonRequest.PositionKeyword = filter.PositionKeyword
	}
	return req
}

// selectedOrAllJobtypes は職種 selectable item 群から検索に使う職種名一覧を取り出す。
// Selected=true が 1 件でもあればその値だけを返し、選択状態が無い場合は候補として保存されている全職種を返す。
func selectedOrAllJobtypes(jobtypes []*jobfilter.JobtypeSelectableItem) []string {
	// 明示的に選択されている職種名だけを集める。
	selected := make([]string, 0, len(jobtypes))
	// Selected が 1 件も無い場合に使うフォールバック候補。
	fallback := make([]string, 0, len(jobtypes))
	for _, item := range jobtypes {
		if item == nil || strings.TrimSpace(item.Value) == "" {
			continue
		}
		value := strings.TrimSpace(item.Value)
		fallback = append(fallback, value)
		if item.Selected {
			selected = append(selected, value)
		}
	}
	if len(selected) > 0 {
		return selected
	}
	return fallback
}

// genericSearchLocationsFromFilter は保存済み Locations から汎用検索の LocationRequest 一覧を復元する。
// Residence.Address は居住地、Residence.CommutingAreas は明示的な通勤圏、WorkLocations は希望勤務地または
// フルリモートとして扱い、保存形式から検索入力形式へ LocationType を戻しながら配列を組み立てる。
func genericSearchLocationsFromFilter(locations *jobfilter.JobSearchFilterLocations) []*address.LocationRequest {
	if locations == nil {
		return nil
	}
	// recommendations 再検索へ渡す LocationRequest を保存順に復元する。
	result := []*address.LocationRequest{}
	if locations.Residence != nil {
		if locations.Residence.Address != nil &&
			strings.TrimSpace(locations.Residence.Address.PrefectureName) != "" &&
			strings.TrimSpace(locations.Residence.Address.CityName) != "" {
			result = append(result, &address.LocationRequest{
				LocationType:   address.LOCATION_TYPE_RESIDENCE,
				PrefectureName: locations.Residence.Address.PrefectureName,
				CityName:       locations.Residence.Address.CityName,
			})
			for _, area := range locations.Residence.CommutingAreas {
				if area == nil || !area.Selected || strings.TrimSpace(area.PrefectureName) == "" || strings.TrimSpace(area.CityName) == "" {
					continue
				}
				result = append(result, &address.LocationRequest{
					LocationType:   address.LOCATION_TYPE_COMMUTING_AREAS,
					PrefectureName: area.PrefectureName,
					CityName:       area.CityName,
				})
			}
		}
	}
	for _, item := range locations.WorkLocations {
		if item == nil || !item.Selected {
			continue
		}
		if strings.TrimSpace(item.PrefectureName) == "" || strings.TrimSpace(item.CityName) == "" {
			continue
		}
		result = append(result, &address.LocationRequest{
			LocationType:   address.LOCATION_TYPE_WORK_LOCATION,
			PrefectureName: item.PrefectureName,
			CityName:       item.CityName,
		})
	}
	return result
}

// jobtypeNamesFromItems は job_search_filter 全体に保存されている職種名を重複なく列挙する。
// グループ単位の Selected 状態は見ず、保存されている Value を出現順に一意化して返すため、
// 「同条件を共有する職種名一覧」を組み立てる場面で利用する。
func jobtypeNamesFromItems(filter *jobfilter.JobSearchFilter) []string {
	if filter == nil || len(filter.Jobtypes) == 0 {
		return nil
	}
	// 出現順を保ったまま返すための結果配列。
	names := make([]string, 0)
	// 同じ職種名を複数回返さないための既出判定セット。
	seen := map[string]struct{}{}
	for _, items := range filter.Jobtypes {
		for _, item := range items {
			if item == nil {
				continue
			}
			name := strings.TrimSpace(item.Value)
			if name == "" {
				continue
			}
			if _, ok := seen[name]; ok {
				continue
			}
			seen[name] = struct{}{}
			names = append(names, name)
		}
	}
	return names
}
