package master

import (
	"aica/api/sdk/vo"
)

type (
	SkillGroupID int

	SkillGroup struct {
		ID          SkillGroupID // ID
		Name        string       // 名前
		HasYearsFlg string       // 年数ありフラグ
		SortOrder   int          // ソート順
	}

	SkillGroups   = list[SkillGroupID, SkillGroup]
	SkillGroupMap = Map[SkillGroupID, SkillGroup]
)

func (s SkillGroup) TableName() string {
	return "master.skill_group"
}

func (s SkillGroup) IntIDNamePair() *vo.IntIDNamePair {
	return vo.NewIntIDNamePair(s.ID, s.Name)
}

func (s SkillGroup) GetID() SkillGroupID {
	return s.ID
}

type SkillGroupIdNamePair struct {
	vo.IntIDNamePair
	Skills []SkillIdNamePair
}

// TODO: この型は不要。vo.IdNamePairをそのまま使えばOK
type SkillIdNamePair struct {
	vo.IntIDNamePair
}
