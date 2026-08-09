package master

type (
	WorkExperienceNeedtimeID int

	WorkExperienceNeedtime struct {
		ID        WorkExperienceNeedtimeID
		Name      string
		SortOrder int
	}

	WorkExperienceNeedtimes   = list[WorkExperienceNeedtimeID, WorkExperienceNeedtime]
	WorkExperienceNeedtimeMap = Map[WorkExperienceNeedtimeID, WorkExperienceNeedtime]
)

func (w WorkExperienceNeedtime) TableName() string {
	return "master.work_experience_needtime"
}

func (w WorkExperienceNeedtime) GetID() WorkExperienceNeedtimeID {
	return w.ID
}
