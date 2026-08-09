package master

type AreaID int

type Area struct {
	ID        AreaID // ID
	Name      string // 地域名
	SortOrder int    // ソート順
}

func (a Area) GetID() AreaID {
	return a.ID
}

type (
	Areas   = list[AreaID, Area]
	AreaMap = Map[AreaID, Area]
)

func (a Area) TableName() string {
	return "master.area"
}
