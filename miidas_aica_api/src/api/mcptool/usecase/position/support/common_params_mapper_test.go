package support

import "testing"

func TestConvertDayOffs_AndOvertime(t *testing.T) {
	t.Run("休日がnilまたは空の場合", func(t *testing.T) {
		v, err := ConvertDayOffs(nil)
		if err != nil || v != nil {
			t.Fatalf("unexpected: %v %v", v, err)
		}
		empty := []string{}
		v, err = ConvertDayOffs(&empty)
		if err != nil || v != nil {
			t.Fatalf("unexpected: %v %v", v, err)
		}
	})

	dayOffs := []string{"土日祝休み", "毎週2日休み", "その他"}
	values, err := ConvertDayOffs(&dayOffs)
	if err != nil || len(values) != 4 {
		t.Fatalf("unexpected convert result: %v %v", values, err)
	}
	if values[0] != 1 || values[1] != 2 || values[2] != 3 || values[3] != 4 {
		t.Fatalf("unexpected dayoffs map result: %v", values)
	}

	t.Run("休日が不正な場合", func(t *testing.T) {
		invalid := []string{"invalid"}
		if _, err := ConvertDayOffs(&invalid); err == nil {
			t.Fatalf("expected error")
		}
	})

	if v, err := ConvertAverageOvertime(nil); err != nil || v != 0 {
		t.Fatalf("unexpected error: %v %v", v, err)
	}
	empty := ""
	if v, err := ConvertAverageOvertime(&empty); err != nil || v != 0 {
		t.Fatalf("unexpected error: %v %v", v, err)
	}
	none := "原則なし"
	if v, err := ConvertAverageOvertime(&none); err != nil || v != 1 {
		t.Fatalf("unexpected error: %v %v", v, err)
	}
	ten := "10時間以内"
	if v, err := ConvertAverageOvertime(&ten); err != nil || v != 2 {
		t.Fatalf("unexpected error: %v %v", v, err)
	}
	invalidOt := "invalid"
	if _, err := ConvertAverageOvertime(&invalidOt); err == nil {
		t.Fatalf("unexpected error: %v", err)
	}
}
