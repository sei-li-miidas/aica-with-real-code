package support

import (
	pinterfaces "aica/api/api/mcptool/usecase/position/interfaces"
	pmodel "aica/api/api/mcptool/usecase/position/model"
	address "aica/api/api/mcptool/usecase/shared"

	"github.com/samber/lo"
)

// ResolveLocationIDs は検索条件に含まれる勤務地関連情報から、検索に使う city ID 一覧を解決する。
// まず居住地、通勤圏、勤務地、フルリモート指定を分類し、フルリモートなら勤務地制約なしとして nil を返す。
// それ以外は明示的な通勤圏指定を優先し、必要な場合だけ居住地から通勤圏を逆引きし、最後に勤務地由来の city ID を重複排除して返す。
func ResolveLocationIDs(lookup pinterfaces.LocationLookup, params *pmodel.GenericPositionSearchParams) ([]int, error) {
	if lookup == nil || params == nil {
		return nil, nil
	}

	// フルリモート指定が含まれているかを保持し、含まれる場合は勤務地 ID 解決自体をスキップする。
	isFullyRemoteWork := false
	// 居住地指定を保持し、明示的な通勤圏がない場合の通勤圏逆引きに利用する。
	var residence *address.LocationRequest
	// 勤務地または明示的な通勤圏として解決対象になる都道府県・市区町村の組を蓄積する。
	locationTargets := make([]struct{ PrefectureName, CityName string }, 0, len(params.Locations))
	// 通勤圏が明示指定されているかを表し、居住地からの自動補完を行うかどうかの判定に使う。
	hasExplicitCommutingAreas := false

	for _, location := range params.Locations {
		switch location.LocationType {
		case address.LOCATION_TYPE_RESIDENCE:
			residence = location
		case address.LOCATION_TYPE_COMMUTING_AREAS:
			hasExplicitCommutingAreas = true
			locationTargets = append(locationTargets, struct{ PrefectureName, CityName string }{
				PrefectureName: location.PrefectureName,
				CityName:       location.CityName,
			})
		case address.LOCATION_TYPE_FULL_REMOTE_WORK:
			isFullyRemoteWork = true
		case address.LOCATION_TYPE_WORK_LOCATION:
			locationTargets = append(locationTargets, struct{ PrefectureName, CityName string }{
				PrefectureName: location.PrefectureName,
				CityName:       location.CityName,
			})
		}
	}

	if isFullyRemoteWork {
		return nil, nil
	}

	// 通勤圏と勤務地から解決した city ID を集約し、最後に重複排除して返すための作業用スライス。
	cityIDs := make([]int, 0)
	if hasExplicitCommutingAreas {
		// 明示的な通勤圏指定がある場合は居住地からの逆引きを行わない。
	} else if residence != nil {
		commutingCityIDs, err := lookup.GetCommutingAreasFromResidence(residence.PrefectureName, residence.CityName)
		if err != nil {
			return nil, err
		}
		cityIDs = append(cityIDs, commutingCityIDs...)
	}

	if len(locationTargets) > 0 {
		workLocationCityIDs, err := lookup.GetCityIDsFromWorkLocations(locationTargets)
		if err != nil {
			return nil, err
		}
		cityIDs = append(cityIDs, workLocationCityIDs...)
	}

	return lo.Uniq(cityIDs), nil
}
