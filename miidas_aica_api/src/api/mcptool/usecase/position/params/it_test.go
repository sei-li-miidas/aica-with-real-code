package params

import (
	"errors"
	"testing"

	"aica/api/domain/public/master"
)

func TestITEngineerParams_SelectedOptionNamesByFilter(t *testing.T) {
	p := &ITEngineerParams{
		ProgrammingLanguages: []string{"Go", ""},
	}
	selected := p.SelectedOptionNamesByFilter()
	if _, ok := selected["言語（all）"]["Go"]; !ok {
		t.Fatalf("expected Go to be selected")
	}
	if _, ok := selected["言語（all）"][""]; ok {
		t.Fatalf("empty option should be skipped")
	}
}

func TestITEngineerParams_RemotePositionOptionState(t *testing.T) {
	remoteWork := true
	p := &ITEngineerParams{RemoteWorkPossible: &remoteWork}
	state := p.RemotePositionOptionState()
	if state == nil || !state.CurrentChoice {
		t.Fatalf("expected remote option on")
	}
}

func TestITEngineerParams_BuildExtensions(t *testing.T) {
	t.Run("スキルなしの場合", func(t *testing.T) {
		remoteWork := true
		p := &ITEngineerParams{
			RemoteWorkPossible: &remoteWork,
			PositionKeyword:    "go",
		}
		ext, err := p.BuildExtensions(&stubResolver{
			resolveSkills: func(_ []string) (master.Skills, error) { return nil, nil },
		})
		if err != nil || len(ext) != 2 {
			t.Fatalf("unexpected result: len=%d err=%v", len(ext), err)
		}
	})

	t.Run("スキルありの場合", func(t *testing.T) {
		p := &ITEngineerParams{
			ProgrammingLanguages: []string{"Go"},
			CloudServices:        []string{"AWS"},
		}
		calls := 0
		ext, err := p.BuildExtensions(&stubResolver{
			resolveSkills: func(names []string) (master.Skills, error) {
				calls++
				if len(names) != 1 {
					t.Fatalf("expected per-filter skill resolution")
				}
				return master.Skills{
					&master.Skill{ID: 11},
				}, nil
			},
		})
		if err != nil || len(ext) != 4 {
			t.Fatalf("unexpected result: len=%d err=%v", len(ext), err)
		}
		if calls != 2 {
			t.Fatalf("expected 2 resolver calls, got %d", calls)
		}
	})

	t.Run("リゾルバがエラーを返す場合", func(t *testing.T) {
		p := &ITEngineerParams{
			ProgrammingLanguages: []string{"Go"},
		}
		_, err := p.BuildExtensions(&stubResolver{
			resolveSkills: func(_ []string) (master.Skills, error) { return nil, errors.New("failed") },
		})
		if err == nil {
			t.Fatalf("expected error")
		}
	})
}
