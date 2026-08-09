package position

import (
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	pinterfaces "aica/api/api/mcptool/usecase/position/interfaces"
	pmodel "aica/api/api/mcptool/usecase/position/model"
	merr "aica/api/sdk/error"
	"aica/api/sdk/logger"
	"errors"
	"strings"
)

type JobTypesSelectedUseCase struct {
	logger                 logger.LevelLogger
	jobSearchFilterService pinterfaces.JobSearchFilterJobtypesWriter
	resolver               pcontracts.JobSpecificSearchResolver
	toolResolver           pinterfaces.JobTypeSearchToolResolver
}

// NewJobTypesSelectedUseCase は職種選択状態を更新するユースケースを生成する。
// 検索条件保存サービス、職種名検証用リゾルバ、検索ツール分類用リゾルバを受け取り、実行時に使える形で保持する。
func NewJobTypesSelectedUseCase(
	l logger.LevelLogger,
	jobSearchFilterService pinterfaces.JobSearchFilterJobtypesWriter,
	resolver pcontracts.JobSpecificSearchResolver,
	toolResolver pinterfaces.JobTypeSearchToolResolver,
) *JobTypesSelectedUseCase {
	return &JobTypesSelectedUseCase{
		logger:                 l,
		jobSearchFilterService: jobSearchFilterService,
		resolver:               resolver,
		toolResolver:           toolResolver,
	}
}

// Execute はセッションに紐づく選択職種を検証し、検索グループ単位に整理して保存する。
// `/positions/jobtypes/decided` から呼ばれた場合は、指定された職種名を検証して対応グループの選択状態を更新する。
// `/positions/jobtypes/clear` から空の JobtypeNames で呼ばれた場合は、検証をスキップし、既存グループの Selected をすべて false にする形で選択状態をクリアする。
func (uc *JobTypesSelectedUseCase) Execute(sessionID string, req *pmodel.JobTypesSelection) (*pmodel.JobTypesSelectionResult, error) {
	if req == nil {
		return nil, merr.ErrInvalidRequest.WithCause(errors.New("request is required"))
	}
	if sessionID == "" {
		return nil, merr.ErrInvalidRequest.WithCause(errors.New("X-Session-Id is required"))
	}
	if uc.jobSearchFilterService == nil {
		return nil, merr.ErrInternalServer.WithCause(errors.New("job search filter service is not configured"))
	}
	if uc.resolver == nil {
		return nil, merr.ErrInternalServer.WithCause(errors.New("job specific resolver is not configured"))
	}
	// 職種名の存在確認に使う一覧で、空要素と重複を除いた値だけを resolver に渡す。
	namesToValidate := uniqueRequestedJobtypeNames(req.JobtypeNames)
	// clear エンドポイントでは JobtypeNames が空のため、この検証は decided エンドポイント経由のときだけ実行される。
	if len(namesToValidate) > 0 {
		if _, err := uc.resolver.ResolveJobTypeSmallIDs(namesToValidate); err != nil {
			return nil, err
		}
	}

	// decided では指定職種をグループ別に保存し、clear では空入力により各グループの選択状態を解除する。
	selectedGroupKey, groupedJobtypeNames := resolveRequestedJobtypesByGroup(namesToValidate, uc.toolResolver)
	if err := uc.jobSearchFilterService.MergeJobTypes(sessionID, selectedGroupKey, groupedJobtypeNames); err != nil {
		return nil, err
	}
	return &pmodel.JobTypesSelectionResult{ToolName: selectedGroupKey}, nil
}

// resolveRequestedJobtypesByGroup は正規化済みかつ一意化済みの職種名一覧を検索ツールのグループ単位に整理する。
// 先頭職種から代表となるグループを決めた後、全職種を対応する ToolName ごとに振り分ける。
func resolveRequestedJobtypesByGroup(names []string, resolver pinterfaces.JobTypeSearchToolResolver) (string, map[string][]string) {
	if len(names) == 0 {
		return pcontracts.ToolNameSearchJobPostings, nil
	}

	selectedGroupKey := resolveJobtypeGroupKey(names[0], resolver)
	grouped := make(map[string][]string)
	for _, name := range names {
		groupKey := resolveJobtypeGroupKey(name, resolver)
		grouped[groupKey] = append(grouped[groupKey], name)
	}
	return selectedGroupKey, grouped
}

// resolveJobtypeGroupKey は 1 件の職種名がどの検索グループに属するかを決定する。
// 専用検索ツールとして扱う職種だけは専用 ToolName を返し、それ以外や未解決時は汎用検索グループへ寄せる。
func resolveJobtypeGroupKey(jobtypeName string, resolver pinterfaces.JobTypeSearchToolResolver) string {
	if resolver == nil {
		return pcontracts.ToolNameSearchJobPostings
	}
	resolved := strings.TrimSpace(resolver.ToolNameByJobtypeName(strings.TrimSpace(jobtypeName)))
	if resolved == pcontracts.ToolNameSearchJobPostingsForITEngineer || resolved == pcontracts.ToolNameSearchJobPostingsForSalesFinancialSales {
		return resolved
	}
	return pcontracts.ToolNameSearchJobPostings
}

// uniqueRequestedJobtypeNames は入力された職種名一覧から空文字と重複を除いた正規化済み一覧を作る。
// 前後空白を除去した値だけを保持し、出現順を保ったまま一意な職種名の配列を返す。
func uniqueRequestedJobtypeNames(jobtypeNames []string) []string {
	seen := make(map[string]struct{}, len(jobtypeNames))
	results := make([]string, 0, len(jobtypeNames))
	for _, name := range jobtypeNames {
		normalized := strings.TrimSpace(name)
		if normalized == "" {
			continue
		}
		if _, ok := seen[normalized]; ok {
			continue
		}
		seen[normalized] = struct{}{}
		results = append(results, normalized)
	}
	return results
}
