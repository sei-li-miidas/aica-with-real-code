package master

import (
	"slices"
	"strings"

	"aica/api/sdk/util"
	"aica/api/sdk/vo"

	"github.com/samber/lo"
)

type (
	CityID   int    // CityマスターのID
	CityName string // Cityマスターの名称

	City struct {
		ID            CityID
		Name          CityName
		Kana          string
		MajorCityType int
		PrefectureID  PrefectureID
		SortOrder     int
	}
	Cities  []*City
	CityMap = Map[CityID, City]

	PrefectureCity struct {
		PrefectureID   PrefectureID
		PrefectureName string
		CityID         CityID
		CityName       CityName
		CityKana       string
		RealCityName   CityName
		RealCityKana   string
		Name           string
		Kana           string
	}
	PrefectureCities []*PrefectureCity
)

const (
	CityCodeSapporoCity   CityID = 11002
	CityCodeSendaiCity    CityID = 41009
	CityCodeMaebashiCity  CityID = 102016
	CityCodeSaitamaCity   CityID = 111007
	CityCodeChibaCity     CityID = 121002
	CityCodeFunabashiCity CityID = 122041
	CityCodeHachioujiCity CityID = 132012
	CityCodeYokohamaCity  CityID = 141003
	CityCode23City        CityID = 139999
	CityCodeKoufuCity     CityID = 192015
	CityCodeNagoyaCity    CityID = 231002
	CityCodeOsakaCity     CityID = 271004
	CityCodeFukuokaCity   CityID = 401307
	CityCodeNahaCity      CityID = 472018

	Tokyo23 = "23区"
)

func (c CityID) PrefectureID() PrefectureID {
	// CityIDを10000で割ることで、都道府県IDを取得できる
	// CityIDが5桁の場合 e.g. 札幌市(11002) → 都道府県IDは1(北海道)
	// CityIDが6桁の場合 e.g. 川口市(112038) → 都道府県IDは11(埼玉県)
	return PrefectureID(int(c) / 10000)
}

func (City) TableName() string {
	return "master.city"
}

func (c City) IntIDNamePair() *vo.IntIDNamePair {
	return vo.NewIntIDNamePair(c.ID, string(c.Name))
}

func (c City) GetID() CityID {
	return c.ID
}

func (c City) GetName() CityName {
	return c.Name
}

func (c City) WorkAddressID() WorkAddressID { return WorkAddressID(int(c.ID) + constInJapan) }

func (cs Cities) ToMap() Map[CityID, City] {
	return lo.SliceToMap(cs, func(e *City) (CityID, *City) {
		return e.ID, e
	})
}

// GetByPrefectureIDs 都道府県コードに一致する市区町村を取得する
func (cs Cities) GetByPrefectureIDs(ids ...PrefectureID) Cities {
	return lo.Filter(cs, func(e *City, _ int) bool {
		return slices.Contains(ids, e.ID.PrefectureID())
	})
}

func (cs Cities) GetByIDs(ids ...CityID) Cities {
	return lo.Filter(cs, func(e *City, _ int) bool {
		return slices.Contains(ids, e.ID)
	})
}

func (pcs PrefectureCities) GetByIDs(ids ...CityID) PrefectureCities {
	return lo.Filter(pcs, func(pc *PrefectureCity, _ int) bool {
		return slices.Contains(ids, pc.CityID)
	})
}

func (pcs PrefectureCities) GetByName(prefectureName string, cityName string) PrefectureCities {
	prefCities := lo.Filter(pcs, func(prefectureCity *PrefectureCity, _ int) bool {
		if prefectureName == "" || strings.Contains(prefectureCity.PrefectureName, prefectureName) {
			return strings.Contains(string(prefectureCity.CityName), cityName) || strings.Contains(prefectureCity.CityKana, cityName) || strings.Contains(string(prefectureCity.RealCityName), cityName) || strings.Contains(prefectureCity.RealCityKana, cityName)
		}

		return false
	})

	// インプットに「市」「区」「町」「村」のいずれかが欠けている場合、
	// "市区町村"以外で完全一致しない市区町村名を除外する
	// 例：
	// ユーザーインプット = "広島"
	// A "東広島市" → "市"を削除して"広島"と比較 → "東広島 == 広島" → 除外
	// B "広島市" → "市"を削除して"広島"と比較 → "広島 == "広島" → OK
	if util.IsMissingLocalSuffix(cityName) {
		prefCities = lo.Filter(prefCities, func(prefCity *PrefectureCity, _ int) bool {
			shortCityName := util.GetCharsExceptLast(string(prefCity.CityName))
			shortRealCityName := util.GetCharsExceptLast(string(prefCity.RealCityName))
			return shortCityName == cityName || shortRealCityName == cityName
		})
	} else {
		// インプットに「市」「区」「町」「村」のいずれかが欠けていない場合、
		// インプットと完全一致しない市区町名は除外する
		// 例：
		// ユーザーインプット = "広島"
		// A "東広島市" → "東広島市 == 広島市" → 除外
		// B "広島市" → "広島市 == "広島市" → OK
		prefCities = lo.Filter(prefCities, func(prefCity *PrefectureCity, _ int) bool {
			return string(prefCity.CityName) == cityName || string(prefCity.RealCityName) == cityName
		})
	}

	return prefCities
}
