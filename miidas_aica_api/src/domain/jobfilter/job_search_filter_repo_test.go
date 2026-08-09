package jobfilter

import (
	"aica/api/domain/jobtype"
	"errors"
	"testing"

	"gorm.io/datatypes"
)

func TestJobSearchFilterRepository_GetTypedJobSearchFilterBySessionID_ReturnsErrorWhenDescriptionLookupFails(t *testing.T) {
	repo := NewJobSearchFilterRepository(nil)
	repo.findRecordByID = func(sessionID string) (*jobSearchFilter, error) {
		if sessionID == "" {
			return nil, nil
		}
		return &jobSearchFilter{
			SessionID:             "session-1",
			Jobtypes:              datatypes.JSON(`{"group":[{"Value":"engineer","Label":"engineer","Selected":true}]}`),
			Locations:             datatypes.JSON(`null`),
			Salary:                intPtr(500),
			SelectedFilterOptions: datatypes.JSON(`{}`),
		}, nil
	}
	repo.findJobtypesByIDs = func([]string) ([]*jobtype.JobTypeSmall, error) {
		return nil, errors.New("description lookup failed")
	}

	filter, err := repo.GetTypedJobSearchFilterBySessionID("session-1")
	if err == nil {
		t.Fatal("expected description lookup error")
	}
	if filter != nil {
		t.Fatalf("expected no filter on error, got: %#v", filter)
	}
}

func intPtr(v int) *int {
	return &v
}

func boolPtr(v bool) *bool {
	return &v
}

func TestNormalizeLocations_Nil(t *testing.T) {
	// should not panic
	normalizeLocations(nil)
}

func TestNormalizeLocations_EmptyWorkLocations(t *testing.T) {
	loc := &JobSearchFilterLocations{}
	normalizeLocations(loc)
	if loc.RemoteWorkPossible != nil {
		t.Fatalf("expected RemoteWorkPossible to remain nil, got %v", *loc.RemoteWorkPossible)
	}
}

func TestNormalizeLocations_FullRemoteSelectedTrue(t *testing.T) {
	loc := &JobSearchFilterLocations{
		WorkLocations: []*JobSearchFilterLocationSelectableItem{
			{Label: "フルリモート", Selected: true},
		},
	}
	normalizeLocations(loc)
	if len(loc.WorkLocations) != 0 {
		t.Fatalf("expected フルリモート to be removed, got %+v", loc.WorkLocations)
	}
	if loc.RemoteWorkPossible == nil || !*loc.RemoteWorkPossible {
		t.Fatalf("expected RemoteWorkPossible to be true")
	}
}

func TestNormalizeLocations_FullRemoteSelectedFalse(t *testing.T) {
	loc := &JobSearchFilterLocations{
		WorkLocations: []*JobSearchFilterLocationSelectableItem{
			{Label: "フルリモート", Selected: false},
		},
	}
	normalizeLocations(loc)
	if len(loc.WorkLocations) != 0 {
		t.Fatalf("expected フルリモート to be removed regardless of Selected, got %+v", loc.WorkLocations)
	}
	if loc.RemoteWorkPossible == nil || !*loc.RemoteWorkPossible {
		t.Fatalf("expected RemoteWorkPossible to be true")
	}
}

func TestNormalizeLocations_MixedWorkLocations(t *testing.T) {
	loc := &JobSearchFilterLocations{
		WorkLocations: []*JobSearchFilterLocationSelectableItem{
			{Label: "東京都港区", PrefectureName: "東京都", CityName: "港区", Selected: true},
			{Label: "フルリモート", Selected: true},
			{Label: "大阪府大阪市", PrefectureName: "大阪府", CityName: "大阪市", Selected: false},
		},
	}
	normalizeLocations(loc)
	if len(loc.WorkLocations) != 2 {
		t.Fatalf("expected 2 work locations after removing フルリモート, got %+v", loc.WorkLocations)
	}
	if loc.WorkLocations[0].Label != "東京都港区" || loc.WorkLocations[1].Label != "大阪府大阪市" {
		t.Fatalf("unexpected work locations order: %+v", loc.WorkLocations)
	}
	if loc.RemoteWorkPossible == nil || !*loc.RemoteWorkPossible {
		t.Fatalf("expected RemoteWorkPossible to be true")
	}
}

func TestNormalizeLocations_NoFullRemote(t *testing.T) {
	loc := &JobSearchFilterLocations{
		WorkLocations: []*JobSearchFilterLocationSelectableItem{
			{Label: "東京都港区", PrefectureName: "東京都", CityName: "港区", Selected: true},
		},
	}
	normalizeLocations(loc)
	if len(loc.WorkLocations) != 1 {
		t.Fatalf("expected work locations unchanged, got %+v", loc.WorkLocations)
	}
	if loc.RemoteWorkPossible != nil {
		t.Fatalf("expected RemoteWorkPossible to remain nil, got %v", *loc.RemoteWorkPossible)
	}
}

func TestNormalizeLocations_RemoteWorkPossibleAlreadySet(t *testing.T) {
	loc := &JobSearchFilterLocations{
		WorkLocations: []*JobSearchFilterLocationSelectableItem{
			{Label: "フルリモート", Selected: true},
		},
		RemoteWorkPossible: boolPtr(false),
	}
	normalizeLocations(loc)
	if len(loc.WorkLocations) != 0 {
		t.Fatalf("expected フルリモート to be removed, got %+v", loc.WorkLocations)
	}
	// フルリモートエントリが存在したので true に上書きされることを確認
	if loc.RemoteWorkPossible == nil || !*loc.RemoteWorkPossible {
		t.Fatalf("expected RemoteWorkPossible to be overwritten to true")
	}
}
