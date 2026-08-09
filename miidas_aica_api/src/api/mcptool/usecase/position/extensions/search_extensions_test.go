package extensions

import (
	"testing"

	jobfilter "aica/api/domain/jobfilter"
	"aica/api/domain/public/master"
	"miidas/m2/user/marketvalue/grpc/iface"
)

func TestRemoteWorkExtension_ApplyMV2(t *testing.T) {
	ext := NewRemoteWorkExtension(true)
	positionWill := &iface.Position{
		RemoteWork: &iface.RemoteWork{
			Value: &iface.RemoteWorkValue{},
		},
	}

	ext.ApplyMV2(nil, nil, positionWill)
	if positionWill.RemoteWork.Importance != 3 {
		t.Fatalf("unexpected importance: %d", positionWill.RemoteWork.Importance)
	}
}

func TestRemoteWorkExtension_Disabled(t *testing.T) {
	ext := NewRemoteWorkExtension(false)
	positionWill := &iface.Position{
		RemoteWork: &iface.RemoteWork{Importance: 0, Value: &iface.RemoteWorkValue{}},
	}
	ext.ApplyMV2(nil, nil, positionWill)
	if positionWill.RemoteWork.Importance != 0 {
		t.Fatalf("expected no change")
	}
	if ext.RemoteWorkPossible() {
		t.Fatalf("expected false")
	}
	if _, of := ext.BuildSelectedOtherFilterOptions(); len(of) != 0 {
		t.Fatalf("expected empty other filter")
	}
}

func TestPositionKeywordExtension(t *testing.T) {
	ext := NewPositionKeywordExtension("go")
	ext.ApplyMV2(nil, nil, nil)
	if _, of := ext.BuildSelectedOtherFilterOptions(); len(of) != 0 {
		t.Fatalf("expected empty filter")
	}
	if ext.Keyword() != "go" {
		t.Fatalf("unexpected keyword")
	}
}

func TestSkillExtension(t *testing.T) {
	t.Run("空の場合", func(t *testing.T) {
		ext := NewSkillExtension(nil, nil)
		positionWill := &iface.Position{}
		ext.ApplyMV2(nil, nil, positionWill)
		if positionWill.Skill != nil {
			t.Fatalf("expected nil skill")
		}
		if _, of := ext.BuildSelectedOtherFilterOptions(); len(of) != 0 {
			t.Fatalf("expected empty other filter")
		}
	})
	t.Run("値がある場合", func(t *testing.T) {
		skills := master.Skills{
			&master.Skill{ID: 1, Name: "skill1"},
			&master.Skill{ID: 2, Name: "skill2"},
		}
		ext := NewSkillExtension(&jobfilter.JobSearchFilterOtherFilter{Name: "default"}, skills)
		positionWill := &iface.Position{}
		ext.ApplyMV2(nil, nil, positionWill)
		if positionWill.Skill == nil || positionWill.Skill.Importance != 3 || len(positionWill.Skill.Value) != 2 {
			t.Fatalf("unexpected skill setup")
		}
	})
}

func TestSalesStyleDiveExtension(t *testing.T) {
	t.Run("無効な場合", func(t *testing.T) {
		ext := NewSalesStyleDiveExtension("", 0)
		p := &iface.Position{SalesStyleDive: &iface.SalesStyleDive{}}
		ext.ApplyMV2(nil, nil, p)
		if p.SalesStyleDive.Importance != 0 {
			t.Fatalf("expected unchanged")
		}
		_, of := ext.BuildSelectedOtherFilterOptions()
		if len(of) != 1 || of[0] != "" {
			t.Fatalf("unexpected other filter")
		}
	})
	t.Run("有効な場合", func(t *testing.T) {
		ext := NewSalesStyleDiveExtension("なし", 2)
		p := &iface.Position{SalesStyleDive: &iface.SalesStyleDive{}}
		ext.ApplyMV2(nil, nil, p)
		if p.SalesStyleDive.Importance != 3 || *p.SalesStyleDive.Value != 2 {
			t.Fatalf("unexpected style dive")
		}
		_, of := ext.BuildSelectedOtherFilterOptions()
		if len(of) != 1 || of[0] != "なし" {
			t.Fatalf("unexpected selected option")
		}
	})
}
