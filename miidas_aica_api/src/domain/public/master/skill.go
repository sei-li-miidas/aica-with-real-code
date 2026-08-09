package master

type (
	SkillID int
	Skill   struct {
		ID           SkillID      // ID
		SkillGroupID SkillGroupID // スキルグループID
		Name         SkillName    // 名前（$で階層化されているので注意）
		SortOrder    int          // ソート順
	}

	Skills   = list[SkillID, Skill]
	SkillMap = Map[SkillID, Skill]
)

// TableName .
func (s Skill) TableName() string {
	return "master.skill"
}

// GetPureName $区切りで階層化されている、末端の名称を取得する。
func (s Skill) GetPureName() string {
	return s.Name.GetDisplayName()
}

func (s Skill) GetName() string {
	return string(s.Name)
}

func (s Skill) GetID() SkillID {
	return s.ID
}
