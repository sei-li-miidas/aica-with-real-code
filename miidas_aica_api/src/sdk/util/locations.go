package util

import "slices"

type (
	Tokyo23Ward struct {
		Name string
		Kana string
	}
	Tokyo23Wards []*Tokyo23Ward
)

var tokyo23Wards = []Tokyo23Ward{
	{Name: "千代田区", Kana: "ちよだく"},
	{Name: "中央区", Kana: "ちゅうおうく"},
	{Name: "港区", Kana: "みなとく"},
	{Name: "新宿区", Kana: "しんじゅくく"},
	{Name: "文京区", Kana: "ぶんきょうく"},
	{Name: "台東区", Kana: "たいとうく"},
	{Name: "墨田区", Kana: "すみだく"},
	{Name: "江東区", Kana: "こうとうく"},
	{Name: "品川区", Kana: "しながわく"},
	{Name: "目黒区", Kana: "めぐろく"},
	{Name: "大田区", Kana: "おおたく"},
	{Name: "世田谷区", Kana: "せたがやく"},
	{Name: "渋谷区", Kana: "しぶやく"},
	{Name: "中野区", Kana: "なかのく"},
	{Name: "杉並区", Kana: "すぎなみく"},
	{Name: "豊島区", Kana: "としまく"},
	{Name: "北区", Kana: "きたく"},
	{Name: "荒川区", Kana: "あらかわく"},
	{Name: "板橋区", Kana: "いたばしく"},
	{Name: "練馬区", Kana: "ねりまく"},
	{Name: "足立区", Kana: "あだちく"},
	{Name: "葛飾区", Kana: "かつしかく"},
	{Name: "江戸川区", Kana: "えどがわく"},
}

func GetTokyo23Wards() []Tokyo23Ward {
	return slices.Clone(tokyo23Wards)
}

// 東京23区のいずれかであれば、「東京23区」に変換する
// 例：「東京都新宿区」は「東京23区」に変換される
func MaybeReplaceTokyoWardName(prefectureName, cityName string) (string, string) {
	if prefectureName == "東京都" {
		for _, ward := range GetTokyo23Wards() {
			if ward.Name != cityName {
				continue
			}
			cityName = "23区"
			break
		}
	}
	return prefectureName, cityName
}

// 「市」「区」「町」「村」のいずれかを欠けているかどうかをチェックする
func IsMissingLocalSuffix(cityName string) bool {
	suffixes := []string{
		"市",
		"区",
		"町",
		"村",
	}
	// 例外
	exceptions := []string{
		"四日市", // 四日市市
		"野々市", // 野々市市
		"廿日市", // 廿日市市
		"余市",  // 余市町
		"上市",  // 上市町
		"下市",  // 下市町
		"十日町", // 十日町市
		"大町",  // 大町市
		"田村",  // 田村市
		"羽村",  // 羽村市
		"大村",  // 大村市
		"玉村",  // 玉村町
	}

	// 例外のいずれかと一致すれば欠けている
	if SliceContains(exceptions, cityName) {
		return true
	}

	// 最後の文字を取得する
	lastCharacter := GetLastCharacter(cityName)
	// 最後の文字を確認する
	return !SliceContains(suffixes, lastCharacter)
}
