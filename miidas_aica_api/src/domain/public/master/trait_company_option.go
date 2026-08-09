package master

import (
	"github.com/samber/lo"

	"aica/api/sdk/slice"
)

type (
	TraitCompanyOption struct {
		TraitCompanyID MasterTraitCompanyID // 企業特徴マスタID
		Value          int                  // 選択肢値
		Name           string               // 選択肢名称 (選択値表示内容)
		UserSideName   string               // ユーザ側表示内容
		SortOrder      int                  // 選択肢並び順
	}

	// TraitCompanyOptionForUser ユーザー向け
	TraitCompanyOptionForUser struct {
		TraitCompanyID MasterTraitCompanyID // 企業特徴マスタID
		Value          int                  // 選択肢値
		UserSideName   string               // ユーザ側表示内容
		SortOrder      int                  // 選択肢並び順
	}

	// TraitCompanyOptionForCorp 企業向け
	TraitCompanyOptionForCorp struct {
		TraitCompanyID MasterTraitCompanyID // 企業特徴マスタID
		Value          int                  // 選択肢値
		CorpSideName   string               // 選択肢名称 (選択値表示内容)
		SortOrder      int                  // 選択肢並び順
	}

	TraitCompanyOptionListForUser []*TraitCompanyOptionForUser
	TraitCompanyOptionListForCorp []*TraitCompanyOptionForCorp
)

// TableName target table
func (m TraitCompanyOption) TableName() string {
	return "master.trait_company_option"
}

func (m *TraitCompanyOptionForUser) GetUserSideName() string {
	if m == nil {
		return ""
	}
	return m.UserSideName
}

func (m *TraitCompanyOptionForUser) GetValue() int {
	if m == nil {
		return 0
	}
	return m.Value
}

func (s TraitCompanyOptionListForUser) ValueMap() map[int]*TraitCompanyOptionForUser {
	return lo.SliceToMap(s, func(e *TraitCompanyOptionForUser) (int, *TraitCompanyOptionForUser) {
		return e.Value, e
	})
}

func (s TraitCompanyOptionListForUser) Get(value int) *TraitCompanyOptionForUser {
	ret, found := slice.Find(s, func(e *TraitCompanyOptionForUser) bool {
		return e.Value == value
	})
	if found {
		return ret
	} else {
		return nil
	}
}

func (s TraitCompanyOptionListForUser) GetByBool(on bool) *TraitCompanyOptionForUser {
	v := func(on bool) int {
		if on {
			return 1
		}
		return 2
	}(on)
	return s.Get(v)
}
