package master

import (
	"github.com/samber/lo"

	"aica/api/sdk/slice"
)

type (
	SchoolID int

	// School 学校マスタ
	School struct {
		ID           SchoolID     // ID
		Name         string       // 学校名
		Kana         string       // 学校名かな
		SchoolTypeID SchoolTypeID // 学校種別ID
		SchoolRankID SchoolRankID // 学校ランクID
		SortOrder    int
	}

	Schools   []*School
	SchoolMap = Map[SchoolID, School]
)

// TableName .
func (s School) TableName() string {
	return "master.school"
}

func (s School) GetID() SchoolID {
	return s.ID
}

func (ss Schools) ToMap() SchoolMap {
	return lo.SliceToMap(ss, func(e *School) (SchoolID, *School) {
		v := *e
		return v.GetID(), e
	})
}

// GetByName 学校名の完全一致で取得
func (ss Schools) GetByName(name string) Schools {
	return slice.Filter(ss, func(_ int, e *School) bool {
		return e.Name == name
	})
}

// GetByType 学校種別で取得
func (ss Schools) GetByType(schoolTypeID SchoolTypeID) Schools {
	return slice.Filter(ss, func(_ int, e *School) bool {
		return e.SchoolTypeID == schoolTypeID
	})
}
