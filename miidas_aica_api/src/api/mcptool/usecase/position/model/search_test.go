package model

import (
	address "aica/api/api/mcptool/usecase/shared"
	"testing"
)

func TestSearchModel_BasicHelpers(t *testing.T) {
	recs := PositionRecommendations("test")
	if len(recs) == 0 {
		t.Fatalf("expected position recommendations")
	}

	var p *GenericPositionSearchParams
	if got := p.GetSalary(); got != 0 {
		t.Fatalf("unexpected salary: %d", got)
	}

	p = &GenericPositionSearchParams{
		CommonPositionSearchParams: CommonPositionSearchParams{
			Salary:    500,
			Locations: []*address.LocationRequest{},
		},
	}
	if got := p.GetSalary(); got != 500 {
		t.Fatalf("unexpected salary: %d", got)
	}
	if p.Locations == nil {
		t.Fatalf("expected locations slice, got nil")
	}
}
