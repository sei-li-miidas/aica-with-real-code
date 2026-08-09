package location

import "aica/api/domain/public/master"

type commutingAreaSearcher interface {
	SearchCommutingAreas(originCityID int) ([]*master.PrefectureCity, error)
}
