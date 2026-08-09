package position

import (
	"cmp"
	"slices"

	mapset "github.com/deckarep/golang-set/v2"
	"github.com/samber/lo"

	"aica/api/domain/public/master"
	"aica/api/domain/user/profile/will/importance"
	"aica/api/sdk/vo"
)

// WorkAddress 勤務地
// 企業側項目: 勤務地(ptx_work_address)
type WorkAddress struct {
	Importance importance.Importance // オファー表示ロジック改定v2まではValueから判定した重要度 (不問 or 必須のみ)
	Value      WorkAddressValue
}

// NewWorkAddress .
func NewWorkAddress(i importance.Importance, v WorkAddressValue) *WorkAddress {
	if i.IsAnything() {
		// 「こだわりなし」設定の場合、値をクリア
		v = WorkAddressValue{
			OverseasFlg: false,
			Prefectures: nil,
			Cities:      nil,
		}
	}
	return &WorkAddress{
		Importance: i,
		Value:      v,
	}
}

// IsValidValue 有効な値か
func (w *WorkAddress) IsValidValue(cm master.CityMap) bool {
	// 市区町村がマスタに存在するか
	for _, cityID := range w.Value.Cities {
		if _, ok := cm[cityID]; !ok {
			return false
		}
	}

	// 都道府県・市区町村の県・海外合わせて最大5つまで
	others := 0
	if w.Value.OverseasFlg {
		others = 1
	}
	if len(w.GetAllPrefectures(cm))+others > 5 {
		return false
	}
	return true
}

// IsInputValue 値が入力されているか
func (w *WorkAddress) IsInputValue() bool {
	if w.Importance.IsAnything() {
		// 「こだわりなし」設定の場合、値が無視されるので空と判定する
		return false
	}
	if !w.Value.OverseasFlg && len(w.Value.Prefectures) == 0 && len(w.Value.Cities) == 0 {
		// Valueのフィールドがすべて未入力のとき空と判定する
		return false
	}
	return true
}

// IsExistValue 値が入力されているか
func (w WorkAddress) IsExistValue() bool {
	return w.Value.IsExistValue()
}

// IsExistValue .
func (v WorkAddressValue) IsExistValue() bool {
	return v.OverseasFlg || len(v.Prefectures) > 0 || len(v.Cities) > 0
}

// GetAllPrefectures 「都道府県」と「市区町村に紐付く都道府県」を返す
func (w *WorkAddress) GetAllPrefectures(cm master.CityMap) Prefectures {
	set := mapset.NewThreadUnsafeSet[master.PrefectureID](w.Value.Prefectures...)
	for _, v := range w.GetCities(cm) {
		set.Add(v.PrefectureID)
	}

	return set.ToSlice()
}

// GetCities .
func (w *WorkAddress) GetCities(cm master.CityMap) []City {
	c := make([]City, 0, len(w.Value.Cities))
	for _, cityID := range w.Value.Cities {
		if city, found := cm[cityID]; found {
			c = append(c, City{
				IDNamePair:   *vo.NewIDNamePair(cityID, string(city.Name)),
				PrefectureID: city.PrefectureID,
			})
		} else {
			c = append(c, City{
				IDNamePair:   *vo.NewIDNamePair(cityID, ""),
				PrefectureID: 0,
			})
		}
	}
	return c
}

// WorkAddressValue .
type WorkAddressValue struct {
	OverseasFlg bool        // 海外フラグ
	Prefectures Prefectures `validate:"slicemin=1,slicemax=47,max=5,unique"` // 都道府県
	Cities      Cities      // 市区町村(値検証はIsValidValueメソッドで行う)
}

// NewWorkAddressWithName .
func NewWorkAddressWithName(w *WorkAddress, pm master.PrefectureMap, cm master.CityMap) *WorkAddressWithName {
	p := make([]vo.IDNamePair[master.PrefectureID], 0, len(w.Value.Prefectures))
	for _, prefectureID := range w.Value.Prefectures {
		if pref, found := pm[prefectureID]; found {
			p = append(p, *vo.NewIDNamePair(prefectureID, pref.Name))
		} else {
			p = append(p, *vo.NewIDNamePair(prefectureID, ""))
		}
	}

	allPrefectures := w.GetAllPrefectures(cm)
	ap := make([]vo.IDNamePair[master.PrefectureID], 0, len(allPrefectures))
	for _, prefectureID := range allPrefectures {
		if pref, found := pm[prefectureID]; found {
			ap = append(ap, *vo.NewIDNamePair(prefectureID, pref.Name))
		} else {
			ap = append(ap, *vo.NewIDNamePair(prefectureID, ""))
		}
	}

	return &WorkAddressWithName{
		Importance: w.Importance,
		Value: WorkAddressValueWithName{
			OverseasFlg:    w.Value.OverseasFlg,
			AllPrefectures: ap,
			Prefectures:    p,
			Cities:         w.GetCities(cm),
		},
	}
}

// WorkAddressWithName 勤務地(名前付き)
type WorkAddressWithName struct {
	Importance importance.Importance
	Value      WorkAddressValueWithName
}

// WorkAddressValueWithName .
type WorkAddressValueWithName struct {
	OverseasFlg    bool                                // 海外フラグ
	AllPrefectures vo.IDNamePairs[master.PrefectureID] // 市区町村の都道府県も含む
	Prefectures    vo.IDNamePairs[master.PrefectureID] // 都道府県
	Cities         []City                              // 市区町村
}

// GetNamesForNotifyOffer オファー通知にて、オファーを並び替えするための希望勤務地を取得
func (w WorkAddressValueWithName) GetNamesForNotifyOffer() []string {
	names := w.Prefectures.Names()

	if len(w.Cities) > 0 {
		for _, city := range w.Cities {
			name := city.getPrefectureName(w.AllPrefectures) + " " + city.Name
			names = append(names, name)
		}
	}

	if w.OverseasFlg {
		names = append(names, "海外")
	}

	return names
}

// City 市区町村
type City struct {
	vo.IDNamePair[master.CityID]
	PrefectureID master.PrefectureID
}

func (city City) getPrefectureName(allPrefectures vo.IDNamePairs[master.PrefectureID]) string {
	var prefName string
	for _, pref := range allPrefectures {
		if pref.ID == city.PrefectureID {
			prefName = pref.Name
			break
		}
	}
	return prefName
}

type (
	Prefectures []master.PrefectureID
	Cities      []master.CityID
)

// ToSet .
func (p Prefectures) ToSet() mapset.Set[master.PrefectureID] {
	return mapset.NewThreadUnsafeSet[master.PrefectureID](p...)
}

// SortForJSON プロフィールJSON用にソートする
func (p Prefectures) SortForJSON(pm master.PrefectureMap) {
	so := func(p *master.Prefecture) int {
		if p != nil {
			return p.SortOrder
		}
		return 0
	}
	slices.SortFunc(p, func(a, b master.PrefectureID) int {
		ma := so(pm[a])
		mb := so(pm[b])

		// sort_orderの昇順
		return cmp.Compare(ma, mb)
	})
}

// ToSet .
func (c Cities) ToSet() mapset.Set[master.CityID] {
	return mapset.NewThreadUnsafeSet[master.CityID](c...)
}

// SortForJSON プロフィールJSON用にソートする
func (c Cities) SortForJSON(cm master.CityMap) {
	so := func(c *master.City) int {
		if c != nil {
			return c.SortOrder
		}
		return 0
	}
	slices.SortFunc(c, func(a, b master.CityID) int {
		ma := so(cm[a])
		mb := so(cm[b])

		// sort_orderの昇順
		return cmp.Compare(ma, mb)
	})
}

// PrefectureIDs 市区町村IDリストから都道府県IDリストを返す
func (c Cities) PrefectureIDs() []master.PrefectureID {
	PrefectureIDs := lo.Map(c, func(c master.CityID, _ int) master.PrefectureID {
		return c.PrefectureID()
	})
	return lo.Uniq(PrefectureIDs)
}
