package params

import (
	"aica/api/api/mcptool/service"
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	pextensions "aica/api/api/mcptool/usecase/position/extensions"
	jobfilter "aica/api/domain/jobfilter"
	"slices"
)

const (
	filterProgrammingLanguages   = "言語（all）"
	filterProjectScales          = "プロジェクト規模（IT）"
	filterApplicationFrameworks  = "アプリケーションフレームワーク（IT）"
	filterCloudServices          = "クラウドサービス（IT）"
	filterPhases                 = "担当フェーズ（IT）"
	filterPositions              = "ポジション（IT）"
	filterSystemScales           = "システム規模（IT）"
	filterDevelopmentProjectType = "開発案件種別（IT／業務系）"
)

type ITEngineerParams struct {
	RemoteWorkPossible      *bool
	PositionKeyword         string
	ProgrammingLanguages    []string
	ProjectScales           []string
	ApplicationFrameworks   []string
	CloudServices           []string
	Phases                  []string
	Positions               []string
	SystemScales            []string
	DevelopmentProjectTypes []string
}

func (p *ITEngineerParams) BuildExtensions(resolver pcontracts.JobSpecificSearchResolver) ([]pcontracts.SearchExtension, error) {
	remoteWork := false
	if p.RemoteWorkPossible != nil {
		remoteWork = *p.RemoteWorkPossible
	}
	extensions := []pcontracts.SearchExtension{
		pextensions.NewRemoteWorkExtension(remoteWork),
		pextensions.NewPositionKeywordExtension(p.PositionKeyword),
	}

	skillGroups := []struct {
		label string
		names []string
	}{
		{label: filterProgrammingLanguages, names: p.ProgrammingLanguages},
		{label: filterProjectScales, names: p.ProjectScales},
		{label: filterApplicationFrameworks, names: p.ApplicationFrameworks},
		{label: filterCloudServices, names: p.CloudServices},
		{label: filterPhases, names: p.Phases},
		{label: filterPositions, names: p.Positions},
		{label: filterSystemScales, names: p.SystemScales},
		{label: filterDevelopmentProjectType, names: p.DevelopmentProjectTypes},
	}
	for _, group := range skillGroups {
		if len(group.names) == 0 {
			continue
		}
		skills, err := resolver.ResolveSkills(group.names)
		if err != nil {
			return nil, err
		}
		extensions = append(extensions, pextensions.NewSkillExtension(findFilterByName(ITEngineerSearchFilters, group.label), skills))
	}

	return extensions, nil
}

func (p *ITEngineerParams) Keyword() string {
	if p == nil {
		return ""
	}
	return p.PositionKeyword
}

func (p *ITEngineerParams) SelectedOptionNamesByFilter() map[string]map[string]struct{} {
	result := make(map[string]map[string]struct{})
	add := func(filterName string, optionNames []string) {
		if len(optionNames) == 0 {
			return
		}
		seen := result[filterName]
		if seen == nil {
			seen = make(map[string]struct{})
			result[filterName] = seen
		}
		for _, name := range optionNames {
			if name == "" {
				continue
			}
			seen[name] = struct{}{}
		}
	}

	add(filterProgrammingLanguages, p.ProgrammingLanguages)
	add(filterProjectScales, p.ProjectScales)
	add(filterApplicationFrameworks, p.ApplicationFrameworks)
	add(filterCloudServices, p.CloudServices)
	add(filterPhases, p.Phases)
	add(filterPositions, p.Positions)
	add(filterSystemScales, p.SystemScales)
	add(filterDevelopmentProjectType, p.DevelopmentProjectTypes)

	return result
}

func (p *ITEngineerParams) RemotePositionOptionState() *pcontracts.RemotePositionOptionState {
	currentChoice := false
	if p.RemoteWorkPossible != nil {
		currentChoice = *p.RemoteWorkPossible
	}
	return &pcontracts.RemotePositionOptionState{
		HasOption:     true,
		CurrentChoice: currentChoice,
	}
}

var ITEngineerSearchFilters []*jobfilter.JobSearchFilterOtherFilter

func initITEngineerSearchFilters(cacheService *service.MiidasCacheService) {
	filterDefinitions := []struct {
		key   string
		label string
	}{
		{key: "ProgrammingLanguages", label: filterProgrammingLanguages},
		{key: "ProjectScales", label: filterProjectScales},
		{key: "ApplicationFrameworks", label: filterApplicationFrameworks},
		{key: "CloudServices", label: filterCloudServices},
		{key: "Phases", label: filterPhases},
		{key: "Positions", label: filterPositions},
		{key: "SystemScales", label: filterSystemScales},
		{key: "DevelopmentProjectTypes", label: filterDevelopmentProjectType},
	}

	ITEngineerSearchFilters = make([]*jobfilter.JobSearchFilterOtherFilter, 0, len(filterDefinitions))
	for _, def := range filterDefinitions {
		filter := buildSkillFilter(cacheService, def.label)
		if filter == nil {
			continue
		}
		if len(filter.Options) == 0 {
			continue
		}
		filter.Key = def.key
		ITEngineerSearchFilters = append(ITEngineerSearchFilters, filter)
	}
}

func NewITEngineerParamsFromSelectedOptions(selected map[string][]string, remoteWorkPossible *bool) *ITEngineerParams {
	return &ITEngineerParams{
		RemoteWorkPossible:      remoteWorkPossible,
		ProgrammingLanguages:    slices.Clone(selected[filterProgrammingLanguages]),
		ProjectScales:           slices.Clone(selected[filterProjectScales]),
		ApplicationFrameworks:   slices.Clone(selected[filterApplicationFrameworks]),
		CloudServices:           slices.Clone(selected[filterCloudServices]),
		Phases:                  slices.Clone(selected[filterPhases]),
		Positions:               slices.Clone(selected[filterPositions]),
		SystemScales:            slices.Clone(selected[filterSystemScales]),
		DevelopmentProjectTypes: slices.Clone(selected[filterDevelopmentProjectType]),
	}
}
