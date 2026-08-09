package service

import (
	"errors"
	"testing"

	hydehistory "aica/api/domain/hyde_history"
)

type stubHydeHistoryRepo struct {
	getText    *string
	getErr     error
	saved      *hydehistory.HydeHistory
	saveErr    error
	getCalled  int
	saveCalled int
}

func (s *stubHydeHistoryRepo) GetHydeText(_ hydehistory.HydeType, _ string) (*string, error) {
	s.getCalled++
	if s.getErr != nil {
		return nil, s.getErr
	}
	return s.getText, nil
}

func (s *stubHydeHistoryRepo) Save(history *hydehistory.HydeHistory) error {
	s.saveCalled++
	s.saved = history
	if s.saveErr != nil {
		return s.saveErr
	}
	return nil
}

func TestHydeService_GetOrGenerateHydeText(t *testing.T) {
	t.Run("履歴が存在する場合は生成せず履歴を返す", func(t *testing.T) {
		cached := "cached text"
		repo := &stubHydeHistoryRepo{getText: &cached}
		svc := NewHydeService(&stubServiceLogger{}, repo)
		generateCalled := false

		got, err := svc.GetOrGenerateHydeText(hydehistory.HydeTypeJobType, "営業", true, func(string) (string, error) {
			generateCalled = true
			return "generated text", nil
		})
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if got != cached {
			t.Fatalf("expected cached text, got %q", got)
		}
		if generateCalled {
			t.Fatal("expected generate func not to be called")
		}
		if repo.getCalled != 1 {
			t.Fatalf("expected GetHydeText to be called once, got %d", repo.getCalled)
		}
		if repo.saveCalled != 0 {
			t.Fatalf("expected Save not to be called, got %d", repo.saveCalled)
		}
	})

	t.Run("履歴がない場合は生成して保存する", func(t *testing.T) {
		repo := &stubHydeHistoryRepo{}
		svc := NewHydeService(&stubServiceLogger{}, repo)

		got, err := svc.GetOrGenerateHydeText(hydehistory.HydeTypeIndustry, "IT", true, func(keyword string) (string, error) {
			return keyword + " generated", nil
		})
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if got != "IT generated" {
			t.Fatalf("unexpected generated text: %q", got)
		}
		if repo.getCalled != 1 {
			t.Fatalf("expected GetHydeText to be called once, got %d", repo.getCalled)
		}
		if repo.saveCalled != 1 {
			t.Fatalf("expected Save to be called once, got %d", repo.saveCalled)
		}
		if repo.saved == nil {
			t.Fatal("expected saved history")
		}
		if repo.saved.HydeType != hydehistory.HydeTypeIndustry {
			t.Fatalf("unexpected HydeType: %v", repo.saved.HydeType)
		}
		if repo.saved.Keyword != "IT" {
			t.Fatalf("unexpected Keyword: %q", repo.saved.Keyword)
		}
		if repo.saved.HydeText != "IT generated" {
			t.Fatalf("unexpected HydeText: %q", repo.saved.HydeText)
		}
		if repo.saved.LastUsedAt.IsZero() {
			t.Fatal("expected LastUsedAt to be set")
		}
	})

	t.Run("履歴を使わない場合は生成のみ行う", func(t *testing.T) {
		repo := &stubHydeHistoryRepo{}
		svc := NewHydeService(&stubServiceLogger{}, repo)

		got, err := svc.GetOrGenerateHydeText(hydehistory.HydeTypeJobType, "開発", false, func(string) (string, error) {
			return "generated only", nil
		})
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if got != "generated only" {
			t.Fatalf("unexpected generated text: %q", got)
		}
		if repo.getCalled != 0 {
			t.Fatalf("expected GetHydeText not to be called, got %d", repo.getCalled)
		}
		if repo.saveCalled != 0 {
			t.Fatalf("expected Save not to be called, got %d", repo.saveCalled)
		}
	})

	t.Run("履歴取得でエラーが発生した場合はエラーを返す", func(t *testing.T) {
		repo := &stubHydeHistoryRepo{getErr: errors.New("get failed")}
		svc := NewHydeService(&stubServiceLogger{}, repo)
		generateCalled := false

		_, err := svc.GetOrGenerateHydeText(hydehistory.HydeTypeJobType, "営業", true, func(string) (string, error) {
			generateCalled = true
			return "generated", nil
		})
		if err == nil || err.Error() != "get failed" {
			t.Fatalf("expected get failed error, got %v", err)
		}
		if generateCalled {
			t.Fatal("expected generate func not to be called")
		}
	})

	t.Run("生成でエラーが発生した場合はエラーを返す", func(t *testing.T) {
		repo := &stubHydeHistoryRepo{}
		svc := NewHydeService(&stubServiceLogger{}, repo)

		_, err := svc.GetOrGenerateHydeText(hydehistory.HydeTypeJobType, "営業", true, func(string) (string, error) {
			return "", errors.New("generate failed")
		})
		if err == nil || err.Error() != "generate failed" {
			t.Fatalf("expected generate failed error, got %v", err)
		}
		if repo.saveCalled != 0 {
			t.Fatalf("expected Save not to be called, got %d", repo.saveCalled)
		}
	})

	t.Run("保存でエラーが発生した場合はエラーを返す", func(t *testing.T) {
		repo := &stubHydeHistoryRepo{saveErr: errors.New("save failed")}
		svc := NewHydeService(&stubServiceLogger{}, repo)

		_, err := svc.GetOrGenerateHydeText(hydehistory.HydeTypeJobType, "営業", true, func(string) (string, error) {
			return "generated text", nil
		})
		if err == nil || err.Error() != "save failed" {
			t.Fatalf("expected save failed error, got %v", err)
		}
		if repo.saveCalled != 1 {
			t.Fatalf("expected Save to be called once, got %d", repo.saveCalled)
		}
	})
}
