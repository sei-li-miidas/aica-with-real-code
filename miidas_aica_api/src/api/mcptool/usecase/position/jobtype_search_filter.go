package position

import (
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	pinterfaces "aica/api/api/mcptool/usecase/position/interfaces"
	pmodel "aica/api/api/mcptool/usecase/position/model"
	jobfilter "aica/api/domain/jobfilter"
	merr "aica/api/sdk/error"
	"aica/api/sdk/logger"
	"errors"
	"strings"
)

type JobTypeSearchFilterUseCase struct {
	logger                 logger.LevelLogger
	jobSearchFilterService pinterfaces.JobSearchFilterReader
	resolver               pcontracts.JobSpecificSearchResolver
}

// NewJobTypeSearchFilterUseCase は職種特化検索フィルタ取得ユースケースを生成する。
// 保存済みフィルタ参照と職種名検証に必要な依存を受け取り、実行時に利用できる形で保持する。
func NewJobTypeSearchFilterUseCase(
	l logger.LevelLogger,
	jobSearchFilterService pinterfaces.JobSearchFilterReader,
	resolver pcontracts.JobSpecificSearchResolver,
) *JobTypeSearchFilterUseCase {
	return &JobTypeSearchFilterUseCase{
		logger:                 l,
		jobSearchFilterService: jobSearchFilterService,
		resolver:               resolver,
	}
}

// Execute は指定職種または現在の選択状態に対応する職種特化検索フィルタを返す。
// `/positions/search_filter/jobtype` から呼ばれた場合は req.JobtypeName に入った職種名を検証し、その職種向けの検索フィルタ取得に使う。
// `/positions/search_filter/current` から呼ばれた場合は JobtypeName が空のため、保存済みフィルタから現在選択されている ToolName を推定して返却する。
func (uc *JobTypeSearchFilterUseCase) Execute(sessionID string, req *pmodel.JobTypeSearchFilterQuery) (*pmodel.JobTypeSearchFilter, error) {
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

	// `search_filter/jobtype` では職種名が入るため、その場合だけ resolver で存在確認を行う。
	current := strings.TrimSpace(req.JobtypeName)
	if current != "" {
		if _, err := uc.resolver.ResolveJobTypeSmallIDs([]string{current}); err != nil {
			return nil, err
		}
	}

	filter, err := uc.jobSearchFilterService.GetBySessionID(sessionID)
	if err != nil {
		return nil, err
	}

	// `search_filter/current` では JobtypeName が空のため、保存済みフィルタから現在選択中の ToolName を返却用に補う。
	toolName := ""
	if current == "" && filter != nil {
		toolName = selectedToolNameFromFilter(filter)
		if toolName == "" {
			return nil, nil
		}
	}

	return &pmodel.JobTypeSearchFilter{
		SearchFilter: filter,
		ToolName:     toolName,
	}, nil
}

// selectedToolNameFromFilter は保存済みフィルタから、現在選択されている職種グループの ToolName を推定する。
// Jobtypes を走査し、Selected=true かつ有効な値を持つ職種が最初に見つかったグループ名を返す。
func selectedToolNameFromFilter(filter *jobfilter.JobSearchFilter) string {
	if filter == nil {
		return ""
	}
	for toolName, items := range filter.Jobtypes {
		if strings.TrimSpace(toolName) == "" {
			continue
		}
		for _, item := range items {
			if item == nil || !item.Selected {
				continue
			}
			if strings.TrimSpace(item.Value) == "" {
				continue
			}
			return toolName
		}
	}
	return ""
}
