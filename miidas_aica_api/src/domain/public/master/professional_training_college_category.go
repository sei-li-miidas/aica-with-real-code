package master

import (
	"aica/api/sdk/vo"
)

type (
	ProfessionalTrainingCollegeCategoryID int

	// ProfessionalTrainingCollegeCategory 専門学校区分
	ProfessionalTrainingCollegeCategory struct {
		ID        ProfessionalTrainingCollegeCategoryID // ID
		Name      string                                // 名前
		SortOrder int
	}

	ProfessionalTrainingCollegeCategories = list[ProfessionalTrainingCollegeCategoryID, ProfessionalTrainingCollegeCategory]

	ProfessionalTrainingCollegeCategoryMap = Map[ProfessionalTrainingCollegeCategoryID, ProfessionalTrainingCollegeCategory]
)

const (
	ProfessionalTrainingCollegeCategoryIDOther ProfessionalTrainingCollegeCategoryID = 26 // その他
)

func (ptcc ProfessionalTrainingCollegeCategory) TableName() string {
	return "master.professional_training_college_category"
}

func (ptcc ProfessionalTrainingCollegeCategory) IDNamePair() *vo.IDNamePair[ProfessionalTrainingCollegeCategoryID] {
	if ptcc.ID == 0 {
		return nil
	}
	return vo.NewIDNamePair(ptcc.ID, ptcc.Name)
}

func (ptcc ProfessionalTrainingCollegeCategory) GetID() ProfessionalTrainingCollegeCategoryID {
	return ptcc.ID
}
