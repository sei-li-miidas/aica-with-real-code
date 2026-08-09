package master

type (
	WorkExperienceTimingID int

	WorkExperienceTiming struct {
		ID        WorkExperienceTimingID
		Name      string
		SortOrder int
	}

	WorkExperienceTimings   = list[WorkExperienceTimingID, WorkExperienceTiming]
	WorkExperienceTimingMap = Map[WorkExperienceTimingID, WorkExperienceTiming]
)

func (w WorkExperienceTiming) TableName() string {
	return "master.work_experience_timing"
}

func (w WorkExperienceTiming) GetID() WorkExperienceTimingID {
	return w.ID
}
