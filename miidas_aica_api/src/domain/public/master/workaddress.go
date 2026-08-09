package master

import (
	"bytes"
	"database/sql/driver"
	"encoding/json"
	"errors"

	"aica/api/sdk/gormio/serializer"
)

// WorkAddressID 勤務地ID。都道府県、市区町村、海外を包括した体系のIDです。
//
//   - 7桁の固定長
//   - 先頭1桁目：1なら国内、9なら海外。海外の場合、以下の6桁は000000になります。
//   - 2,3桁目：都道府県D。勤務地が都道府県の場合、以下4桁は0000になります。
//   - 2-7桁目：市区町村コード
//
// 都道府県と市区町村の桁がかぶっていますが、master.prefecture.id、master.city.idの体系そのままになっているからです。
// 矛盾した値が指定された場合、市区町村が優先されます。
type WorkAddressID int

const (
	constInJapan        int           = 1000000 // 国内判定用
	constPrefecture     int           = 10000   // 都道府県ID算出用
	workAddressOverseas WorkAddressID = 9000000 // 海外

	OverseasLabel string = "海外" // 海外(value=9000000)のラベル
)

// NewWorkAddressID masterのコード値からの勤務地Valueの新規作成
// 海外の場合、prefectureIDとcityCodeは無視します
// 市区町村を指定しない場合、cityCodeは0にしてください
// 市区町村コードを指定した場合、都道府県IDは無視します（市区町村コードに含まれるため）
func NewWorkAddressID(isInJapan bool, prefectureID int, cityCode int) WorkAddressID {
	// 海外の場合
	if !isInJapan {
		return workAddressOverseas
	}
	// 市区町村指定なしの場合
	if cityCode == 0 {
		return WorkAddressID(constInJapan + prefectureID*constPrefecture + cityCode)
	}
	// 市区町村指定ありの場合
	return WorkAddressID(constInJapan + cityCode)
}

// IsInJapan 国内かどうか
func (w WorkAddressID) IsInJapan() bool {
	return w != workAddressOverseas // 海外以外は全て国内
}

// IsOverseas 海外かどうか
func (w WorkAddressID) IsOverseas() bool {
	return w == workAddressOverseas
}

// PrefectureID 都道府県IDを取得
// 海外だった場合はエラー
func (w WorkAddressID) PrefectureID() (PrefectureID, error) {
	if !w.IsInJapan() {
		return 0, errors.New("this work_address is not in japan")
	}
	return PrefectureID((int(w) - constInJapan) / constPrefecture), nil
}

// IsCityAssigned 市区町村コードまで指定しているかどうか
// 海外だった場合はエラー
func (w WorkAddressID) IsCityAssigned() (bool, error) {
	if !w.IsInJapan() {
		return false, errors.New("this work_address is not in japan")
	}
	return int(w)%constPrefecture != 0, nil
}

// CityID 市区町村コードを取得
// 市区町村の指定なしの場合、0。海外だった場合はエラー
func (w WorkAddressID) CityID() (CityID, error) {
	if ok, err := w.IsCityAssigned(); !ok || err != nil {
		return 0, err
	}
	return CityID(int(w) - constInJapan), nil
}

// 勤務地
type WorkAddresses []WorkAddress

func (wa *WorkAddresses) Scan(value any) error {
	return serializer.JsoniterJSONScan(wa, value)
}

func (wa WorkAddresses) Value() (driver.Value, error) {
	return serializer.StdJSONValue(wa)
}

func (wa *WorkAddresses) Append(id WorkAddressID, loc string) {
	*wa = append(*wa, WorkAddress{ID: id, Location: loc})
}

func (wa WorkAddresses) IsIncludeOverSeas() bool {
	for _, w := range wa {
		if w.ID.IsOverseas() {
			return true
		}
	}
	return false
}

// Equal ２つの勤務地に違いがあるか。並び順は気にしない。
func (wa WorkAddresses) Equal(wb WorkAddresses) bool {
	if len(wa) != len(wb) {
		return false
	}

	wbMap := make(map[WorkAddressID]WorkAddress, len(wb))
	for _, w := range wb {
		wbMap[w.ID] = w
	}

	for _, ae := range wa {
		if be, ok := wbMap[ae.ID]; !ok {
			return false
		} else {
			if ae.Location != be.Location {
				return false
			}
		}
	}
	return true
}

// GetPrefectureIDs 都道府県ID一覧を取得する。
// 海外は除外します。
func (wa WorkAddresses) GetPrefectureIDs() []PrefectureID {
	ret := make([]PrefectureID, 0, len(wa))
	for _, w := range wa {
		if w.ID.IsOverseas() {
			continue
		}
		prefectureID, _ := w.ID.PrefectureID()
		ret = append(ret, prefectureID)
	}
	return ret
}

// GetCityCodeList 市区町村コード一覧を取得する。
// 海外、国内(市区町村の指定なし)は除外します。
func (wa WorkAddresses) GetCityCodeList() []CityID {
	ret := make([]CityID, 0, len(wa))
	for _, w := range wa {
		IsCityAssigned, _ := w.ID.IsCityAssigned()
		if !IsCityAssigned {
			continue
		}
		cityCode, _ := w.ID.CityID()
		ret = append(ret, cityCode)
	}
	return ret
}

// WorkAddress システム内で勤務地絡みの判定をする際に使用する
type WorkAddress struct {
	ID       WorkAddressID
	Location string // WorkAddressIDを使ってマスターから取得した地名(補足を付け足す場合もある)
}

func (wa WorkAddresses) String() string {
	var buf bytes.Buffer
	b, _ := json.Marshal(wa)
	buf.Write(b)
	return buf.String()
}
