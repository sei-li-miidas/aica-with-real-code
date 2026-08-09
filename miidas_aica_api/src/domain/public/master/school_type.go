package master

import "aica/api/sdk/vo"

//go:generate go run $GOPATH/src/miidas/domain/connect/enum/decorator/enumDecorator.go -type=SchoolTypeID -output=school_type_string.go
type (
	SchoolTypeID int

	// SchoolType 学校区分
	SchoolType struct {
		ID        SchoolTypeID // ID
		Name      string       // 名前
		SortOrder int
	}

	SchoolTypes   = list[SchoolTypeID, SchoolType]
	SchoolTypeMap = Map[SchoolTypeID, SchoolType]
)

func (st SchoolType) TableName() string {
	return "master.school_type"
}

func (st SchoolType) IDNamePair() *vo.IDNamePair[SchoolTypeID] {
	return vo.NewIDNamePair(st.ID, st.Name)
}

func (st SchoolType) GetID() SchoolTypeID {
	return st.ID
}

const (
	SchoolTypeIDPostGraduate     SchoolTypeID = 1 // 大学院
	SchoolTypeIDCollege          SchoolTypeID = 2 // 大学
	SchoolTypeIDJuniorCollege    SchoolTypeID = 3 // 短期大学
	SchoolTypeIDVocationalSchool SchoolTypeID = 4 // 専門学校
	SchoolTypeIDTechnicalCollege SchoolTypeID = 5 // 高等専門学校
	SchoolTypeIDHighSchool       SchoolTypeID = 6 // 高等学校
	SchoolTypeIDJuniorHighSchool SchoolTypeID = 7 // 中学校
)

// NeedSchoolName 学校名の入力が必要かどうかを返す
func (id SchoolTypeID) NeedSchoolName() bool {
	// 大学院、大学、短大、高等専門学校の場合は入力必要
	return id == SchoolTypeIDPostGraduate ||
		id == SchoolTypeIDCollege ||
		id == SchoolTypeIDJuniorCollege ||
		id == SchoolTypeIDTechnicalCollege
}

// IsCollege 大学か
func (id SchoolTypeID) IsCollege() bool {
	return id == SchoolTypeIDCollege
}

// IsCollegeAbove 大学以上（大学or大学院）か
func (id SchoolTypeID) IsCollegeAbove() bool {
	return id == SchoolTypeIDPostGraduate || id == SchoolTypeIDCollege
}

func (id SchoolTypeID) BaseGraduationAge() int {
	switch id {
	case SchoolTypeIDPostGraduate: // 大学院
		return 24
	case SchoolTypeIDCollege: // 大学
		return 22
	case SchoolTypeIDJuniorCollege: // 短期大学
		return 20
	case SchoolTypeIDVocationalSchool: // 専門学校
		return 20
	case SchoolTypeIDTechnicalCollege: // 高等専門学校
		return 20
	case SchoolTypeIDHighSchool: // 高等学校
		return 18
	case SchoolTypeIDJuniorHighSchool: // 中学校
		return 15
	default:
		return 0
	}
}

// NeedDepartmentType 学部・学科の指定が必要かどうかを返す
func (id SchoolTypeID) NeedDepartmentType() bool {
	// 大学院、大学、短大、高等専門学校の場合は入力必要
	return id == SchoolTypeIDPostGraduate ||
		id == SchoolTypeIDCollege ||
		id == SchoolTypeIDJuniorCollege ||
		id == SchoolTypeIDTechnicalCollege
}

// NeedProfessionalTrainingCollegeCategory 専門学校区分の指定が必要かどうかを返す
func (id SchoolTypeID) NeedProfessionalTrainingCollegeCategory() bool {
	return id == SchoolTypeIDVocationalSchool
}
