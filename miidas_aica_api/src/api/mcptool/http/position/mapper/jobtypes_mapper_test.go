package mapper

import (
	dto "aica/api/api/mcptool/http/position/dto"
	"testing"
)

func TestToJobTypesSelectedRequest(t *testing.T) {
	req := &dto.JobTypesSelectionRequest{JobtypeNames: []string{"A", "B"}}
	got := ToJobTypesSelectedRequest(req)
	if got == nil || len(got.JobtypeNames) != 2 {
		t.Fatalf("unexpected mapping: %+v", got)
	}
	if ToJobTypesSelectedRequest(nil) != nil {
		t.Fatalf("nil request should return nil")
	}
}

func TestToJobTypeSearchFilterRequest(t *testing.T) {
	req := &dto.JobTypeSearchFilterRequest{JobtypeName: "A"}
	got := ToJobTypeSearchFilterRequest(req)
	if got == nil || got.JobtypeName != "A" {
		t.Fatalf("unexpected mapping: %+v", got)
	}
	if ToJobTypeSearchFilterRequest(nil) != nil {
		t.Fatalf("nil request should return nil")
	}
}
