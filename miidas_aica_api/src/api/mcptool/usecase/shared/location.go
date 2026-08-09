package shared

type (
	// 場所の種別
	LocationType string

	// 場所のリクエスト
	LocationRequest struct {
		LocationType   LocationType
		PrefectureName string
		CityName       string
	}
)

const (
	LOCATION_TYPE_RESIDENCE        LocationType = "居住地"
	LOCATION_TYPE_COMMUTING_AREAS  LocationType = "通勤圏"
	LOCATION_TYPE_WORK_LOCATION    LocationType = "希望勤務地"
	LOCATION_TYPE_FULL_REMOTE_WORK LocationType = "フルリモート"
)
