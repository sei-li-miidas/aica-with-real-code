package vo

import (
	"github.com/pkg/errors"
)

// TODO: not quite know what this is
//go:generate go run $GOPATH/src/miidas/domain/connect/enum/decorator/enumDecorator.go -type=IncomeID,IncomeFromTypeID -output=income_string.go

// IncomeID 収入ID
type IncomeID int

const (
	IncomeIDMin      IncomeID = 2 // オファー時の年収指定は250万未満は2で渡される為
	IncomeID250to299 IncomeID = 3
	IncomeID300to349 IncomeID = 4
	IncomeID350to399 IncomeID = 5
	IncomeID400to449 IncomeID = 6
	IncomeID450to499 IncomeID = 7
	IncomeID500to549 IncomeID = 8
	IncomeID550to599 IncomeID = 9
	IncomeID600to649 IncomeID = 10
	IncomeID650to699 IncomeID = 11
	IncomeID700to749 IncomeID = 12
	IncomeID750to799 IncomeID = 13
	IncomeID800to849 IncomeID = 14
	IncomeID850to899 IncomeID = 15
	IncomeID900to949 IncomeID = 16
	IncomeID950to999 IncomeID = 17
	IncomeIDMax      IncomeID = 18 // オファー時の年収指定は1000万以上は18で渡される為
)

const IncomeMin = 100 // 最小の年収。100万円。

// IncomeToIncomeID 年収（現／希望のいずれでも）を（オファー金額マップのキーの範囲の）年収IDに変換する
// 引数のincomeは万円単位。
func IncomeToIncomeID(income int) IncomeID {
	switch {
	case income < 250:
		return IncomeIDMin
	case 250 <= income && income <= 299:
		return IncomeID250to299
	case 300 <= income && income <= 349:
		return IncomeID300to349
	case 350 <= income && income <= 399:
		return IncomeID350to399
	case 400 <= income && income <= 449:
		return IncomeID400to449
	case 450 <= income && income <= 499:
		return IncomeID450to499
	case 500 <= income && income <= 549:
		return IncomeID500to549
	case 550 <= income && income <= 599:
		return IncomeID550to599
	case 600 <= income && income <= 649:
		return IncomeID600to649
	case 650 <= income && income <= 699:
		return IncomeID650to699
	case 700 <= income && income <= 749:
		return IncomeID700to749
	case 750 <= income && income <= 799:
		return IncomeID750to799
	case 800 <= income && income <= 849:
		return IncomeID800to849
	case 850 <= income && income <= 899:
		return IncomeID850to899
	case 900 <= income && income <= 949:
		return IncomeID900to949
	case 950 <= income && income <= 999:
		return IncomeID950to999
	default:
		return IncomeIDMax
	}
}

// GetOfferIncome 年収の取得
// baseIncomeとfrom/to、最低年収からfrom/toを算出します
func GetOfferIncome(baseIncome int, offerIncomeFrom, offerIncomeTo int) (int, int) {
	switch {
	case baseIncome < IncomeMin:
		return IncomeMin, offerIncomeTo
	case baseIncome < offerIncomeTo:
		return baseIncome, offerIncomeTo
	default:
		return offerIncomeFrom, offerIncomeTo
	}
}

// IncomeFromTypeID 年収FromタイプID
type IncomeFromTypeID int

const (
	IncomeFromTypeDefaultValue IncomeFromTypeID = 0 // ポジション作成時のデフォルトで設定される値として定義
	IncomeFromTypeEach         IncomeFromTypeID = 1 // 個別に提示
	IncomeFromTypeUniform      IncomeFromTypeID = 2 // 一律提示
	IncomeFromTypeCurrent      IncomeFromTypeID = 3 // 現年収を提示
	IncomeFromTypeWill         IncomeFromTypeID = 4 // 希望年収を提示
)

// CalculateOfferIncome 現年収、希望年収、オファー年収のマップを元にオファー年収を算出します。
func (i IncomeFromTypeID) CalculateOfferIncome(annualIncome, willIncome int, incomeMap map[IncomeID]FromTo) (int, int) {
	switch i {
	case IncomeFromTypeEach, IncomeFromTypeUniform:
		income := incomeMap[IncomeToIncomeID(annualIncome)]
		return income.From, income.To
	case IncomeFromTypeCurrent:
		income := incomeMap[IncomeToIncomeID(annualIncome)]
		return GetOfferIncome(annualIncome, income.From, income.To)
	case IncomeFromTypeWill:
		income := incomeMap[IncomeToIncomeID(willIncome)]
		return GetOfferIncome(willIncome, income.From, income.To)
	case IncomeFromTypeDefaultValue:
		panic("確約年収の設定が終わる前にメソッドが呼ばれることを考慮しない")
	default:
		panic(errors.Errorf("ここに来たらIncomeFromTypeIDの実装漏れ:%d", i))
	}
}

// IsCalculatable 確約年収計算可能？
func (i IncomeFromTypeID) IsCalculatable() bool {
	return i != IncomeFromTypeDefaultValue
}

type (
	Income struct {
		IncomeID   IncomeID
		IncomeFrom int
		IncomeTo   int
	}
)
