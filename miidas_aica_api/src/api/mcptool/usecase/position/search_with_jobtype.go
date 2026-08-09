package position

import (
	pbuilder "aica/api/api/mcptool/usecase/position/builder"
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	pinterfaces "aica/api/api/mcptool/usecase/position/interfaces"
	pmodel "aica/api/api/mcptool/usecase/position/model"
	jobSpecificParams "aica/api/api/mcptool/usecase/position/params"
	psupport "aica/api/api/mcptool/usecase/position/support"
	pvalidation "aica/api/api/mcptool/usecase/position/validation"
	address "aica/api/api/mcptool/usecase/shared"
	jobfilter "aica/api/domain/jobfilter"
	"aica/api/domain/position"
	"aica/api/domain/public/master"
	"aica/api/domain/search"
	mposition "aica/api/domain/user/apply/position"
	"aica/api/domain/vectorizer"
	merr "aica/api/sdk/error"
	"aica/api/sdk/logger"
	"fmt"
	"miidas/m2/user/marketvalue/grpc/iface"
	"strings"
)

type SearchWithJobTypeUseCase struct {
	logger                   logger.LevelLogger
	mvGateway                willPositionGetter
	vectorizerRepository     vectorizer.VectorizerRepository
	positionVectorRepository search.SemanticSearchRepository[*position.PositionSearchResult]
	positionRepository       pinterfaces.PositionGetter
	resolver                 pcontracts.JobSpecificSearchResolver
	jobSearchFilterReader    pinterfaces.JobSearchFilterReader
	jobSearchFilterPersister pinterfaces.JobSearchFilterPersister
}

type executeByInputContext struct {
	// 検索条件の本体。MV2 の will 構築と検索実行に使う。
	jobTypeSmallIDs []int32
	cityIDs         []int32
	dayOffs         []int32
	averageOvertime int32
	positionKeyword string

	// 拡張条件。検索条件の付与と、選択済みフィルタの再構築に使う。
	extensions []pcontracts.SearchExtension

	// 保存用 job_search_filter の Locations 再構築に使う。
	residenceLocation   *address.LocationRequest
	commutingLocations  []*address.LocationRequest
	workLocationResults []*address.LocationRequest
}

func NewSearchWithJobTypeUseCase(
	logger logger.LevelLogger,
	mvGateway willPositionGetter,
	vectorizerRepository vectorizer.VectorizerRepository,
	positionVectorRepository search.SemanticSearchRepository[*position.PositionSearchResult],
	positionRepository pinterfaces.PositionGetter,
	resolver pcontracts.JobSpecificSearchResolver,
	jobSearchFilterReader pinterfaces.JobSearchFilterReader,
	jobSearchFilterPersister pinterfaces.JobSearchFilterPersister,
) *SearchWithJobTypeUseCase {
	return &SearchWithJobTypeUseCase{
		logger:                   logger,
		mvGateway:                mvGateway,
		vectorizerRepository:     vectorizerRepository,
		positionVectorRepository: positionVectorRepository,
		positionRepository:       positionRepository,
		resolver:                 resolver,
		jobSearchFilterReader:    jobSearchFilterReader,
		jobSearchFilterPersister: jobSearchFilterPersister,
	}
}

func (uc *SearchWithJobTypeUseCase) Execute(
	sessionID string,
	input *pcontracts.JobSpecificSearchInput,
) ([]mposition.ID, []*pmodel.PositionSummary, *jobfilter.JobSearchFilter, error) {
	allPositionIDs, positions, ctx, err := uc.executeByInput(input, pcontracts.PositionRecommendationTheme(""))
	if err != nil {
		return nil, nil, nil, err
	}

	searchFilters := buildJobSearchFilterFromInput(input, ctx)

	if uc.jobSearchFilterPersister != nil {
		persisted, err := uc.jobSearchFilterPersister.PersistFromSearchInput(sessionID, input, ctx.commutingLocations, searchFilters)
		if err != nil {
			uc.logger.Error("failed to persist job_search_filter", "session_id", sessionID, "error", err)
		} else if persisted != nil {
			searchFilters = persisted
		}
	}

	return allPositionIDs, positions, searchFilters, nil
}

func (uc *SearchWithJobTypeUseCase) ExecuteWithTheme(
	input *pcontracts.JobSpecificSearchInput,
	theme pcontracts.PositionRecommendationTheme,
) ([]mposition.ID, []*pmodel.PositionSummary, error) {
	allPositionIDs, positions, _, err := uc.executeByInput(input, theme)
	return allPositionIDs, positions, err
}

func (uc *SearchWithJobTypeUseCase) ExecuteWithThemeBySession(
	sessionID string,
	jobTypeLargeID master.JobTypeLargeID,
	theme pcontracts.PositionRecommendationTheme,
) ([]mposition.ID, []*pmodel.PositionSummary, error) {
	if sessionID == "" {
		return nil, nil, merr.ErrInvalidRequest.WithCause(fmt.Errorf("X-Session-Id is required"))
	}
	if uc.jobSearchFilterReader == nil {
		return nil, nil, merr.ErrInternalServer.WithCause(fmt.Errorf("job search filter service is not configured"))
	}
	if uc.resolver == nil {
		return nil, nil, merr.ErrInternalServer.WithCause(fmt.Errorf("job specific resolver is not configured"))
	}

	filter, err := uc.jobSearchFilterReader.GetBySessionID(sessionID)
	if err != nil {
		return nil, nil, err
	}
	input, err := uc.buildInputFromStoredFilter(filter, jobTypeLargeID)
	if err != nil {
		return nil, nil, err
	}
	return uc.ExecuteWithTheme(input, theme)
}

func (uc *SearchWithJobTypeUseCase) buildInputFromStoredFilter(
	filter *jobfilter.JobSearchFilter,
	jobTypeLargeID master.JobTypeLargeID,
) (*pcontracts.JobSpecificSearchInput, error) {
	if filter == nil {
		return nil, merr.ErrInvalidRequest.WithCause(fmt.Errorf("job_search_filter is not found"))
	}

	jobTypeNames := selectedJobTypeNames(filter.Jobtypes, selectedFilterOptionsKeyByJobTypeLargeID(jobTypeLargeID))
	if len(jobTypeNames) == 0 {
		return nil, merr.ErrInvalidRequest.WithCause(fmt.Errorf("selected job type is required in job_search_filter"))
	}
	if filter.Salary <= 0 {
		return nil, merr.ErrInvalidRequest.WithCause(fmt.Errorf("salary is required in job_search_filter"))
	}

	locations, err := uc.buildLocationsFromStoredFilter(filter.Locations)
	if err != nil {
		return nil, err
	}

	selectedOptions := map[string][]string{}
	if filter.SelectedOtherFilterOptions != nil {
		if key := selectedFilterOptionsKeyByJobTypeLargeID(jobTypeLargeID); key != "" {
			selectedOptions = filter.SelectedOtherFilterOptions[key]
		}
	}
	var remoteWorkPossible *bool
	if filter.Locations != nil {
		remoteWorkPossible = filter.Locations.RemoteWorkPossible
	}
	custom, err := buildCustomParamsFromSelected(jobTypeLargeID, selectedOptions, remoteWorkPossible)
	if err != nil {
		return nil, err
	}

	applyPositionKeywordToCustom(custom, filter.PositionKeyword)

	return &pcontracts.JobSpecificSearchInput{
		JobTypeLargeID: jobTypeLargeID,
		JobTypeNames:   jobTypeNames,
		Salary:         int32(filter.Salary),
		Locations:      locations,
		Custom:         custom,
	}, nil
}

func (uc *SearchWithJobTypeUseCase) buildLocationsFromStoredFilter(locations *jobfilter.JobSearchFilterLocations) ([]*address.LocationRequest, error) {
	if uc.resolver == nil || locations == nil {
		return nil, nil
	}

	results := make([]*address.LocationRequest, 0)

	if locations.Residence != nil {
		if locations.Residence.Address != nil &&
			strings.TrimSpace(locations.Residence.Address.PrefectureName) != "" &&
			strings.TrimSpace(locations.Residence.Address.CityName) != "" {
			results = append(results, &address.LocationRequest{
				LocationType:   address.LOCATION_TYPE_RESIDENCE,
				PrefectureName: locations.Residence.Address.PrefectureName,
				CityName:       locations.Residence.Address.CityName,
			})
		}
		for _, area := range locations.Residence.CommutingAreas {
			if area == nil || !area.Selected {
				continue
			}
			if commutingArea, err := uc.resolveStoredLocationWithType(area, address.LOCATION_TYPE_COMMUTING_AREAS); err != nil {
				return nil, err
			} else if commutingArea != nil {
				results = append(results, commutingArea)
			}
		}
	}

	for _, work := range locations.WorkLocations {
		if work == nil || !work.Selected {
			continue
		}
		if workLocation, err := uc.resolveStoredLocationWithType(work, address.LOCATION_TYPE_WORK_LOCATION); err != nil {
			return nil, err
		} else if workLocation != nil {
			results = append(results, workLocation)
		}
	}

	return results, nil
}

func (uc *SearchWithJobTypeUseCase) resolveLocationWithType(name string, locationType address.LocationType) (*address.LocationRequest, error) {
	if name == "" {
		return nil, nil
	}
	location, err := uc.resolver.ResolveLocationByName(name)
	if err != nil {
		return nil, err
	}
	if location == nil {
		return nil, nil
	}
	location.LocationType = locationType
	return location, nil
}

func (uc *SearchWithJobTypeUseCase) resolveStoredLocationWithType(loc *jobfilter.JobSearchFilterLocationSelectableItem, locationType address.LocationType) (*address.LocationRequest, error) {
	if loc == nil {
		return nil, nil
	}
	if strings.TrimSpace(loc.PrefectureName) != "" && strings.TrimSpace(loc.CityName) != "" {
		return &address.LocationRequest{
			LocationType:   locationType,
			PrefectureName: loc.PrefectureName,
			CityName:       loc.CityName,
		}, nil
	}
	return uc.resolveLocationWithType(strings.TrimSpace(loc.Label), locationType)
}

func buildCustomParamsFromSelected(
	jobTypeLargeID master.JobTypeLargeID,
	selected map[string][]string,
	remoteWorkPossible *bool,
) (pcontracts.JobSpecificParams, error) {
	switch jobTypeLargeID {
	case master.JobTypeLargeIDITSpecialist:
		return jobSpecificParams.NewITEngineerParamsFromSelectedOptions(selected, remoteWorkPossible), nil
	case master.JobTypeLargeIDFinancialSpecialist:
		return jobSpecificParams.NewFinancialSalesParamsFromSelectedOptions(selected), nil
	default:
		return nil, merr.ErrInvalidRequest.WithCause(fmt.Errorf("unsupported job type large id: %d", jobTypeLargeID))
	}
}

func selectedJobTypeNames(jobtypes map[string][]*jobfilter.JobtypeSelectableItem, groupKey string) []string {
	items := jobtypes[groupKey]
	seen := map[string]struct{}{}
	selected := make([]string, 0, len(items))
	fallback := make([]string, 0, len(items))
	for _, item := range items {
		if item == nil {
			continue
		}
		value := strings.TrimSpace(item.Value)
		if value == "" {
			continue
		}
		if _, ok := seen[value]; ok {
			continue
		}
		seen[value] = struct{}{}
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

func collectOtherFiltersFromExtensions(extensions []pcontracts.SearchExtension) map[string][]string {
	if len(extensions) == 0 {
		return nil
	}
	otherFilters := map[string][]string{}
	for _, ext := range extensions {
		if ext == nil {
			continue
		}
		filterName, selectedOptions := ext.BuildSelectedOtherFilterOptions()
		if selectedOptions == nil {
			continue
		}
		normalizedFilterName := strings.TrimSpace(filterName)
		if normalizedFilterName == "" {
			continue
		}
		otherFilters[normalizedFilterName] = selectedOptions
	}
	return otherFilters
}

func buildJobSearchFilterFromInput(input *pcontracts.JobSpecificSearchInput, ctx *executeByInputContext) *jobfilter.JobSearchFilter {
	if input == nil {
		return nil
	}

	selectedFilterOptionsKey := selectedFilterOptionsKeyFromInput(input)
	requestedJobTypes := psupport.RequestedJobTypeNames(input)

	jobtypes := make([]*jobfilter.JobtypeSelectableItem, 0, len(requestedJobTypes))
	for _, jobTypeName := range requestedJobTypes {
		jobtypes = append(jobtypes, &jobfilter.JobtypeSelectableItem{
			JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{
				JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{
					Label: jobTypeName,
					Value: jobTypeName,
				},
				Selected: true,
			},
		})
	}
	positionKeyword := psupport.ExtractPositionKeyword(input)

	var residence *jobfilter.JobSearchFilterResidence
	var workLocations []*jobfilter.JobSearchFilterLocationSelectableItem
	var otherFilters map[string][]string
	if ctx != nil {
		if ctx.residenceLocation != nil {
			residence = &jobfilter.JobSearchFilterResidence{
				Address: &jobfilter.JobSearchFilterAddress{
					PrefectureName: ctx.residenceLocation.PrefectureName,
					CityName:       ctx.residenceLocation.CityName,
				},
				CommutingAreas: toSelectableItemsFromLocations(ctx.commutingLocations),
			}
		}

		workLocations = toSelectableItemsFromLocations(ctx.workLocationResults)

		otherFilters = collectOtherFiltersFromExtensions(ctx.extensions)
	}

	selectedOtherFilterOptions := map[string]map[string][]string{}
	if selectedFilterOptionsKey != "" && len(otherFilters) > 0 {
		selectedOtherFilterOptions[selectedFilterOptionsKey] = otherFilters
	}
	if positionKeyword != "" {
		selectedOtherFilterOptions[pcontracts.SelectedFilterOptionsCommonKey] = map[string][]string{
			"PositionKeyword": {positionKeyword},
		}
	}
	return &jobfilter.JobSearchFilter{
		Jobtypes: map[string][]*jobfilter.JobtypeSelectableItem{
			selectedFilterOptionsKey: jobtypes,
		},
		Locations: &jobfilter.JobSearchFilterLocations{
			Residence:     residence,
			WorkLocations: workLocations,
		},
		Salary:                     int(input.Salary),
		PositionKeyword:            psupport.StringPtrIfNonEmpty(positionKeyword),
		SelectedOtherFilterOptions: selectedOtherFilterOptions,
	}
}

func selectedFilterOptionsKeyByJobTypeLargeID(jobTypeLargeID master.JobTypeLargeID) string {
	return pcontracts.ToolNameByJobTypeLargeID(jobTypeLargeID)
}

func selectedFilterOptionsKeyFromInput(input *pcontracts.JobSpecificSearchInput) string {
	if input == nil {
		return ""
	}
	if key := strings.TrimSpace(input.SelectedFilterOptionsKey); key != "" {
		return key
	}
	return pcontracts.ToolNameByJobTypeLargeID(input.JobTypeLargeID)
}

func applyPositionKeywordToCustom(custom pcontracts.JobSpecificParams, keyword *string) {
	if custom == nil || keyword == nil || strings.TrimSpace(*keyword) == "" {
		return
	}
	switch params := custom.(type) {
	case *jobSpecificParams.ITEngineerParams:
		params.PositionKeyword = *keyword
	case *jobSpecificParams.FinancialSalesParams:
		params.PositionKeyword = *keyword
	}
}

func toSelectableItemsFromLocations(locations []*address.LocationRequest) []*jobfilter.JobSearchFilterLocationSelectableItem {
	if len(locations) == 0 {
		return nil
	}
	items := make([]*jobfilter.JobSearchFilterLocationSelectableItem, 0, len(locations))
	for _, loc := range locations {
		if loc == nil {
			continue
		}
		label := strings.TrimSpace(loc.PrefectureName + loc.CityName)
		if label == "" {
			continue
		}
		items = append(items, &jobfilter.JobSearchFilterLocationSelectableItem{
			Label:          label,
			PrefectureName: loc.PrefectureName,
			CityName:       loc.CityName,
			Selected:       true,
		})
	}
	return items
}

func (uc *SearchWithJobTypeUseCase) executeByInput(
	input *pcontracts.JobSpecificSearchInput,
	theme pcontracts.PositionRecommendationTheme,
) ([]mposition.ID, []*pmodel.PositionSummary, *executeByInputContext, error) {
	ctx, err := uc.prepareExecuteByInputContext(input)
	if err != nil {
		return nil, nil, nil, err
	}

	allPositionIDs, positions, err := uc.executeSearch(
		&pcontracts.PositionSearchWill{
			JobTypeLargeID:  int32(input.JobTypeLargeID),
			Salary:          input.Salary,
			CityIDs:         ctx.cityIDs,
			JobTypeSmallIDs: ctx.jobTypeSmallIDs,
			DayOffs:         ctx.dayOffs,
			AverageOvertime: ctx.averageOvertime,
		},
		ctx.positionKeyword,
		theme,
		ctx.extensions,
	)
	if err != nil {
		return nil, nil, nil, err
	}
	return allPositionIDs, positions, ctx, nil
}

func (uc *SearchWithJobTypeUseCase) prepareExecuteByInputContext(input *pcontracts.JobSpecificSearchInput) (*executeByInputContext, error) {
	if err := validateJobSpecificSearchInput(input); err != nil {
		return nil, err
	}
	if uc.resolver == nil {
		return nil, merr.ErrInternalServer.WithCause(fmt.Errorf("job specific resolver is not configured"))
	}

	extensions, err := input.Custom.BuildExtensions(uc.resolver)
	if err != nil {
		return nil, err
	}

	remoteWorkPossible := extractRemoteWorkPossible(extensions)
	if err := pvalidation.ValidateLocationRequests(input.Locations, uc.resolver.ExistsPrefectureCity, pvalidation.LocationValidationOptions{
		AllowEmptyIfRemotePossible: true,
		RemoteWork:                 remoteWorkPossible,
	}); err != nil {
		err = merr.ErrInvalidRequest.WithCause(err)
		return nil, err
	}

	jobTypeSmallIDs, err := uc.resolver.ResolveJobTypeSmallIDs(psupport.RequestedJobTypeNames(input))
	if err != nil {
		return nil, err
	}
	if len(jobTypeSmallIDs) == 0 {
		return nil, merr.ErrInvalidRequest.WithCause(
			fmt.Errorf("職種（JobtypeNames）が見つかりませんでした。正しい職種名を指定してください。"),
		)
	}

	cityIDs, residenceLocation, commutingAreaResponses, workLocationResponses, err := uc.resolver.ResolveLocations(input.Locations, remoteWorkPossible)
	if err != nil {
		return nil, err
	}

	dayOffs, err := uc.resolver.ResolveDayOffs(input.DayOffs)
	if err != nil {
		return nil, err
	}

	averageOvertime, err := uc.resolver.ResolveAverageOvertime(input.AverageOvertime)
	if err != nil {
		return nil, err
	}

	return &executeByInputContext{
		extensions:          extensions,
		jobTypeSmallIDs:     jobTypeSmallIDs,
		cityIDs:             cityIDs,
		commutingLocations:  commutingAreaResponses,
		dayOffs:             dayOffs,
		averageOvertime:     averageOvertime,
		residenceLocation:   residenceLocation,
		workLocationResults: workLocationResponses,
		positionKeyword:     extractKeyword(extensions),
	}, nil
}

func (uc *SearchWithJobTypeUseCase) executeSearch(will *pcontracts.PositionSearchWill, semanticKeyword string, theme pcontracts.PositionRecommendationTheme, extensions []pcontracts.SearchExtension) ([]mposition.ID, []*pmodel.PositionSummary, error) {
	uc.logger.Info("職種指定ポジション検索条件", "will", will)

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

	// 職種大分類IDを設定
	positionWill.Job.Value.Larges = []int32{will.JobTypeLargeID}
	positionWill.Job.Importance = 3

	for _, ext := range extensions {
		ext.ApplyMV2(companyWill, businessWill, positionWill)
	}

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

func validateJobSpecificSearchInput(input *pcontracts.JobSpecificSearchInput) error {
	if input == nil {
		return merr.ErrInvalidRequest.WithCause(fmt.Errorf("request is required"))
	}

	if input.Salary <= 0 {
		return merr.ErrInvalidRequest.WithCause(
			fmt.Errorf("希望年収（Salary）は必須です。0より大きい値を指定してください。"),
		)
	}
	if len(psupport.RequestedJobTypeNames(input)) == 0 {
		return merr.ErrInvalidRequest.WithCause(
			fmt.Errorf("職種（JobtypeNames）は必須です。職種名を指定してください。"),
		)
	}
	if input.Custom == nil {
		return merr.ErrInvalidRequest.WithCause(
			fmt.Errorf("custom search parameters are required"),
		)
	}
	return nil
}

func extractRemoteWorkPossible(extensions []pcontracts.SearchExtension) bool {
	for _, ext := range extensions {
		if carrier, ok := ext.(pcontracts.RemoteWorkCarrier); ok {
			return carrier.RemoteWorkPossible()
		}
	}
	return false
}

func extractKeyword(extensions []pcontracts.SearchExtension) string {
	for _, ext := range extensions {
		if carrier, ok := ext.(pcontracts.KeywordCarrier); ok {
			keyword := carrier.Keyword()
			if keyword != "" {
				return keyword
			}
		}
	}
	return ""
}
