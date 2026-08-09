package master

import (
	"strings"
	"sync"

	mapset "github.com/deckarep/golang-set/v2"
	"github.com/samber/lo"

	"aica/api/sdk/vo"
)

type (
	PrefectureID int

	// Prefecture 都道府県
	Prefecture struct {
		ID        PrefectureID // ID
		AreaID    AreaID       // 地域ID
		Name      string       // 都道府県名
		SortOrder int
	}

	Prefectures   list[PrefectureID, Prefecture]
	PrefectureMap Map[PrefectureID, Prefecture]
)

func (p Prefecture) TableName() string {
	return "master.prefecture"
}

func (p Prefecture) IntIDNamePair() *vo.IntIDNamePair {
	return vo.NewIntIDNamePair(p.ID, p.Name)
}

func (p Prefecture) GetID() PrefectureID {
	return p.ID
}

func (ps Prefectures) ToMap() PrefectureMap {
	return PrefectureMap(list[PrefectureID, Prefecture](ps).ToMap())
}

func (pm PrefectureMap) Get(id PrefectureID) (*Prefecture, bool) {
	return Map[PrefectureID, Prefecture](pm).Get(id)
}

// GetByName 都道府県名に部分一致する都道府県を取得する
func (ps Prefectures) GetByName(name string) Prefectures {
	return lo.Filter(ps, func(e *Prefecture, _ int) bool {
		return strings.Contains(e.Name, name)
	})
}

// GetName 都道府県名を取得する
func (p Prefecture) GetName() string {
	return p.Name
}

// GetNameExcludingCapitals 県や府、都を除いた都道府県名を取得する
func (p Prefecture) GetNameExcludingCapital() string {
	// 北海道はそのまま
	if p.GetID() == PrefectureIDHokkaido {
		return p.GetName()
	}
	// 北海道以外は最後の一文字を削る
	rs := []rune(p.GetName())
	return string(rs[:len(rs)-1])
}

// 都道府県の定数
const (
	PrefectureIDHokkaido  PrefectureID = 1  // 北海道
	PrefectureIDAomori    PrefectureID = 2  // 青森
	PrefectureIDIwate     PrefectureID = 3  // 岩手
	PrefectureIDMiyagi    PrefectureID = 4  // 宮城
	PrefectureIDAkita     PrefectureID = 5  // 秋田
	PrefectureIDYamagata  PrefectureID = 6  // 山形
	PrefectureIDFukushima PrefectureID = 7  // 福島
	PrefectureIDIbaraki   PrefectureID = 8  // 茨城
	PrefectureIDTochigi   PrefectureID = 9  // 栃木
	PrefectureIDGunma     PrefectureID = 10 // 群馬
	PrefectureIDSaitama   PrefectureID = 11 // 埼玉
	PrefectureIDChiba     PrefectureID = 12 // 千葉
	PrefectureIDTokyo     PrefectureID = 13 // 東京
	PrefectureIDKanagawa  PrefectureID = 14 // 神奈川
	PrefectureIDNiigata   PrefectureID = 15 // 新潟
	PrefectureIDToyama    PrefectureID = 16 // 富山
	PrefectureIDIshikawa  PrefectureID = 17 // 石川
	PrefectureIDFukui     PrefectureID = 18 // 福井
	PrefectureIDYamanashi PrefectureID = 19 // 山梨
	PrefectureIDNagano    PrefectureID = 20 // 長野
	PrefectureIDGifu      PrefectureID = 21 // 岐阜
	PrefectureIDShizuoka  PrefectureID = 22 // 静岡
	PrefectureIDAichi     PrefectureID = 23 // 愛知
	PrefectureIDMie       PrefectureID = 24 // 三重
	PrefectureIDShiga     PrefectureID = 25 // 滋賀
	PrefectureIDKyoto     PrefectureID = 26 // 京都
	PrefectureIDOsaka     PrefectureID = 27 // 大阪
	PrefectureIDHyogo     PrefectureID = 28 // 兵庫
	PrefectureIDNara      PrefectureID = 29 // 奈良
	PrefectureIDWakayama  PrefectureID = 30 // 和歌山
	PrefectureIDTottori   PrefectureID = 31 // 鳥取
	PrefectureIDShimane   PrefectureID = 32 // 島根
	PrefectureIDOkayama   PrefectureID = 33 // 岡山
	PrefectureIDHiroshima PrefectureID = 34 // 広島
	PrefectureIDYamaguchi PrefectureID = 35 // 山口
	PrefectureIDTokushima PrefectureID = 36 // 徳島
	PrefectureIDKagawa    PrefectureID = 37 // 香川
	PrefectureIDEhime     PrefectureID = 38 // 愛媛
	PrefectureIDKochi     PrefectureID = 39 // 高知
	PrefectureIDFukuoka   PrefectureID = 40 // 福岡
	PrefectureIDSaga      PrefectureID = 41 // 佐賀
	PrefectureIDNagasaki  PrefectureID = 42 // 長崎
	PrefectureIDKumamoto  PrefectureID = 43 // 熊本
	PrefectureIDOita      PrefectureID = 44 // 大分
	PrefectureIDMiyazaki  PrefectureID = 45 // 宮崎
	PrefectureIDKagoshima PrefectureID = 46 // 鹿児島
	PrefectureIDOkinawa   PrefectureID = 47 // 沖縄

	PrefectureNameTokyo string = "東京都"
)

var nearlyPrefMap = map[PrefectureID][]PrefectureID{
	PrefectureIDHokkaido:  {PrefectureIDAomori},                                                                                                                                                // 北海道：青森県
	PrefectureIDAomori:    {PrefectureIDHokkaido, PrefectureIDIwate, PrefectureIDAkita},                                                                                                        // 青森県：北海道、岩手県、秋田県
	PrefectureIDIwate:     {PrefectureIDAomori, PrefectureIDMiyagi, PrefectureIDAkita},                                                                                                         // 岩手県：青森県、宮城県、秋田県
	PrefectureIDMiyagi:    {PrefectureIDIwate, PrefectureIDAkita, PrefectureIDYamagata, PrefectureIDFukushima},                                                                                 // 宮城県：岩手県、秋田県、山形県、福島県
	PrefectureIDAkita:     {PrefectureIDAomori, PrefectureIDIwate, PrefectureIDMiyagi, PrefectureIDYamagata},                                                                                   // 秋田県：青森県、岩手県、宮城県、山形県
	PrefectureIDYamagata:  {PrefectureIDMiyagi, PrefectureIDAkita, PrefectureIDFukushima, PrefectureIDNiigata},                                                                                 // 山形県：宮城県、秋田県、福島県、新潟県
	PrefectureIDFukushima: {PrefectureIDMiyagi, PrefectureIDYamagata, PrefectureIDIbaraki, PrefectureIDTochigi, PrefectureIDGunma, PrefectureIDNiigata},                                        // 福島県：宮城県、山形県、茨城県、栃木県、群馬県、新潟県
	PrefectureIDIbaraki:   {PrefectureIDFukushima, PrefectureIDTochigi, PrefectureIDSaitama, PrefectureIDChiba},                                                                                // 茨城県：福島県、栃木県、埼玉県、千葉県
	PrefectureIDTochigi:   {PrefectureIDFukushima, PrefectureIDIbaraki, PrefectureIDGunma, PrefectureIDSaitama},                                                                                // 栃木県：福島県、茨城県、群馬県、埼玉県
	PrefectureIDGunma:     {PrefectureIDFukushima, PrefectureIDTochigi, PrefectureIDSaitama, PrefectureIDNiigata, PrefectureIDNagano},                                                          // 群馬県：福島県、栃木県、埼玉県、新潟県、長野県
	PrefectureIDSaitama:   {PrefectureIDIbaraki, PrefectureIDTochigi, PrefectureIDGunma, PrefectureIDChiba, PrefectureIDTokyo, PrefectureIDYamanashi, PrefectureIDNagano},                      // 埼玉県：茨城県、栃木県、群馬県、千葉県、東京都、山梨県、長野県
	PrefectureIDChiba:     {PrefectureIDIbaraki, PrefectureIDSaitama, PrefectureIDTokyo, PrefectureIDKanagawa},                                                                                 // 千葉県：茨城県、埼玉県、東京都、神奈川県
	PrefectureIDTokyo:     {PrefectureIDSaitama, PrefectureIDChiba, PrefectureIDKanagawa, PrefectureIDYamanashi},                                                                               // 東京都：埼玉県、千葉県、神奈川県、山梨県
	PrefectureIDKanagawa:  {PrefectureIDChiba, PrefectureIDTokyo, PrefectureIDYamanashi, PrefectureIDShizuoka},                                                                                 // 神奈川県：千葉県、東京都、山梨県、静岡県
	PrefectureIDNiigata:   {PrefectureIDYamagata, PrefectureIDFukushima, PrefectureIDGunma, PrefectureIDToyama, PrefectureIDNagano},                                                            // 新潟県：山形県、福島県、群馬県、富山県、長野県
	PrefectureIDToyama:    {PrefectureIDNiigata, PrefectureIDIshikawa, PrefectureIDNagano, PrefectureIDGifu},                                                                                   // 富山県：新潟県、石川県、長野県、岐阜県
	PrefectureIDIshikawa:  {PrefectureIDToyama, PrefectureIDFukui, PrefectureIDGifu},                                                                                                           // 石川県：富山県、福井県、岐阜県
	PrefectureIDFukui:     {PrefectureIDIshikawa, PrefectureIDGifu, PrefectureIDShiga, PrefectureIDKyoto},                                                                                      // 福井県：石川県、岐阜県、滋賀県、京都府
	PrefectureIDYamanashi: {PrefectureIDSaitama, PrefectureIDTokyo, PrefectureIDKanagawa, PrefectureIDNagano, PrefectureIDShizuoka},                                                            // 山梨県：埼玉県、東京都、神奈川県、長野県、静岡県
	PrefectureIDNagano:    {PrefectureIDGunma, PrefectureIDSaitama, PrefectureIDNiigata, PrefectureIDToyama, PrefectureIDYamanashi, PrefectureIDGifu, PrefectureIDShizuoka, PrefectureIDAichi}, // 長野県：群馬県、埼玉県、新潟県、富山県、山梨県、岐阜県、静岡県、愛知県
	PrefectureIDGifu:      {PrefectureIDToyama, PrefectureIDIshikawa, PrefectureIDFukui, PrefectureIDNagano, PrefectureIDAichi, PrefectureIDMie, PrefectureIDShiga},                            // 岐阜県：富山県、石川県、福井県、長野県、愛知県、三重県、滋賀県
	PrefectureIDShizuoka:  {PrefectureIDKanagawa, PrefectureIDYamanashi, PrefectureIDNagano, PrefectureIDAichi},                                                                                // 静岡県：神奈川県、山梨県、長野県、愛知県
	PrefectureIDAichi:     {PrefectureIDNagano, PrefectureIDGifu, PrefectureIDShizuoka, PrefectureIDMie},                                                                                       // 愛知県：長野県、岐阜県、静岡県、三重県
	PrefectureIDMie:       {PrefectureIDGifu, PrefectureIDAichi, PrefectureIDShiga, PrefectureIDKyoto, PrefectureIDNara, PrefectureIDWakayama},                                                 // 三重県：岐阜県、愛知県、滋賀県、京都府、奈良県、和歌山県
	PrefectureIDShiga:     {PrefectureIDFukui, PrefectureIDGifu, PrefectureIDMie, PrefectureIDKyoto},                                                                                           // 滋賀県：福井県、岐阜県、三重県、京都府
	PrefectureIDKyoto:     {PrefectureIDFukui, PrefectureIDMie, PrefectureIDShiga, PrefectureIDOsaka, PrefectureIDHyogo, PrefectureIDNara},                                                     // 京都府：福井県、三重県、滋賀県、大阪府、兵庫県、奈良県
	PrefectureIDOsaka:     {PrefectureIDKyoto, PrefectureIDHyogo, PrefectureIDNara, PrefectureIDWakayama},                                                                                      // 大阪府：京都府、兵庫県、奈良県、和歌山県
	PrefectureIDHyogo:     {PrefectureIDKyoto, PrefectureIDOsaka, PrefectureIDTottori, PrefectureIDOkayama, PrefectureIDTokushima},                                                             // 兵庫県：京都府、大阪府、鳥取県、岡山県、徳島県
	PrefectureIDNara:      {PrefectureIDMie, PrefectureIDKyoto, PrefectureIDOsaka, PrefectureIDWakayama},                                                                                       // 奈良県：三重県、京都府、大阪府、和歌山県
	PrefectureIDWakayama:  {PrefectureIDMie, PrefectureIDOsaka, PrefectureIDNara},                                                                                                              // 和歌山県：三重県、大阪府、奈良県
	PrefectureIDTottori:   {PrefectureIDHyogo, PrefectureIDShimane, PrefectureIDOkayama, PrefectureIDHiroshima},                                                                                // 鳥取県：兵庫県、島根県、岡山県、広島県
	PrefectureIDShimane:   {PrefectureIDTottori, PrefectureIDHiroshima, PrefectureIDYamaguchi},                                                                                                 // 島根県：鳥取県、広島県、山口県
	PrefectureIDOkayama:   {PrefectureIDHyogo, PrefectureIDShimane, PrefectureIDHiroshima, PrefectureIDKagawa},                                                                                 // 岡山県：兵庫県、島根県、広島県、香川県
	PrefectureIDHiroshima: {PrefectureIDTottori, PrefectureIDShimane, PrefectureIDOkayama, PrefectureIDYamaguchi, PrefectureIDEhime},                                                           // 広島県：鳥取県、島根県、岡山県、山口県、愛媛県
	PrefectureIDYamaguchi: {PrefectureIDShimane, PrefectureIDHiroshima, PrefectureIDFukuoka},                                                                                                   // 山口県：島根県、広島県、福岡県
	PrefectureIDTokushima: {PrefectureIDHyogo, PrefectureIDKagawa, PrefectureIDEhime, PrefectureIDKochi},                                                                                       // 徳島県：兵庫県、香川県、愛媛県、高知県
	PrefectureIDKagawa:    {PrefectureIDOkayama, PrefectureIDTokushima, PrefectureIDEhime},                                                                                                     // 香川県：岡山県、徳島県、愛媛県
	PrefectureIDEhime:     {PrefectureIDHiroshima, PrefectureIDTokushima, PrefectureIDKagawa, PrefectureIDKochi},                                                                               // 愛媛県：広島県、徳島県、香川県、高知県
	PrefectureIDKochi:     {PrefectureIDTokushima, PrefectureIDEhime},                                                                                                                          // 高知県：徳島県、愛媛県
	PrefectureIDFukuoka:   {PrefectureIDYamaguchi, PrefectureIDSaga, PrefectureIDKumamoto, PrefectureIDOita},                                                                                   // 福岡県：山口県、佐賀県、熊本県、大分県
	PrefectureIDSaga:      {PrefectureIDFukuoka, PrefectureIDNagasaki},                                                                                                                         // 佐賀県：福岡県、長崎県
	PrefectureIDNagasaki:  {PrefectureIDSaga},                                                                                                                                                  // 長崎県：佐賀県
	PrefectureIDKumamoto:  {PrefectureIDFukuoka, PrefectureIDOita, PrefectureIDMiyazaki, PrefectureIDKagoshima},                                                                                // 熊本県：福岡県、大分県、宮崎県、鹿児島県
	PrefectureIDOita:      {PrefectureIDFukuoka, PrefectureIDKumamoto, PrefectureIDMiyazaki},                                                                                                   // 大分県 ：福岡県、熊本県、宮崎県
	PrefectureIDMiyazaki:  {PrefectureIDKumamoto, PrefectureIDOita, PrefectureIDKagoshima},                                                                                                     // 宮崎県：熊本県、大分県、鹿児島県
	PrefectureIDKagoshima: {PrefectureIDKumamoto, PrefectureIDMiyazaki},                                                                                                                        // 鹿児島県：熊本県、宮崎県
	PrefectureIDOkinawa:   {},                                                                                                                                                                  // 沖縄県：なし
}

// 近隣都道府県データを元に mapset 化してキャッシュ
var nearlyPrefSetMap = sync.OnceValue(func() map[PrefectureID]mapset.Set[PrefectureID] {
	sets := make(map[PrefectureID]mapset.Set[PrefectureID], len(nearlyPrefMap))

	for pref, nearlyPrefs := range nearlyPrefMap {
		sets[pref] = mapset.NewThreadUnsafeSet(pref)
		sets[pref].Append(nearlyPrefs...)
	}
	return sets
})

// NearbyPrefIDSet 近隣都府県IDを取得する
// @see 希望条件の「極力」ロジックと同じ
// https://gitlab.miidas.jp/miidas/miidas_go/-/blob/1a5a90717130fdae04b1ebf30d9af51982cbd6c2/domain/user/offer/evaluation/checkers.go#L46-66
func (p PrefectureID) NearbyPrefIDSet() mapset.Set[PrefectureID] {
	return nearlyPrefSetMap()[p]
}

// NearbyPrefsAndCityIDs 近隣都府県/市区町村IDを取得する
func (p PrefectureID) NearbyPrefsAndCityIDs() ([]PrefectureID, CityID) {
	switch {
	case p.IsCapitalArea():
		return lo.Filter(capitalAreaPrefects().ToSlice(), func(prefID PrefectureID, _ int) bool { return prefID != p }), 0
	case p.IsKeihanshinPrefects():
		return lo.Filter(keihanshinPrefects().ToSlice(), func(prefID PrefectureID, _ int) bool { return prefID != p }), 0
	case p.IsTohokuPrefects():
		if p == PrefectureIDMiyagi { // 宮城県の場合は「仙台市」は返さない
			return nil, 0
		}
		return nil, CityCodeSendaiCity
	case p.IsKyushuPrefects():
		if p == PrefectureIDFukuoka { // 福岡県の場合は「福岡市」は返さない
			return nil, 0
		}
		return nil, CityCodeFukuokaCity
	}
	return nil, 0
}

// IsCapitalArea 首都圏かどうかを返す
func (p PrefectureID) IsCapitalArea() bool {
	return capitalAreaPrefects().ContainsOne(p)
}

// IsKeihanshinPrefects 京阪神かどうかを返す
func (p PrefectureID) IsKeihanshinPrefects() bool {
	return keihanshinPrefects().ContainsOne(p)
}

// IsKyushuPrefects 九州かどうかを返す
func (p PrefectureID) IsKyushuPrefects() bool {
	return kyushuPrefects().ContainsOne(p)
}

// IsTohokuPrefects 東北かどうかを返す
func (p PrefectureID) IsTohokuPrefects() bool {
	return tohokuPrefects().ContainsOne(p)
}

// IsMiidasTELAppealTargetPrefectures ミイダスTEL訴求対象の都道府県かどうかを返す
func (p PrefectureID) IsMiidasTELAppealTargetPrefectures() bool {
	return !MiidasTELAppealNoTargetPrefectures().ContainsOne(p)
}

// IsValid 都道府県コードの妥当性チェック
func (p PrefectureID) IsValid() bool {
	return PrefectureIDHokkaido <= p && p <= PrefectureIDOkinawa
}

var tohokuPrefects = sync.OnceValue(func() mapset.Set[PrefectureID] {
	return mapset.NewThreadUnsafeSet(
		PrefectureIDAomori,
		PrefectureIDIwate,
		PrefectureIDMiyagi,
		PrefectureIDAkita,
		PrefectureIDYamagata,
		PrefectureIDFukushima,
	)
})

var capitalAreaPrefects = sync.OnceValue(func() mapset.Set[PrefectureID] {
	return mapset.NewThreadUnsafeSet(
		PrefectureIDSaitama,
		PrefectureIDChiba,
		PrefectureIDTokyo,
		PrefectureIDKanagawa,
	)
})

var keihanshinPrefects = sync.OnceValue(func() mapset.Set[PrefectureID] {
	return mapset.NewThreadUnsafeSet(
		PrefectureIDKyoto,
		PrefectureIDOsaka,
		PrefectureIDHyogo,
	)
})

var kyushuPrefects = sync.OnceValue(func() mapset.Set[PrefectureID] {
	return mapset.NewThreadUnsafeSet(
		PrefectureIDFukuoka,
		PrefectureIDSaga,
		PrefectureIDNagasaki,
		PrefectureIDKumamoto,
		PrefectureIDOita,
		PrefectureIDMiyazaki,
		PrefectureIDKagoshima,
	)
})

// MiidasTELAppealNoTargetPrefectures ミイダスTEL訴求対象外の都道府県
var MiidasTELAppealNoTargetPrefectures = sync.OnceValue(func() mapset.Set[PrefectureID] {
	return mapset.NewThreadUnsafeSet(
		PrefectureIDHokkaido,
		PrefectureIDSaitama,
		PrefectureIDChiba,
		PrefectureIDTokyo,
		PrefectureIDKanagawa,
		PrefectureIDAichi,
		PrefectureIDKyoto,
		PrefectureIDOsaka,
		PrefectureIDHyogo,
		PrefectureIDFukuoka,
	)
})
