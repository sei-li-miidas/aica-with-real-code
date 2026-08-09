package master

type (
	WorkExperienceContentTypeID int

	WorkExperienceContentType struct {
		ID        WorkExperienceContentTypeID
		Name      string
		SortOrder int
	}

	WorkExperienceContentTypes   = list[WorkExperienceContentTypeID, WorkExperienceContentType]
	WorkExperienceContentTypeMap = Map[WorkExperienceContentTypeID, WorkExperienceContentType]
)

func (w WorkExperienceContentType) TableName() string {
	return "master.work_experience_content_type"
}

func (w WorkExperienceContentType) GetID() WorkExperienceContentTypeID {
	return w.ID
}
