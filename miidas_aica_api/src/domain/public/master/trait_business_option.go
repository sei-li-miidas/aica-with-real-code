package master

import (
	"github.com/samber/lo"
)

type (
	TraitBusinessOption struct {
		TraitBusinessID MasterTraitBusinessID
		Value           int
		Name            string
		UserSideName    string
		SortOrder       int
	}

	TraitBusinessOptionForUser struct {
		TraitBusinessID MasterTraitBusinessID
		Value           int
		UserSideName    string
		SortOrder       int
	}

	TraitBusinessOptionListForUser []*TraitBusinessOptionForUser
)

// TableName target table
func (m TraitBusinessOption) TableName() string {
	return "master.trait_business_option"
}

func (m *TraitBusinessOptionForUser) GetUserSideName() string {
	if m == nil {
		return ""
	}
	return m.UserSideName
}

func (m *TraitBusinessOptionForUser) GetValue() int {
	if m == nil {
		return 0
	}
	return m.Value
}

func (s TraitBusinessOptionListForUser) ValueMap() map[int]*TraitBusinessOptionForUser {
	return lo.SliceToMap(s, func(e *TraitBusinessOptionForUser) (int, *TraitBusinessOptionForUser) {
		return e.Value, e
	})
}

func (s TraitBusinessOptionListForUser) Get(value int) *TraitBusinessOptionForUser {
	ret, found := lo.Find(s, func(e *TraitBusinessOptionForUser) bool {
		return e.Value == value
	})
	if found {
		return ret
	} else {
		return nil
	}
}

func (s TraitBusinessOptionListForUser) GetByBool(on bool) *TraitBusinessOptionForUser {
	v := func(on bool) int {
		if on {
			return 1
		}
		return 2
	}(on)
	return s.Get(v)
}
