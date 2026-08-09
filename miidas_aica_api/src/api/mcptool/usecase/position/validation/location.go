package validation

import (
	address "aica/api/api/mcptool/usecase/shared"
	"aica/api/sdk/util"
	"errors"
	"fmt"
)

type PrefectureCityExistsFunc func(prefectureName, cityName string) bool

type LocationValidationOptions struct {
	AllowEmptyIfRemotePossible bool
	RemoteWork                 bool
}

func locationTypeLabel(locationType address.LocationType) string {
	switch locationType {
	case address.LOCATION_TYPE_COMMUTING_AREAS:
		return "通勤圏"
	default:
		return "希望勤務地"
	}
}

func ValidateLocationRequests(
	locations []*address.LocationRequest,
	existsPrefectureCity PrefectureCityExistsFunc,
	options LocationValidationOptions,
) error {
	if len(locations) == 0 {
		if options.AllowEmptyIfRemotePossible && options.RemoteWork {
			return nil
		}
		return errors.New("場所の指定は必須ですのでユーザーに居住地または希望勤務地またはフルリモート希望を聞いて下さい。")
	}

	isFullyRemoteWork := false
	for _, loc := range locations {
		if loc == nil {
			return errors.New("場所の指定に不正な要素が含まれているため、ユーザーに居住地または希望勤務地またはフルリモート希望を確認してください。")
		}
		switch loc.LocationType {
		case address.LOCATION_TYPE_FULL_REMOTE_WORK:
			isFullyRemoteWork = true
		case address.LOCATION_TYPE_RESIDENCE, address.LOCATION_TYPE_WORK_LOCATION, address.LOCATION_TYPE_COMMUTING_AREAS:
		default:
			return errors.New("場所の種別はenumの「居住地」「希望勤務地」「通勤圏」「フルリモート」のいずれかを指定してください。")
		}
	}

	// フルリモート可能時は居住地/希望勤務地の詳細入力を不要にする。
	if isFullyRemoteWork {
		return nil
	}

	for _, loc := range locations {
		if loc == nil {
			return errors.New("場所の指定に不正な要素が含まれているため、ユーザーに居住地または希望勤務地またはフルリモート希望を確認してください。")
		}
		switch loc.LocationType {
		case address.LOCATION_TYPE_RESIDENCE:
			if len(loc.PrefectureName) == 0 || len(loc.CityName) == 0 {
				return errors.New("居住地の都道府県名と市区町村名の両方必要なので、ユーザーに聞いて下さい。")
			}
			if existsPrefectureCity == nil || !existsPrefectureCity(loc.PrefectureName, loc.CityName) {
				return errors.New("居住地の市区町村が見つかりませんでしたので、ユーザーに正しい市区町村名を聞いてください。")
			}
		case address.LOCATION_TYPE_WORK_LOCATION, address.LOCATION_TYPE_COMMUTING_AREAS:
			locationLabel := locationTypeLabel(loc.LocationType)
			if len(loc.PrefectureName) == 0 && len(loc.CityName) == 0 {
				return fmt.Errorf("%sの都道府県名と市区町村名の両方必要なので、ユーザーに聞いて下さい。", locationLabel)
			}
			if len(loc.PrefectureName) > 0 && len(loc.CityName) == 0 {
				return fmt.Errorf("%sの%sの市区町村名が必要なので、ユーザーに聞いてください。", locationLabel, loc.PrefectureName)
			}
			if len(loc.PrefectureName) == 0 && len(loc.CityName) > 0 {
				return fmt.Errorf("%sの%sの都道府県名が必要なので、ユーザーに聞いてください。", locationLabel, loc.CityName)
			}
			if existsPrefectureCity == nil || !existsPrefectureCity(loc.PrefectureName, loc.CityName) {
				return fmt.Errorf("%sの市区町村が見つかりませんでしたので、ユーザーに正しい市区町村名を聞いてください。", locationLabel)
			}
		}
	}

	return nil
}

func NormalizePrefectureCity(prefectureName, cityName string) (string, string) {
	prefectureName, cityName = util.MaybeReplaceTokyoWardName(prefectureName, cityName)
	return prefectureName, cityName
}
