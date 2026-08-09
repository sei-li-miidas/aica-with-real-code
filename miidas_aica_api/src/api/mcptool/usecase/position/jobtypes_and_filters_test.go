package position

import (
	tmock "aica/api/api/mcptool/testutil/mock"
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	pmodel "aica/api/api/mcptool/usecase/position/model"
	address "aica/api/api/mcptool/usecase/shared"
	jobfilter "aica/api/domain/jobfilter"
	"aica/api/domain/public/master"
	"errors"
	"testing"

	"github.com/stretchr/testify/assert"
)

type testResolver struct {
	resolveIDs func(names []string) ([]int32, error)
}

func (r *testResolver) ExistsPrefectureCity(prefectureName string, cityName string) bool { return true }
func (r *testResolver) ResolveJobTypeSmallIDs(names []string) ([]int32, error) {
	if r.resolveIDs != nil {
		return r.resolveIDs(names)
	}
	return []int32{1}, nil
}
func (r *testResolver) ResolveLocations(locations []*address.LocationRequest, remoteWorkPossible bool) ([]int32, *address.LocationRequest, []*address.LocationRequest, []*address.LocationRequest, error) {
	return nil, nil, nil, nil, nil
}
func (r *testResolver) ResolveLocationByName(name string) (*address.LocationRequest, error) {
	return nil, nil
}
func (r *testResolver) ResolveSkills(skillNames []string) (master.Skills, error)    { return nil, nil }
func (r *testResolver) ResolveDayOffs(dayOffs *[]string) ([]int32, error)           { return nil, nil }
func (r *testResolver) ResolveAverageOvertime(overtime *string) (int32, error)      { return 0, nil }
func (r *testResolver) ResolveSalesStyleDive(salesStyleDive *string) (int32, error) { return 0, nil }

type testToolResolver struct {
	toolNameByJobtype map[string]string
}

func (r *testToolResolver) ToolNameByJobtypeName(name string) string {
	if r == nil {
		return ""
	}
	return r.toolNameByJobtype[name]
}

func (r *testToolResolver) JobtypeNamesByToolName(toolName string) []string { return nil }

type testJobtypesWriter struct {
	merge func(sessionID string, selectedGroupKey string, groupedJobtypeNames map[string][]string) error
}

func (w *testJobtypesWriter) MergeJobTypes(sessionID string, selectedGroupKey string, groupedJobtypeNames map[string][]string) error {
	if w.merge != nil {
		return w.merge(sessionID, selectedGroupKey, groupedJobtypeNames)
	}
	return nil
}

type testFilterReader struct {
	get func(sessionID string) (*jobfilter.JobSearchFilter, error)
}

func (r *testFilterReader) GetBySessionID(sessionID string) (*jobfilter.JobSearchFilter, error) {
	if r.get != nil {
		return r.get(sessionID)
	}
	return nil, nil
}

func TestJobTypesSelectedUseCase(t *testing.T) {
	uc := NewJobTypesSelectedUseCase(&tmock.MockLogger{}, &testJobtypesWriter{}, &testResolver{}, &testToolResolver{})
	_, err := uc.Execute("", nil)
	assert.Error(t, err)

	uc = NewJobTypesSelectedUseCase(&tmock.MockLogger{}, nil, &testResolver{}, &testToolResolver{})
	_, err = uc.Execute("s", &pmodel.JobTypesSelection{JobtypeNames: []string{"A"}})
	assert.Error(t, err)

	uc = NewJobTypesSelectedUseCase(&tmock.MockLogger{}, &testJobtypesWriter{}, nil, &testToolResolver{})
	_, err = uc.Execute("s", &pmodel.JobTypesSelection{JobtypeNames: []string{"A"}})
	assert.Error(t, err)

	uc = NewJobTypesSelectedUseCase(&tmock.MockLogger{}, &testJobtypesWriter{}, &testResolver{
		resolveIDs: func(names []string) ([]int32, error) { return nil, errors.New("invalid") },
	}, &testToolResolver{})
	_, err = uc.Execute("s", &pmodel.JobTypesSelection{JobtypeNames: []string{"A"}})
	assert.EqualError(t, err, "invalid")

	called := false
	uc = NewJobTypesSelectedUseCase(&tmock.MockLogger{}, &testJobtypesWriter{
		merge: func(sessionID string, groupKey string, groupedJobtypeNames map[string][]string) error {
			called = true
			assert.Equal(t, "s", sessionID)
			assert.Equal(t, pcontracts.ToolNameSearchJobPostingsForITEngineer, groupKey)
			assert.Equal(t, map[string][]string{pcontracts.ToolNameSearchJobPostingsForITEngineer: {"A"}}, groupedJobtypeNames)
			return nil
		},
	}, &testResolver{}, &testToolResolver{toolNameByJobtype: map[string]string{"A": pcontracts.ToolNameSearchJobPostingsForITEngineer}})
	result, err := uc.Execute("s", &pmodel.JobTypesSelection{JobtypeNames: []string{"A"}})
	assert.NoError(t, err)
	assert.Equal(t, pcontracts.ToolNameSearchJobPostingsForITEngineer, result.ToolName)
	assert.True(t, called)

	called = false
	uc = NewJobTypesSelectedUseCase(&tmock.MockLogger{}, &testJobtypesWriter{
		merge: func(sessionID string, groupKey string, groupedJobtypeNames map[string][]string) error {
			called = true
			assert.Equal(t, "s", sessionID)
			assert.Equal(t, pcontracts.ToolNameSearchJobPostings, groupKey)
			assert.Nil(t, groupedJobtypeNames)
			return nil
		},
	}, &testResolver{}, &testToolResolver{})
	result, err = uc.Execute("s", &pmodel.JobTypesSelection{})
	assert.NoError(t, err)
	assert.Equal(t, pcontracts.ToolNameSearchJobPostings, result.ToolName)
	assert.True(t, called)
	called = false
	uc = NewJobTypesSelectedUseCase(&tmock.MockLogger{}, &testJobtypesWriter{
		merge: func(sessionID string, groupKey string, groupedJobtypeNames map[string][]string) error {
			called = true
			assert.Equal(t, pcontracts.ToolNameSearchJobPostingsForITEngineer, groupKey)
			assert.Equal(t, map[string][]string{
				pcontracts.ToolNameSearchJobPostingsForITEngineer:          {"A"},
				pcontracts.ToolNameSearchJobPostingsForSalesFinancialSales: {"B"},
			}, groupedJobtypeNames)
			return nil
		},
	}, &testResolver{}, &testToolResolver{toolNameByJobtype: map[string]string{
		"A": pcontracts.ToolNameSearchJobPostingsForITEngineer,
		"B": pcontracts.ToolNameSearchJobPostingsForSalesFinancialSales,
	}})
	result, err = uc.Execute("s", &pmodel.JobTypesSelection{JobtypeNames: []string{"A", "B"}})
	assert.NoError(t, err)
	assert.Equal(t, pcontracts.ToolNameSearchJobPostingsForITEngineer, result.ToolName)
	assert.True(t, called)

}

func TestJobTypeSearchFilterUseCaseAndHelpers(t *testing.T) {
	uc := NewJobTypeSearchFilterUseCase(&tmock.MockLogger{}, nil, &testResolver{})
	_, err := uc.Execute("s", &pmodel.JobTypeSearchFilterQuery{JobtypeName: "A"})
	assert.Error(t, err)

	uc = NewJobTypeSearchFilterUseCase(&tmock.MockLogger{}, &testFilterReader{}, nil)
	_, err = uc.Execute("s", &pmodel.JobTypeSearchFilterQuery{JobtypeName: "A"})
	assert.Error(t, err)

	uc = NewJobTypeSearchFilterUseCase(&tmock.MockLogger{}, &testFilterReader{}, &testResolver{
		resolveIDs: func(names []string) ([]int32, error) { return nil, errors.New("invalid") },
	})
	_, err = uc.Execute("s", &pmodel.JobTypeSearchFilterQuery{JobtypeName: "A"})
	assert.EqualError(t, err, "invalid")

	filter := &jobfilter.JobSearchFilter{
		Jobtypes: map[string][]*jobfilter.JobtypeSelectableItem{
			"search_job_postings": {
				{JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{
					JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Value: "A"},
					Selected:                         true,
				}},
			},
		},
	}
	uc = NewJobTypeSearchFilterUseCase(&tmock.MockLogger{}, &testFilterReader{
		get: func(sessionID string) (*jobfilter.JobSearchFilter, error) {
			assert.Equal(t, "s", sessionID)
			return filter, nil
		},
	}, &testResolver{})
	res, err := uc.Execute("s", &pmodel.JobTypeSearchFilterQuery{})
	assert.NoError(t, err)
	assert.Equal(t, "search_job_postings", res.ToolName)
	assert.NotNil(t, res.SearchFilter)

	assert.Equal(t, "search_job_postings", selectedToolNameFromFilter(filter))
	assert.Equal(t, "", selectedToolNameFromFilter(&jobfilter.JobSearchFilter{}))
}
