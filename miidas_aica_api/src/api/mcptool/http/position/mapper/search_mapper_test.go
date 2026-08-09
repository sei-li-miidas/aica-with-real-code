package mapper

import (
	dto "aica/api/api/mcptool/http/position/dto"
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	pmodel "aica/api/api/mcptool/usecase/position/model"
	jobSpecificParams "aica/api/api/mcptool/usecase/position/params"
	address "aica/api/api/mcptool/usecase/shared"
	jobfilter "aica/api/domain/jobfilter"
	mposition "aica/api/domain/user/apply/position"
	"testing"
)

func TestToGenericSearchParams(t *testing.T) {
	keyword := "go"
	req := &dto.PositionSearchRequest{PositionSearchCommonRequest: dto.PositionSearchCommonRequest{JobtypeNames: []string{"SE"}, Salary: 600, PositionKeyword: &keyword}}
	got := ToGenericSearchParams(req)
	if got == nil || got.Salary != 600 || got.PositionKeyword != "go" || len(got.JobtypeNames) != 1 {
		t.Fatalf("unexpected mapped params: %+v", got)
	}
	if ToGenericSearchParams(nil) != nil {
		t.Fatalf("nil request should return nil")
	}
}

func TestToSearchEnvelope(t *testing.T) {
	ids := []mposition.ID{1, 2}
	positions := []*pmodel.PositionSummary{{ID: 1}, {ID: 2}}
	resp := ToSearchEnvelope(ids, positions, pmodel.PositionRecommendations("test"), nil, "", map[string][]string{"search_job_postings": {"SE"}})
	if len(resp.AllPositionIds) != 2 || len(resp.Positions) != 2 || len(resp.Recommendations) == 0 || len(resp.JobtypeNamesWithSameSearchFilters["search_job_postings"]) != 1 {
		t.Fatalf("unexpected envelope: %+v", resp)
	}
}

func TestToGenericSearchEnvelope(t *testing.T) {
	ids := []mposition.ID{1, 2}
	positions := []*pmodel.PositionSummary{{ID: 1}, {ID: 2}}
	params := &pmodel.GenericPositionSearchParams{CommonPositionSearchParams: pmodel.CommonPositionSearchParams{JobtypeNames: []string{"SE"}, Salary: 600}, PositionKeyword: "go"}
	resp := ToGenericSearchEnvelope(ids, positions, pmodel.PositionRecommendations("test"), params)
	if len(resp.AllPositionIds) != 2 || len(resp.Positions) != 2 || len(resp.Recommendations) == 0 {
		t.Fatalf("unexpected envelope: %+v", resp)
	}
	group := resp.SearchFilters.Jobtypes[pcontracts.ToolNameSearchJobPostings]
	if resp.SearchFilters == nil || len(group) != 1 || resp.SearchFilters.Salary != 600 {
		t.Fatalf("unexpected generic search filters: %+v", resp.SearchFilters)
	}
	if resp.SearchFilters.PositionKeyword == nil || *resp.SearchFilters.PositionKeyword != "go" {
		t.Fatalf("unexpected position keyword: %+v", resp.SearchFilters.PositionKeyword)
	}
}

func TestToGenericSearchFilterResponse(t *testing.T) {
	resp := ToGenericSearchFilterResponse(&pmodel.GenericPositionSearchParams{CommonPositionSearchParams: pmodel.CommonPositionSearchParams{JobtypeNames: []string{"SE"}, Salary: 600, Locations: []*address.LocationRequest{{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "東京都", CityName: "新宿区"}, {LocationType: address.LOCATION_TYPE_FULL_REMOTE_WORK}}}, PositionKeyword: "go"})
	if resp == nil {
		t.Fatal("expected response")
	}
	group := resp.Jobtypes[pcontracts.ToolNameSearchJobPostings]
	if len(group) != 1 || group[0].Value != "SE" || !group[0].Selected {
		t.Fatalf("unexpected jobtypes: %+v", resp.Jobtypes)
	}
	if resp.Salary != 600 {
		t.Fatalf("unexpected salary: %d", resp.Salary)
	}
	if resp.Locations == nil || resp.Locations.Residence == nil || resp.Locations.Residence.Address == nil {
		t.Fatalf("unexpected locations: %+v", resp.Locations)
	}
	if resp.Locations.Residence.Address.PrefectureName != "東京都" || resp.Locations.Residence.Address.CityName != "新宿区" {
		t.Fatalf("unexpected residence address: %+v", resp.Locations.Residence.Address)
	}
	if len(resp.Locations.WorkLocations) != 0 {
		t.Fatalf("unexpected work locations: %+v", resp.Locations.WorkLocations)
	}
	if resp.Locations.RemoteWorkPossible == nil || !*resp.Locations.RemoteWorkPossible {
		t.Fatalf("expected remote work possible to be true, got: %+v", resp.Locations.RemoteWorkPossible)
	}
	if resp.PositionKeyword == nil || *resp.PositionKeyword != "go" {
		t.Fatalf("unexpected position keyword: %+v", resp.PositionKeyword)
	}
}

func TestToCurrentJobTypeSearchFilterResponse(t *testing.T) {
	orig := jobSpecificParams.ITEngineerSearchFilters
	jobSpecificParams.ITEngineerSearchFilters = []*jobfilter.JobSearchFilterOtherFilter{{
		Key:     "ProgrammingLanguages",
		Name:    "言語（all）",
		Type:    jobfilter.JobSearchFilterTypeMultiple,
		Options: []*jobfilter.JobSearchFilterOtherFilterOption{{Label: "Go", Value: "Go"}},
	}}
	defer func() { jobSpecificParams.ITEngineerSearchFilters = orig }()

	searchFilters := &jobfilter.JobSearchFilter{Jobtypes: map[string][]*jobfilter.JobtypeSelectableItem{pcontracts.ToolNameSearchJobPostingsForITEngineer: {{JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Label: "ITコンサルタント（アプリ）", Value: "ITコンサルタント（アプリ）"}, Selected: true}}}}, SelectedOtherFilterOptions: map[string]map[string][]string{pcontracts.ToolNameSearchJobPostingsForITEngineer: {"言語（all）": {"Go"}}}}

	resp := ToCurrentJobTypeSearchFilterResponse(searchFilters, pcontracts.ToolNameSearchJobPostingsForITEngineer, map[string][]string{pcontracts.ToolNameSearchJobPostingsForITEngineer: {"ITコンサルタント（アプリ）", "Webアプリ開発"}})
	if resp == nil || resp.SearchFilters == nil {
		t.Fatalf("expected non-nil response")
	}
	if resp.ToolName != pcontracts.ToolNameSearchJobPostingsForITEngineer {
		t.Fatalf("unexpected ToolName: %s", resp.ToolName)
	}
	if len(resp.JobtypeNamesWithSameSearchFilters[pcontracts.ToolNameSearchJobPostingsForITEngineer]) != 2 {
		t.Fatalf("unexpected jobtypeNamesWithSameSearchFilters: %+v", resp.JobtypeNamesWithSameSearchFilters)
	}
	group := resp.SearchFilters.SelectedFilterOptions[pcontracts.ToolNameSearchJobPostingsForITEngineer]
	if resp.SearchFilters.SelectedFilterOptions == nil || len(group["言語（all）"]) != 1 {
		t.Fatalf("unexpected selected filter options: %+v", resp.SearchFilters.SelectedFilterOptions)
	}
	if resp.SearchFilters.OtherFilters == nil || len(resp.SearchFilters.OtherFilters[pcontracts.ToolNameSearchJobPostingsForITEngineer]) == 0 {
		t.Fatalf("unexpected other filters: %+v", resp.SearchFilters.OtherFilters)
	}
}

func TestGroupedSelectedFilterOptions_OmitsCommonAndCopiesGroups(t *testing.T) {
	got := groupedSelectedFilterOptions(map[string]map[string][]string{
		pcontracts.ToolNameSearchJobPostingsForITEngineer: {"言語（all）": {"Go"}},
		pcontracts.SelectedFilterOptionsCommonKey:         {"PositionKeyword": {"go"}},
	})
	if got == nil || len(got) != 1 {
		t.Fatalf("unexpected grouped options: %+v", got)
	}
	if values := got[pcontracts.ToolNameSearchJobPostingsForITEngineer]["言語（all）"]; len(values) != 1 || values[0] != "Go" {
		t.Fatalf("unexpected grouped values: %+v", got)
	}
}

func TestToJobSearchFilterResponse_PositionKeyword(t *testing.T) {
	keyword := "go"
	resp := toJobSearchFilterResponse(&jobfilter.JobSearchFilter{PositionKeyword: &keyword}, pcontracts.ToolNameSearchJobPostingsForITEngineer)
	if resp == nil || resp.PositionKeyword == nil || *resp.PositionKeyword != "go" {
		t.Fatalf("unexpected position keyword: %+v", resp)
	}
}
