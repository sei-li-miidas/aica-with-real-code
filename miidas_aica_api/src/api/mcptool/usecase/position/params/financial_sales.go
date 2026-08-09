package params

import (
	"aica/api/api/mcptool/service"
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	pextensions "aica/api/api/mcptool/usecase/position/extensions"
	jobfilter "aica/api/domain/jobfilter"
	"aica/api/domain/public/master"
	"slices"
	"strings"
)

const (
	filterHandledFinancialProducts = "取扱商材（金融商品）"
	filterSalesMethodStyles        = "営業スタイル（提案型／ルート型）"
	filterTargetCustomerTypes      = "対象顧客（新規／既存）"
	filterQualifications           = "保有資格活用"
	filterIndividualSalesStyles    = "個人営業スタイル"
	filterIncentiveSystem          = "インセンティブ制度"
	filterSalesStyleDive           = "新規飛び込み"

	optionIncentiveBaseSalary   = "固定給重視"
	optionIncentiveCommission   = "フルコミッション（完全歩合）"
	optionIndividualSalesTeller = "銀行窓口（テラー）"
	optionIndividualSalesField  = "外回り（渉外）"
	optionIndividualSalesShop   = "来店型保険ショップ"
	optionQualificationBroker   = "証券外務員一種/二種"
	optionQualificationFP       = "FP（ファイナンシャルプランナー）1級/2級"
	optionQualificationAFP      = "AFP/CFP"
	optionQualificationLoan     = "貸金業務取扱主任者"
)

type FinancialSalesParams struct {
	PositionKeyword          string
	SalesStyleDive           *string
	HandledFinancialProducts []string
	SalesMethodStyles        []string
	TargetCustomerTypes      []string
	Qualifications           []string
	IndividualSalesStyles    []string
	IncentiveSystem          string
}

func (p *FinancialSalesParams) BuildExtensions(resolver pcontracts.JobSpecificSearchResolver) ([]pcontracts.SearchExtension, error) {
	extensions := make([]pcontracts.SearchExtension, 0)

	salesStyleDive, err := resolver.ResolveSalesStyleDive(p.SalesStyleDive)
	if err != nil {
		return nil, err
	}
	salesStyleDiveName := ""
	if p.SalesStyleDive != nil {
		salesStyleDiveName = *p.SalesStyleDive
	}
	extensions = append(extensions, pextensions.NewSalesStyleDiveExtension(salesStyleDiveName, salesStyleDive))

	skillGroups := []struct {
		label string
		names []string
	}{
		{label: filterHandledFinancialProducts, names: p.HandledFinancialProducts},
		{label: filterSalesMethodStyles, names: p.SalesMethodStyles},
		{label: filterTargetCustomerTypes, names: p.TargetCustomerTypes},
	}
	for _, group := range skillGroups {
		if len(group.names) == 0 {
			continue
		}
		skills, err := resolver.ResolveSkills(group.names)
		if err != nil {
			return nil, err
		}
		extensions = append(extensions, pextensions.NewSkillExtension(findFilterByName(FinancialSalesSearchFilters, group.label), skills))
	}

	keywordParts := make([]string, 0)
	keywordParts = append(keywordParts, p.Qualifications...)
	keywordParts = append(keywordParts, p.IndividualSalesStyles...)
	if p.IncentiveSystem != "" {
		keywordParts = append(keywordParts, p.IncentiveSystem)
	}
	if p.PositionKeyword != "" {
		keywordParts = append(keywordParts, p.PositionKeyword)
	}
	extensions = append(extensions, pextensions.NewPositionKeywordExtension(strings.Join(keywordParts, ",")))

	return extensions, nil
}

func (p *FinancialSalesParams) Keyword() string {
	if p == nil {
		return ""
	}
	return p.PositionKeyword
}

func (p *FinancialSalesParams) SelectedOptionNamesByFilter() map[string]map[string]struct{} {
	result := make(map[string]map[string]struct{})
	add := func(filterName string, optionNames []string) {
		if len(optionNames) == 0 {
			return
		}
		seen := result[filterName]
		if seen == nil {
			seen = make(map[string]struct{})
			result[filterName] = seen
		}
		for _, name := range optionNames {
			if name == "" {
				continue
			}
			seen[name] = struct{}{}
		}
	}

	add(filterHandledFinancialProducts, p.HandledFinancialProducts)
	add(filterSalesMethodStyles, p.SalesMethodStyles)
	add(filterTargetCustomerTypes, p.TargetCustomerTypes)
	add(filterQualifications, p.Qualifications)
	add(filterIndividualSalesStyles, p.IndividualSalesStyles)
	if p.IncentiveSystem != "" {
		add(filterIncentiveSystem, []string{p.IncentiveSystem})
	}
	if p.SalesStyleDive != nil && *p.SalesStyleDive != "" {
		add(filterSalesStyleDive, []string{*p.SalesStyleDive})
	}

	return result
}

func (p *FinancialSalesParams) RemotePositionOptionState() *pcontracts.RemotePositionOptionState {
	return &pcontracts.RemotePositionOptionState{
		HasOption: false,
	}
}

var FinancialSalesSearchFilters []*jobfilter.JobSearchFilterOtherFilter

func initFinancialSalesSearchFilters(cacheService *service.MiidasCacheService) {
	filterDefinitions := []struct {
		key   string
		label string
	}{
		{key: "HandledFinancialProducts", label: filterHandledFinancialProducts},
		{key: "SalesMethodStyles", label: filterSalesMethodStyles},
		{key: "TargetCustomerTypes", label: filterTargetCustomerTypes},
	}

	FinancialSalesSearchFilters = make([]*jobfilter.JobSearchFilterOtherFilter, 0, len(filterDefinitions))
	for _, def := range filterDefinitions {
		filter := buildSkillFilter(cacheService, def.label)
		if filter == nil {
			continue
		}
		if len(filter.Options) == 0 {
			continue
		}
		filter.Key = def.key
		FinancialSalesSearchFilters = append(FinancialSalesSearchFilters, filter)
	}

	// 以下はスキルではないため、手動で追加
	options, _ := cacheService.GetTraitPositionOptionUserSideNames(master.PtjSalesStyleDive)
	flags := make([]*jobfilter.JobSearchFilterOtherFilterOption, len(options))
	for i, opt := range options {
		flags[i] = &jobfilter.JobSearchFilterOtherFilterOption{Label: opt, Value: opt}
	}
	FinancialSalesSearchFilters = append(FinancialSalesSearchFilters, &jobfilter.JobSearchFilterOtherFilter{
		Key:     "SalesStyleDive",
		Name:    filterSalesStyleDive,
		Type:    jobfilter.JobSearchFilterTypeSingle,
		Options: flags,
	})

	// Convert []string to []shared_dto.Flag for インセンティブ制度
	incentiveOptions := []string{optionIncentiveBaseSalary, optionIncentiveCommission}
	incentiveFlags := make([]*jobfilter.JobSearchFilterOtherFilterOption, len(incentiveOptions))
	for i, opt := range incentiveOptions {
		incentiveFlags[i] = &jobfilter.JobSearchFilterOtherFilterOption{Label: opt, Value: opt}
	}
	FinancialSalesSearchFilters = append(FinancialSalesSearchFilters, &jobfilter.JobSearchFilterOtherFilter{
		Key:     "IncentiveSystem",
		Name:    filterIncentiveSystem,
		Type:    jobfilter.JobSearchFilterTypeSingle,
		Options: incentiveFlags,
	})

	individualSalesOptions := []string{optionIndividualSalesTeller, optionIndividualSalesField, optionIndividualSalesShop}
	individualSalesFlags := make([]*jobfilter.JobSearchFilterOtherFilterOption, len(individualSalesOptions))
	for i, opt := range individualSalesOptions {
		individualSalesFlags[i] = &jobfilter.JobSearchFilterOtherFilterOption{Label: opt, Value: opt}
	}
	FinancialSalesSearchFilters = append(FinancialSalesSearchFilters, &jobfilter.JobSearchFilterOtherFilter{
		Key:     "IndividualSalesStyles",
		Name:    filterIndividualSalesStyles,
		Type:    jobfilter.JobSearchFilterTypeMultiple,
		Options: individualSalesFlags,
	})

	qualificationOptions := []string{
		optionQualificationBroker,
		optionQualificationFP,
		optionQualificationAFP,
		optionQualificationLoan,
	}
	qualificationFlags := make([]*jobfilter.JobSearchFilterOtherFilterOption, len(qualificationOptions))
	for i, opt := range qualificationOptions {
		qualificationFlags[i] = &jobfilter.JobSearchFilterOtherFilterOption{Label: opt, Value: opt}
	}
	FinancialSalesSearchFilters = append(FinancialSalesSearchFilters, &jobfilter.JobSearchFilterOtherFilter{
		Key:     "Qualifications",
		Name:    filterQualifications,
		Type:    jobfilter.JobSearchFilterTypeMultiple,
		Options: qualificationFlags,
	})

}

func NewFinancialSalesParamsFromSelectedOptions(selected map[string][]string) *FinancialSalesParams {
	var salesStyleDive *string
	if values := selected[filterSalesStyleDive]; len(values) > 0 {
		value := values[0]
		salesStyleDive = &value
	}

	incentiveSystem := ""
	if values := selected[filterIncentiveSystem]; len(values) > 0 {
		incentiveSystem = values[0]
	}

	return &FinancialSalesParams{
		SalesStyleDive:           salesStyleDive,
		HandledFinancialProducts: slices.Clone(selected[filterHandledFinancialProducts]),
		SalesMethodStyles:        slices.Clone(selected[filterSalesMethodStyles]),
		TargetCustomerTypes:      slices.Clone(selected[filterTargetCustomerTypes]),
		Qualifications:           slices.Clone(selected[filterQualifications]),
		IndividualSalesStyles:    slices.Clone(selected[filterIndividualSalesStyles]),
		IncentiveSystem:          incentiveSystem,
	}
}
