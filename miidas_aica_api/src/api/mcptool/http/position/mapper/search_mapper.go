package mapper

import (
	dto "aica/api/api/mcptool/http/position/dto"
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	pmodel "aica/api/api/mcptool/usecase/position/model"
	jobSpecificParams "aica/api/api/mcptool/usecase/position/params"
	address "aica/api/api/mcptool/usecase/shared"
	jobfilter "aica/api/domain/jobfilter"
	mposition "aica/api/domain/user/apply/position"
)

func ToGenericSearchParams(req *dto.PositionSearchRequest) *pmodel.GenericPositionSearchParams {
	if req == nil {
		return nil
	}
	return &pmodel.GenericPositionSearchParams{
		CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
			JobtypeNames:    req.JobtypeNames,
			Salary:          req.Salary,
			Locations:       req.Locations,
			DayOffs:         req.DayOffs,
			AverageOvertime: req.AverageOvertime,
		},
		PositionKeyword: derefString(req.PositionKeyword),
	}
}

func derefString(value *string) string {
	if value == nil {
		return ""
	}
	return *value
}

func ToSearchEnvelope(
	allPositionIDs []mposition.ID,
	positions []*pmodel.PositionSummary,
	recommendations []*pmodel.PositionRecommendation,
	searchFilters *jobfilter.JobSearchFilter,
	toolName string,
	jobtypeNamesWithSameSearchFilters map[string][]string,
) dto.SearchResponseEnvelope {
	return dto.SearchResponseEnvelope{
		AllPositionIds:                    allPositionIDs,
		Positions:                         toPositionSummaryResponses(positions),
		Recommendations:                   toPositionRecommendationResponses(recommendations),
		SearchFilters:                     toJobSearchFilterResponse(searchFilters, toolName),
		JobtypeNamesWithSameSearchFilters: jobtypeNamesWithSameSearchFilters,
	}
}

func ToGenericSearchEnvelope(
	allPositionIDs []mposition.ID,
	positions []*pmodel.PositionSummary,
	recommendations []*pmodel.PositionRecommendation,
	params *pmodel.GenericPositionSearchParams,
) dto.SearchResponseEnvelope {
	return dto.SearchResponseEnvelope{
		AllPositionIds:  allPositionIDs,
		Positions:       toPositionSummaryResponses(positions),
		Recommendations: toPositionRecommendationResponses(recommendations),
		SearchFilters:   ToGenericSearchFilterResponse(params),
	}
}

func ToGenericSearchFilterResponse(params *pmodel.GenericPositionSearchParams) *dto.JobSearchFilterResponse {
	if params == nil {
		return nil
	}

	return &dto.JobSearchFilterResponse{
		Jobtypes:        toGenericJobtypeSelectableItemResponses(params.JobtypeNames),
		Locations:       toGenericSearchFilterLocationsResponse(params.Locations),
		Salary:          int(params.Salary),
		PositionKeyword: stringPointerIfNonEmpty(params.PositionKeyword),
	}
}

func ToJobTypeSearchFilterResponse(
	searchFilters *jobfilter.JobSearchFilter,
	toolName string,
) *dto.JobTypeSearchFilterResponse {
	if searchFilters == nil {
		return &dto.JobTypeSearchFilterResponse{}
	}
	return &dto.JobTypeSearchFilterResponse{
		OtherFilters:          toOtherFiltersResponse(otherFiltersByToolName(toolName)),
		SelectedFilterOptions: selectedFilterOptionsByToolName(searchFilters.SelectedOtherFilterOptions, toolName),
	}
}

func ToCurrentJobTypeSearchFilterResponse(
	searchFilters *jobfilter.JobSearchFilter,
	toolName string,
	jobtypeNamesWithSameSearchFilters map[string][]string,
) *dto.CurrentJobTypeSearchFilterResponse {
	if searchFilters == nil {
		return &dto.CurrentJobTypeSearchFilterResponse{}
	}
	return &dto.CurrentJobTypeSearchFilterResponse{
		ToolName:                          toolName,
		SearchFilters:                     toJobSearchFilterResponse(searchFilters, toolName),
		JobtypeNamesWithSameSearchFilters: jobtypeNamesWithSameSearchFilters,
	}
}

func toPositionSummaryResponses(src []*pmodel.PositionSummary) []*dto.PositionSummaryResponse {
	if len(src) == 0 {
		return nil
	}
	out := make([]*dto.PositionSummaryResponse, 0, len(src))
	for _, item := range src {
		if item == nil {
			continue
		}
		out = append(out, &dto.PositionSummaryResponse{
			ID:          item.ID,
			Title:       item.Title,
			MainJobText: item.MainJobText,
			SalaryFrom:  item.SalaryFrom,
			SalaryTo:    item.SalaryTo,
			Image:       item.Image,
		})
	}
	return out
}

func toPositionRecommendationResponses(src []*pmodel.PositionRecommendation) []*dto.PositionRecommendationResponse {
	if len(src) == 0 {
		return nil
	}
	out := make([]*dto.PositionRecommendationResponse, 0, len(src))
	for _, item := range src {
		if item == nil {
			continue
		}
		out = append(out, &dto.PositionRecommendationResponse{
			Theme:       item.Theme,
			Title:       item.Title,
			Description: item.Description,
		})
	}
	return out
}

func toJobSearchFilterResponse(src *jobfilter.JobSearchFilter, toolName string) *dto.JobSearchFilterResponse {
	if src == nil {
		return nil
	}
	return &dto.JobSearchFilterResponse{
		Jobtypes:              toJobtypeSelectableItemResponses(src.Jobtypes),
		Locations:             toJobSearchFilterLocationsResponse(src.Locations),
		Salary:                src.Salary,
		PositionKeyword:       src.PositionKeyword,
		OtherFilters:          groupedOtherFiltersResponse(src.Jobtypes, toolName),
		SelectedFilterOptions: groupedSelectedFilterOptions(src.SelectedOtherFilterOptions),
	}
}

func toJobtypeSelectableItemResponses(src map[string][]*jobfilter.JobtypeSelectableItem) map[string][]*dto.JobSearchFilterJobtypeSelectableItemResponse {
	if len(src) == 0 {
		return nil
	}
	out := make(map[string][]*dto.JobSearchFilterJobtypeSelectableItemResponse, len(src))
	for key, items := range src {
		group := make([]*dto.JobSearchFilterJobtypeSelectableItemResponse, 0, len(items))
		for _, item := range items {
			if item == nil {
				continue
			}
			group = append(group, &dto.JobSearchFilterJobtypeSelectableItemResponse{
				Label:       item.Label,
				Value:       item.Value,
				Description: item.Description,
				Selected:    item.Selected,
			})
		}
		out[key] = group
	}
	return out
}

func toGenericJobtypeSelectableItemResponses(src []string) map[string][]*dto.JobSearchFilterJobtypeSelectableItemResponse {
	if len(src) == 0 {
		return nil
	}
	out := make([]*dto.JobSearchFilterJobtypeSelectableItemResponse, 0, len(src))
	for _, item := range src {
		if item == "" {
			continue
		}
		out = append(out, &dto.JobSearchFilterJobtypeSelectableItemResponse{
			Label:    item,
			Value:    item,
			Selected: true,
		})
	}
	if len(out) == 0 {
		return nil
	}
	return map[string][]*dto.JobSearchFilterJobtypeSelectableItemResponse{
		pcontracts.ToolNameSearchJobPostings: out,
	}
}

func toLocationSelectableItemResponses(src []*jobfilter.JobSearchFilterLocationSelectableItem) []*dto.JobSearchFilterLocationSelectableItemResponse {
	if len(src) == 0 {
		return nil
	}
	out := make([]*dto.JobSearchFilterLocationSelectableItemResponse, 0, len(src))
	for _, item := range src {
		if item == nil {
			continue
		}
		out = append(out, &dto.JobSearchFilterLocationSelectableItemResponse{
			Label:          item.Label,
			PrefectureName: item.PrefectureName,
			CityName:       item.CityName,
			Selected:       item.Selected,
		})
	}
	return out
}

func toJobSearchFilterLocationsResponse(src *jobfilter.JobSearchFilterLocations) *dto.JobSearchFilterLocationsResponse {
	if src == nil {
		return nil
	}
	out := &dto.JobSearchFilterLocationsResponse{
		WorkLocations:      toLocationSelectableItemResponses(src.WorkLocations),
		RemoteWorkPossible: src.RemoteWorkPossible,
	}
	if src.Residence != nil {
		var addressResp *dto.JobSearchFilterAddressResponse
		if src.Residence.Address != nil {
			addressResp = &dto.JobSearchFilterAddressResponse{
				PrefectureName: src.Residence.Address.PrefectureName,
				CityName:       src.Residence.Address.CityName,
			}
		}
		out.Residence = &dto.JobSearchFilterResidenceResponse{
			Address:        addressResp,
			CommutingAreas: toLocationSelectableItemResponses(src.Residence.CommutingAreas),
		}
	}
	return out
}

func toGenericSearchFilterLocationsResponse(src []*address.LocationRequest) *dto.JobSearchFilterLocationsResponse {
	if len(src) == 0 {
		return nil
	}

	out := &dto.JobSearchFilterLocationsResponse{}
	var commutingAreas []*dto.JobSearchFilterLocationSelectableItemResponse
	var workLocations []*dto.JobSearchFilterLocationSelectableItemResponse
	var remoteWorkPossible *bool

	for _, item := range src {
		if item == nil {
			continue
		}

		switch item.LocationType {
		case address.LOCATION_TYPE_RESIDENCE:
			out.Residence = &dto.JobSearchFilterResidenceResponse{
				Address: &dto.JobSearchFilterAddressResponse{
					PrefectureName: item.PrefectureName,
					CityName:       item.CityName,
				},
			}
		case address.LOCATION_TYPE_COMMUTING_AREAS:
			commutingAreas = append(commutingAreas, &dto.JobSearchFilterLocationSelectableItemResponse{
				Label:          item.PrefectureName + item.CityName,
				PrefectureName: item.PrefectureName,
				CityName:       item.CityName,
				Selected:       true,
			})
		case address.LOCATION_TYPE_WORK_LOCATION:
			workLocations = append(workLocations, &dto.JobSearchFilterLocationSelectableItemResponse{
				Label:          item.PrefectureName + item.CityName,
				PrefectureName: item.PrefectureName,
				CityName:       item.CityName,
				Selected:       true,
			})
		case address.LOCATION_TYPE_FULL_REMOTE_WORK:
			v := true
			remoteWorkPossible = &v
		}
	}

	if out.Residence != nil {
		out.Residence.CommutingAreas = commutingAreas
	}
	out.WorkLocations = workLocations
	out.RemoteWorkPossible = remoteWorkPossible

	if out.Residence == nil && len(out.WorkLocations) == 0 && out.RemoteWorkPossible == nil {
		return nil
	}

	return out
}

func otherFiltersByToolName(toolName string) []*jobfilter.JobSearchFilterOtherFilter {
	switch toolName {
	case pcontracts.ToolNameSearchJobPostingsForITEngineer:
		return jobSpecificParams.ITEngineerSearchFilters
	case pcontracts.ToolNameSearchJobPostingsForSalesFinancialSales:
		return jobSpecificParams.FinancialSalesSearchFilters
	default:
		return nil
	}
}

func groupedSelectedFilterOptions(src map[string]map[string][]string) map[string]map[string][]string {
	if len(src) == 0 {
		return nil
	}
	out := make(map[string]map[string][]string, len(src))
	for toolName, selected := range src {
		if toolName == pcontracts.SelectedFilterOptionsCommonKey || len(selected) == 0 {
			continue
		}
		group := make(map[string][]string, len(selected))
		for filterName, values := range selected {
			group[filterName] = append([]string(nil), values...)
		}
		out[toolName] = group
	}
	if len(out) == 0 {
		return nil
	}
	return out
}

func selectedFilterOptionsByToolName(src map[string]map[string][]string, toolName string) map[string][]string {
	if len(src) == 0 || toolName == "" {
		return nil
	}
	selected := src[toolName]
	if len(selected) == 0 {
		return nil
	}
	out := make(map[string][]string, len(selected))
	for filterName, values := range selected {
		out[filterName] = append([]string(nil), values...)
	}
	return out
}

func groupedOtherFiltersResponse(src map[string][]*jobfilter.JobtypeSelectableItem, fallbackToolName string) map[string][]*dto.JobSearchFilterOtherFilterResponse {
	keys := make(map[string]struct{}, len(src)+1)
	for toolName := range src {
		keys[toolName] = struct{}{}
	}
	if fallbackToolName != "" {
		keys[fallbackToolName] = struct{}{}
	}
	if len(keys) == 0 {
		return nil
	}
	out := make(map[string][]*dto.JobSearchFilterOtherFilterResponse, len(keys))
	for toolName := range keys {
		filters := toOtherFiltersResponse(otherFiltersByToolName(toolName))
		if len(filters) == 0 {
			continue
		}
		out[toolName] = filters
	}
	if len(out) == 0 {
		return nil
	}
	return out
}

func toOtherFiltersResponse(src []*jobfilter.JobSearchFilterOtherFilter) []*dto.JobSearchFilterOtherFilterResponse {
	if len(src) == 0 {
		return nil
	}
	out := make([]*dto.JobSearchFilterOtherFilterResponse, 0, len(src))
	for _, item := range src {
		if item == nil {
			continue
		}
		out = append(out, &dto.JobSearchFilterOtherFilterResponse{
			Key:     item.Key,
			Name:    item.Name,
			Type:    string(item.Type),
			Options: toOtherFilterOptionResponses(item.Options),
		})
	}
	return out
}

func toOtherFilterOptionResponses(src []*jobfilter.JobSearchFilterOtherFilterOption) []*dto.JobSearchFilterOtherFilterOptionResponse {
	if len(src) == 0 {
		return nil
	}
	out := make([]*dto.JobSearchFilterOtherFilterOptionResponse, 0, len(src))
	for _, item := range src {
		if item == nil {
			continue
		}
		out = append(out, &dto.JobSearchFilterOtherFilterOptionResponse{
			Label: item.Label,
			Value: item.Value,
		})
	}
	return out
}

func stringPointerIfNonEmpty(value string) *string {
	if value == "" {
		return nil
	}
	return &value
}
