package mapper

import (
	pmodel "aica/api/api/mcptool/usecase/position/model"
	"testing"
)

func TestToDetailResponse(t *testing.T) {
	resp := &pmodel.PositionDetail{}
	if ToDetailResponse(resp) != resp {
		t.Fatalf("expected passthrough")
	}
	if ToDetailResponse(nil) != nil {
		t.Fatalf("nil should return nil")
	}
}
