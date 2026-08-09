package support

import (
	"testing"

	pmodel "aica/api/api/mcptool/usecase/position/model"
	address "aica/api/api/mcptool/usecase/shared"
)

type locationLookupStub struct {
	commutingResult []int
	workResult      []int
	err             error
	commutingCalls  int
	workCalls       int
}

func (s *locationLookupStub) GetCommutingAreasFromResidence(_ string, _ string) ([]int, error) {
	s.commutingCalls++
	if s.err != nil {
		return nil, s.err
	}
	return s.commutingResult, nil
}

func (s *locationLookupStub) GetCityIDsFromWorkLocations(_ []struct{ PrefectureName, CityName string }) ([]int, error) {
	s.workCalls++
	if s.err != nil {
		return nil, s.err
	}
	return s.workResult, nil
}

func TestResolveLocationIDs_NilLookupOrParamsReturnsNil(t *testing.T) {
	got, err := ResolveLocationIDs(nil, &pmodel.GenericPositionSearchParams{})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got != nil {
		t.Fatalf("expected nil city IDs for nil lookup, got: %#v", got)
	}

	got, err = ResolveLocationIDs(&locationLookupStub{}, nil)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got != nil {
		t.Fatalf("expected nil city IDs for nil params, got: %#v", got)
	}
}

func TestResolveLocationIDs_FullyRemoteReturnsNil(t *testing.T) {
	params := &pmodel.GenericPositionSearchParams{
		CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
			Locations: []*address.LocationRequest{{LocationType: address.LOCATION_TYPE_FULL_REMOTE_WORK}},
		},
	}

	got, err := ResolveLocationIDs(&locationLookupStub{}, params)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if got != nil {
		t.Fatalf("expected nil city IDs for fully remote, got: %#v", got)
	}
}

func TestResolveLocationIDs_ResidenceAndWorkLocationsDeduplicated(t *testing.T) {
	params := &pmodel.GenericPositionSearchParams{
		CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
			Locations: []*address.LocationRequest{
				{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "東京都", CityName: "新宿区"},
				{LocationType: address.LOCATION_TYPE_WORK_LOCATION, PrefectureName: "東京都", CityName: "渋谷区"},
			},
		},
	}

	got, err := ResolveLocationIDs(&locationLookupStub{commutingResult: []int{1, 2}, workResult: []int{2, 3}}, params)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(got) != 3 || got[0] != 1 || got[1] != 2 || got[2] != 3 {
		t.Fatalf("unexpected city IDs: %#v", got)
	}
}

func TestResolveLocationIDs_ExplicitCommutingAreasSkipResidenceLookup(t *testing.T) {
	params := &pmodel.GenericPositionSearchParams{
		CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
			Locations: []*address.LocationRequest{
				{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "東京都", CityName: "新宿区"},
				{LocationType: address.LOCATION_TYPE_COMMUTING_AREAS, PrefectureName: "東京都", CityName: "渋谷区"},
				{LocationType: address.LOCATION_TYPE_WORK_LOCATION, PrefectureName: "東京都", CityName: "港区"},
			},
		},
	}

	lookup := &locationLookupStub{commutingResult: []int{1, 2}, workResult: []int{2, 3}}
	got, err := ResolveLocationIDs(lookup, params)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(got) != 2 || got[0] != 2 || got[1] != 3 {
		t.Fatalf("unexpected city IDs: %#v", got)
	}
	if lookup.commutingCalls != 0 {
		t.Fatalf("expected commuting lookup to be skipped, got %d calls", lookup.commutingCalls)
	}
	if lookup.workCalls != 1 {
		t.Fatalf("expected direct city lookup once, got %d calls", lookup.workCalls)
	}
}
