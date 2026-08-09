package master

type (
	WorkExperienceTimeframeID int

	WorkExperienceTimeframe struct {
		ID        WorkExperienceTimeframeID
		Name      string
		SortOrder int
	}

	WorkExperienceTimeframes   = list[WorkExperienceTimeframeID, WorkExperienceTimeframe]
	WorkExperienceTimeframeMap = Map[WorkExperienceTimeframeID, WorkExperienceTimeframe]
)

func (w WorkExperienceTimeframe) TableName() string {
	return "master.work_experience_timeframe"
}

func (w WorkExperienceTimeframe) GetID() WorkExperienceTimeframeID {
	return w.ID
}
