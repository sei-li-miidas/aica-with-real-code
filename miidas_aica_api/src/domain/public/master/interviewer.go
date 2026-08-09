package master

type (
	InterviewerID int
	Interviewer   struct {
		ID        InterviewerID // ID
		Name      string        // 面接官名称
		SortOrder int
	}
	Interviewers = list[InterviewerID, Interviewer]
)

func (i Interviewer) GetID() InterviewerID {
	return i.ID
}

func (Interviewer) TableName() string {
	return "master.interviewer"
}
