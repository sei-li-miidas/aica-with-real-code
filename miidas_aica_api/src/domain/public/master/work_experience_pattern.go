package master

const (
	workExperiencePatternIDNoSettings     WorkExperiencePatternID = 0 // 未設定
	workExperiencePatternIDNecessarily    WorkExperiencePatternID = 1 // 必ず実施
	workExperiencePatternIDApplicantsOnly WorkExperiencePatternID = 2 // 希望者のみ実施
	workExperiencePatternIDNotImplemented WorkExperiencePatternID = 3 // 実施しない
)

type (
	WorkExperiencePatternID int

	WorkExperiencePattern struct {
		ID        WorkExperiencePatternID
		Name      string
		SortOrder int
	}

	WorkExperiencePatterns   = list[WorkExperiencePatternID, WorkExperiencePattern]
	WorkExperiencePatternMap = Map[WorkExperiencePatternID, WorkExperiencePattern]
)

func (w WorkExperiencePattern) TableName() string {
	return "master.work_experience_pattern"
}

func (w WorkExperiencePattern) GetID() WorkExperiencePatternID {
	return w.ID
}

// IsImplementable リアル職場体験を実施可能か
func (w WorkExperiencePatternID) IsImplementable() bool {
	return w == workExperiencePatternIDNecessarily || w.IsApplicantsOnly()
}

// IsApplicantsOnly リアル職場体験が「希望者のみ実施」か否か
func (w WorkExperiencePatternID) IsApplicantsOnly() bool {
	return w == workExperiencePatternIDApplicantsOnly
}

// IsSetting リアル職場体験を設定済か
func (w WorkExperiencePatternID) IsSetting() bool {
	return w != workExperiencePatternIDNoSettings
}

// IsSettingNotImplement リアル職場体験を実施しないか
func (w WorkExperiencePatternID) IsSettingNotImplement() bool {
	return w == workExperiencePatternIDNotImplemented
}
