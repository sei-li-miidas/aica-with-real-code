package business

import (
	"database/sql/driver"
	"time"

	"github.com/samber/lo"

	"aica/api/domain/public/master"
	"aica/api/domain/user/apply/company"
	"aica/api/domain/user/apply/vo"
	"aica/api/sdk/gormio/serializer"
)

type (
	// ID 事業ID
	ID int

	Detail struct {
		Name                           string
		EmployeeQty                    *vo.ValueText      `json:",omitempty"`
		EstablishmentYear              *vo.ValueText      `json:",omitempty"`
		SalesScale                     *vo.ValueText      `json:",omitempty"`
		Industries                     *Industries        `json:",omitempty"`
		Stage                          *vo.ValueText      `json:",omitempty"`
		Product                        *Product           `json:",omitempty"`
		TargetCustomer                 *TargetCustomer    `json:",omitempty"`
		TrendKeyword                   *vo.ValuesText     `json:",omitempty"`
		MarketProspect                 *vo.ValueText      `json:",omitempty"`
		Strategy                       *vo.ValueText      `json:",omitempty"`
		Advantage                      *vo.ValueText      `json:",omitempty"`
		DecisionType                   *DecisionType      `json:",omitempty"`
		EmployeeAverageAge             *vo.ValueText      `json:",omitempty"`
		EmployeeWomanRate              *vo.ValueText      `json:",omitempty"`
		EmployeeMidCareerRate          *vo.ValueText      `json:",omitempty"`
		EmployeeForeignNationalityRate *vo.ValueText      `json:",omitempty"`
		EmployeeCharacter              *EmployeeCharacter `json:",omitempty"`
		HREvaluationPromotionSpeed     *vo.ValueText      `json:",omitempty"`
		ForeignNationalityRecruiting   *bool              `json:",omitempty"`

		// 以下、業種によって有無が決定される
		MedicalAdvantageField         *vo.ValuesText `json:",omitempty"`
		CarPartsTier                  *vo.ValueText  `json:",omitempty"`
		SIType                        *vo.ValueText  `json:",omitempty"`
		SIAdvantageIndustry           *vo.ValuesText `json:",omitempty"`
		ContractCompanyProfitSource   *vo.ValueText  `json:",omitempty"`
		ContractCompanyProjectTerm    *vo.ValueText  `json:",omitempty"`
		ContractCompanyClientResident *vo.ValueText  `json:",omitempty"`
		ContractCompanyResident       *vo.ValueText  `json:",omitempty"`
	}

	// Business 事業
	Business struct {
		ID        ID
		CompanyID company.ID
		Detail
		LastModifiedAt time.Time
		ImportedAt     time.Time
		TrashedAt      *time.Time `json:",omitempty"`
	}

	// Product 商材・サービスの特徴
	Product struct {
		Share          *vo.ValueText `json:",omitempty"`
		HasOwnProducts *vo.FlagText  `json:",omitempty"`
		Tangibleness   *Tangibleness `json:",omitempty"`
	}
	Tangibleness struct {
		Tangible   *vo.Flag `json:",omitempty"`
		Intangible *vo.Flag `json:",omitempty"`
		Text       *string  `json:",omitempty"`
	}

	// Industries 業種複数
	Industries struct {
		Industries []*Industry
		Text       *string
	}

	Industry struct {
		SmallID master.IndustrySmallID
		Label   string `json:",omitempty"`
		MainFlg bool
	}

	// TargetCustomer 対象顧客
	TargetCustomer struct {
		BtoBExists *bool   `json:",omitempty"`
		BtoCExists *bool   `json:",omitempty"`
		Text       *string `json:",omitempty"`
		BtoB       *BtoB   `json:",omitempty"`
		BtoC       *BtoC   `json:",omitempty"`
	}

	BtoB struct {
		IndustrySmallIDs vo.IDOnlyList
		Text             *string `json:",omitempty"`
	}

	BtoC struct {
		TargetIDs vo.IDOnlyList
		Text      *string `json:",omitempty"`
	}

	// DecisionType 意思決定
	DecisionType struct {
		Type1 int
		Type2 int
		Type3 int
		Type4 int
		Text  string `json:",omitempty"`
	}

	// EmployeeCharacter 組織・社員の特徴
	EmployeeCharacter struct {
		Character1  int
		Character2  int
		Character3  int
		Character4  int
		Character5  int
		Character6  int
		Character7  int
		Character8  int
		Character9  int
		Character10 int
		Character11 int
		Character12 int
		Text        string `json:",omitempty"`
	}
)

// IsIndustryExist 顧客の業界が設定されているかを返す
func (b *BtoB) IsIndustryExist() bool {
	if b == nil || len(b.IndustrySmallIDs) <= 0 {
		return false
	}
	// ID: 0 のIndustrySmallIDが存在することがある。
	// invalidなデータなので0がある場合はIndustrySmallIDsが設定されていないものとして扱う
	for _, v := range b.IndustrySmallIDs {
		if v.ID == 0 {
			return false
		}
	}
	return true
}

// ゴミ箱にはいっていない
func (b *Business) IsNotTrashed() bool {
	return b.TrashedAt == nil
}

// GetIndustrySmallRaw 事業内容ID（メインのみ）
func (b *Business) GetIndustrySmallRaw() *master.IndustrySmallID {
	if b.Industries == nil {
		return nil
	}
	for _, industry := range b.Industries.Industries {
		if industry.MainFlg {
			return lo.ToPtr(industry.SmallID)
		}
	}
	return nil
}

func (b *Business) GetIndustryTraitValue() []Industry {
	if b.Industries == nil {
		return nil
	}
	ret := make([]Industry, 0, len(b.Industries.Industries))
	isMap := master.Provider().IndustrySmallMap()
	for _, industry := range b.Industries.Industries {
		masterIndustry, found := isMap.Get(industry.SmallID)
		var name string
		if found {
			name = masterIndustry.Name
		} else {
			name = ""
		}
		ret = append(ret, Industry{
			SmallID: industry.SmallID,
			Label:   name,
			MainFlg: industry.MainFlg,
		})
	}
	return ret
}

func (b *Business) GetDecisionType() map[string]int {
	if b.DecisionType == nil {
		return map[string]int{}
	}
	ret := make(map[string]int)
	if b.DecisionType.Type1 != 0 {
		ret[master.DecisionTypeGroup1] = b.DecisionType.Type1
	}
	if b.DecisionType.Type2 != 0 {
		ret[master.DecisionTypeGroup2] = b.DecisionType.Type2
	}

	if b.DecisionType.Type3 != 0 {
		ret[master.DecisionTypeGroup3] = b.DecisionType.Type3
	}

	if b.DecisionType.Type4 != 0 {
		ret[master.DecisionTypeGroup4] = b.DecisionType.Type4
	}

	return ret
}

func (b *Business) GetEmployeeCharacter() map[string]int {
	if b.EmployeeCharacter == nil {
		return map[string]int{}
	}
	ret := make(map[string]int)
	if b.EmployeeCharacter.Character1 != 0 {
		ret[master.EmployeeCharacterGroup1] = b.EmployeeCharacter.Character1
	}
	if b.EmployeeCharacter.Character2 != 0 {
		ret[master.EmployeeCharacterGroup2] = b.EmployeeCharacter.Character2
	}
	if b.EmployeeCharacter.Character3 != 0 {
		ret[master.EmployeeCharacterGroup3] = b.EmployeeCharacter.Character3
	}
	if b.EmployeeCharacter.Character4 != 0 {
		ret[master.EmployeeCharacterGroup4] = b.EmployeeCharacter.Character4
	}
	if b.EmployeeCharacter.Character5 != 0 {
		ret[master.EmployeeCharacterGroup5] = b.EmployeeCharacter.Character5
	}
	if b.EmployeeCharacter.Character6 != 0 {
		ret[master.EmployeeCharacterGroup6] = b.EmployeeCharacter.Character6
	}
	if b.EmployeeCharacter.Character7 != 0 {
		ret[master.EmployeeCharacterGroup7] = b.EmployeeCharacter.Character7
	}
	if b.EmployeeCharacter.Character8 != 0 {
		ret[master.EmployeeCharacterGroup8] = b.EmployeeCharacter.Character8
	}
	if b.EmployeeCharacter.Character9 != 0 {
		ret[master.EmployeeCharacterGroup9] = b.EmployeeCharacter.Character9
	}
	if b.EmployeeCharacter.Character10 != 0 {
		ret[master.EmployeeCharacterGroup10] = b.EmployeeCharacter.Character10
	}
	if b.EmployeeCharacter.Character11 != 0 {
		ret[master.EmployeeCharacterGroup11] = b.EmployeeCharacter.Character11
	}
	if b.EmployeeCharacter.Character12 != 0 {
		ret[master.EmployeeCharacterGroup12] = b.EmployeeCharacter.Character12
	}
	return ret
}

func (b *Business) GetHREvaluationPromotionSpeed() *int {
	return b.HREvaluationPromotionSpeed.GetIntPtr()
}

func (b *Business) GetEmployeeAverageAge() *int {
	return b.EmployeeAverageAge.GetIntPtr()
}

func (b *Business) GetEmployeeMidCareerRate() *int {
	return b.EmployeeMidCareerRate.GetIntPtr()
}

func (b *Business) GetEmployeeWomanRate() *int {
	return b.EmployeeWomanRate.GetIntPtr()
}

func (b *Business) GetEmployeeForeignNationalityRate() *int {
	return b.EmployeeForeignNationalityRate.GetIntPtr()
}

func (b *Business) GetForeignNationalityRecruiting() *int {
	if b.ForeignNationalityRecruiting == nil {
		return nil
	}
	if *b.ForeignNationalityRecruiting {
		return lo.ToPtr(1)
	}
	return lo.ToPtr(0)
}

func (b *Business) GetBusinessEmployeeQty() *int {
	return b.EmployeeQty.GetIntPtr()
}

func (b *Business) GetBusinessEstablishmentYear() *int {
	return b.EstablishmentYear.GetIntPtr()
}

func (b *Business) GetBusinessSalesScale() *int {
	return b.SalesScale.GetIntPtr()
}

func (b *Business) GetStage() *int {
	return b.Stage.GetIntPtr()
}

func (b *Business) GetProductsShare() *int {
	if b.Product == nil {
		return nil
	}
	return b.Product.Share.GetIntPtr()
}

func (b *Business) GetHasOwnProducts() *vo.FlagText {
	if b.Product == nil {
		return nil
	}
	return b.Product.HasOwnProducts
}

func (b *Business) GetHasOwnProductsValue() *int {
	if b.Product == nil {
		return nil
	}
	return b.Product.HasOwnProducts.GetIntPtr()
}

func (b *Business) GetProductsTangibleness() []int {
	if b.Product == nil || b.Product.Tangibleness == nil {
		return nil
	}
	// TODO NW イケテナイ
	ret := make([]int, 0, 2)
	if b.Product.Tangibleness.Tangible != nil && b.Product.Tangibleness.Tangible.On {
		ret = append(ret, master.Tangible)
	}
	if b.Product.Tangibleness.Intangible != nil && b.Product.Tangibleness.Intangible.On {
		ret = append(ret, master.Intangible)
	}
	return ret
}

func (b *Business) GetTargetCustomer() []int {
	if b.TargetCustomer == nil {
		return nil
	}
	// TODO NW イケテナイ
	ret := make([]int, 0, 2)
	if b.TargetCustomer.BtoB.IsIndustryExist() {
		ret = append(ret, master.TargetCustomerBtoB)
	}
	if b.TargetCustomer.BtoC != nil {
		ret = append(ret, master.TargetCustomerBtoC)
	}
	return ret
}

func (b *Business) GetTargetCustomerBtoB() []int {
	if b.TargetCustomer == nil ||
		b.TargetCustomer.BtoB == nil ||
		b.TargetCustomer.BtoBExists == nil ||
		!*b.TargetCustomer.BtoBExists {
		return nil
	}

	ret := make([]int, 0, len(b.TargetCustomer.BtoB.IndustrySmallIDs))
	for _, b := range b.TargetCustomer.BtoB.IndustrySmallIDs {
		ret = append(ret, b.ID)
	}
	return ret
}

func (b *Business) GetTargetCustomerBtoC() []int {
	if b.TargetCustomer == nil ||
		b.TargetCustomer.BtoCExists == nil ||
		b.TargetCustomer.BtoC == nil ||
		!*b.TargetCustomer.BtoCExists {
		return nil
	}
	ret := make([]int, 0, len(b.TargetCustomer.BtoC.TargetIDs))
	for _, c := range b.TargetCustomer.BtoC.TargetIDs {
		ret = append(ret, c.ID)
	}
	return ret
}

func (b *Business) GetTrendKeyword() []int {
	return b.TrendKeyword.GetIntIDs()
}

func (b *Business) GetMarketProspect() *int {
	return b.MarketProspect.GetIntPtr()
}

func (b *Business) GetStrategy() *int {
	return b.Strategy.GetIntPtr()
}

func (b *Business) GetAdvantage() *int {
	return b.Advantage.GetIntPtr()
}

func (b *Business) GetMedicalAdvantageField() []int {
	return b.MedicalAdvantageField.GetIntIDs()
}

func (b *Business) GetSIType() *int {
	return b.SIType.GetIntPtr()
}

func (b *Business) GetSIAdvantageIndustry() []int {
	return b.SIAdvantageIndustry.GetIntIDs()
}

func (b *Business) GetCarPartsTier() *int {
	return b.CarPartsTier.GetIntPtr()
}

func (b *Business) GetContractCompanyProfitSource() *int {
	return b.ContractCompanyProfitSource.GetIntPtr()
}

func (b *Business) GetContractCompanyProjectTerm() *int {
	return b.ContractCompanyProjectTerm.GetIntPtr()
}

func (b *Business) GetContractCompanyClientResident() *int {
	return b.ContractCompanyClientResident.GetIntPtr()
}

func (b *Business) GetContractCompanyResident() *int {
	return b.ContractCompanyResident.GetIntPtr()
}

func (d *Detail) Scan(value interface{}) error {
	return serializer.JsoniterJSONScan(d, value)
}

func (d Detail) Value() (driver.Value, error) {
	return serializer.StdJSONValue(d)
}

// MiddleID 業種中分類
func (i Industry) MiddleID() master.IndustryMiddleID {
	return master.IndustryMiddleID(i.SmallID / 100)
}

// LargeID 業種大分類
func (i Industry) LargeID() master.IndustryLargeID {
	return master.IndustryLargeID(i.SmallID / 10000)
}

func (i *Industries) GetMainIndustry() *Industry {
	if i == nil {
		return nil
	}

	for _, industry := range i.Industries {
		if industry == nil {
			continue
		}
		if industry.MainFlg {
			return industry
		}
	}
	return nil
}

func (b *Business) GetIndustries() *Industries {
	if b == nil {
		return nil
	}
	return b.Industries
}
