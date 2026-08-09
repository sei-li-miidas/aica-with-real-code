package dto

type LocationRequest struct {
	PrefectureName string `json:"PrefectureName"`
	CityName       string `json:"CityName"`
}

type VerifyPrefectureCityRequest struct {
	Locations []LocationRequest `json:"Locations"`
}

type SearchByKeywordRequest struct {
	Keyword string `json:"Keyword"`
}
