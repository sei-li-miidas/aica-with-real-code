package params

import (
	"errors"
	"testing"

	pextensions "aica/api/api/mcptool/usecase/position/extensions"
	"aica/api/domain/public/master"
)

func TestFinancialSalesParams_SelectedOptionNamesByFilter(t *testing.T) {
	dive := "あり"
	p := &FinancialSalesParams{
		SalesStyleDive:           &dive,
		HandledFinancialProducts: []string{"保険", ""},
		IncentiveSystem:          "固定給重視",
	}

	selected := p.SelectedOptionNamesByFilter()
	if _, ok := selected["取扱商材（金融商品）"]["保険"]; !ok {
		t.Fatalf("expected selected financial product")
	}
	if _, ok := selected["新規飛び込み"]["あり"]; !ok {
		t.Fatalf("expected selected sales style dive")
	}
	if _, ok := selected["取扱商材（金融商品）"][""]; ok {
		t.Fatalf("empty option should be skipped")
	}
	if _, ok := selected["インセンティブ制度"]["固定給重視"]; !ok {
		t.Fatalf("expected selected incentive system")
	}
}

func TestFinancialSalesParams_RemotePositionOptionState(t *testing.T) {
	p := &FinancialSalesParams{}
	state := p.RemotePositionOptionState()
	if state == nil || state.HasOption {
		t.Fatalf("expected no remote option")
	}
}

func TestFinancialSalesParams_BuildExtensions(t *testing.T) {
	dive := "あり"
	p := &FinancialSalesParams{
		PositionKeyword:          "営業",
		SalesStyleDive:           &dive,
		HandledFinancialProducts: []string{"保険"},
		SalesMethodStyles:        []string{"保険"},
		TargetCustomerTypes:      []string{"新規"},
		Qualifications:           []string{"証券外務員一種/二種"},
		IndividualSalesStyles:    []string{"銀行窓口（テラー）"},
		IncentiveSystem:          "固定給重視",
	}
	ext, err := p.BuildExtensions(&stubResolver{
		resolveSalesStyleDive: func(_ *string) (int32, error) { return 1, nil },
		resolveSkills: func(_ []string) (master.Skills, error) {
			return master.Skills{
				&master.Skill{ID: 21},
			}, nil
		},
	})
	if err != nil || len(ext) != 5 {
		t.Fatalf("unexpected result: len=%d err=%v", len(ext), err)
	}
	keywordExt, ok := ext[len(ext)-1].(*pextensions.PositionKeywordExtension)
	if !ok {
		t.Fatalf("expected final extension to be PositionKeywordExtension, got %T", ext[len(ext)-1])
	}
	if keywordExt.Keyword() != "証券外務員一種/二種,銀行窓口（テラー）,固定給重視,営業" {
		t.Fatalf("unexpected keyword: %q", keywordExt.Keyword())
	}

	_, err = p.BuildExtensions(&stubResolver{
		resolveSalesStyleDive: func(_ *string) (int32, error) { return 0, errors.New("dive fail") },
		resolveSkills:         func(_ []string) (master.Skills, error) { return nil, nil },
	})
	if err == nil {
		t.Fatalf("expected sales style error")
	}

	_, err = p.BuildExtensions(&stubResolver{
		resolveSalesStyleDive: func(_ *string) (int32, error) { return 1, nil },
		resolveSkills:         func(_ []string) (master.Skills, error) { return nil, errors.New("skill fail") },
	})
	if err == nil {
		t.Fatalf("expected skill error")
	}
}
