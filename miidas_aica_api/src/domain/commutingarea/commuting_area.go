package commutingarea

import (
	"time"
)

type CommutingArea struct {
	CommutingAreaId           int
	OriginId                  int
	OriginPrefectureId        int
	OriginPrefectureName      string
	OriginName                string
	Rank                      int
	DestinationId             int
	DestinationPrefectureId   int
	DestinationPrefectureName string
	DestinationName           string
	CreatedAt                 time.Time
	UpdatedAt                 *time.Time
	DeletedAt                 *time.Time
}

func (CommutingArea) TableName() string {
	return "commuting_areas"
}
