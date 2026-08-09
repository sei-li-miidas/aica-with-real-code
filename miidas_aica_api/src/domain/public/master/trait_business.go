package master

//go:generate go run $GOPATH/src/miidas/domain/connect/enum/decorator/enumDecorator.go -type=MasterTraitBusinessID

// MasterTraitBusinessID 事業特徴ID
type MasterTraitBusinessID string

const (
	BtxEmployeeQty                    MasterTraitBusinessID = "btx_employee_qty"                      // 事業概要_事業の従業員数
	BtxYearsOfEstablishment           MasterTraitBusinessID = "btx_years_of_establishment"            // 事業概要_事業の設立
	BtxSalesScale                     MasterTraitBusinessID = "btx_sales_scale"                       // 事業概要_事業の売上規模
	BtxBusinessIndustry               MasterTraitBusinessID = "btx_business_industry"                 // 事業概要_事業内容
	BtxBusinessText                   MasterTraitBusinessID = "btx_business_text"                     // 事業概要_事業内容_事業内容
	BtxBusinessStage                  MasterTraitBusinessID = "btx_business_stage"                    // 事業概要_事業ステータス
	BtxProductsShare                  MasterTraitBusinessID = "btx_products_share"                    // 事業概要_商材・サービスの特徴_ポジション
	BtxHasOwnProducts                 MasterTraitBusinessID = "btx_has_own_products"                  // 事業概要_商材・サービスの特徴_本事業の商材・サービス
	BtxProductsTangibleness           MasterTraitBusinessID = "btx_products_tangibleness"             // 事業概要_商材・サービスの特徴_有形無形
	BtxTargetCustomer                 MasterTraitBusinessID = "btx_target_customer"                   // 事業概要_対象顧客
	BtxTargetCustomer2BIndustry       MasterTraitBusinessID = "btx_target_customer_2b_industry"       // 事業概要_対象顧客_BtoB
	BtxTargetCustomer2C               MasterTraitBusinessID = "btx_target_customer_2c"                // 事業概要_対象顧客_BtoC
	BtxTrendKeyword                   MasterTraitBusinessID = "btx_trend_keyword"                     // 事業概要_トレンドキーワード
	BtxMarketProspect                 MasterTraitBusinessID = "btx_market_prospect"                   // 事業概要_マーケット
	BtxBusinessStrategy               MasterTraitBusinessID = "btx_business_strategy"                 // 事業概要_戦略
	BtxAdvantage                      MasterTraitBusinessID = "btx_advantage"                         // 事業概要_事業の強み
	BtxDecisionType                   MasterTraitBusinessID = "btx_decision_type"                     // 事業概要_意思決定と裁量_1
	BtxEmployeeAverageAge             MasterTraitBusinessID = "btx_employee_average_age"              // 社員属性_平均年齢
	BtxEmployeeWomanRate              MasterTraitBusinessID = "btx_employee_woman_rate"               // 社員属性_女性社員比率
	BtxEmployeeMidCareerRate          MasterTraitBusinessID = "btx_employee_mid_career_rate"          // 社員属性_中途入社社員比率
	BtxEmployeeForeignNationalityRate MasterTraitBusinessID = "btx_employee_foreign_nationality_rate" // 社員属性_外国籍社員比率
	BtxEmployeeCharacter              MasterTraitBusinessID = "btx_employee_character"                // 社員属性_組織・社員の特徴_1
	BtxHREvaluationPromotionSpeed     MasterTraitBusinessID = "btx_hr_evaluation__promotion_speed"    // 人事評価_昇進昇格スピード
	BtxForeignNationalityRecruiting   MasterTraitBusinessID = "btx_foreign_nationality_recruiting"    // 採用関連　_外国籍社員積極採用
	BtiMedicalAdvantageField          MasterTraitBusinessID = "bti_medical_advantage_field"           // 業種別事業特徴_メディカル系_得意領域（メディカル）
	BtiCarPartsTier                   MasterTraitBusinessID = "bti_car_parts_tier"                    // 業種別事業特徴_メーカー（自動車部品）_Tier
	BtiSIType                         MasterTraitBusinessID = "bti_si__type"                          // 業種別事業特徴_システムインテグレーター_Si種別
	BtiSIAdvantageIndustry            MasterTraitBusinessID = "bti_si__advantage_industry"            // 業種別事業特徴_システムインテグレーター_得意領域（Sire）
	BtiContractCompanyProfitSource    MasterTraitBusinessID = "bti_contract_company__profit_source"   // 業種別事業特徴_請負会社の特徴_主な収益源
	BtiContractCompanyProjectTerm     MasterTraitBusinessID = "bti_contract_company__project_term"    // 業種別事業特徴_請負会社の特徴_プロジェクト期間
	BtiContractCompanyClientResident  MasterTraitBusinessID = "bti_contract_company__client_resident" // 業種別事業特徴_請負会社の特徴_客先常駐
	BtiContractCompanyResidentType    MasterTraitBusinessID = "bti_contract_company__resident_type"   // 業種別事業特徴_請負会社の特徴_常駐形態
)

const (
	DecisionTypeGroup1       = "（1）"  // 意思決定と裁量のグループ名 トップダウン型〜
	DecisionTypeGroup2       = "（2）"  // 意思決定と裁量のグループ名 論理・規則に従う〜
	DecisionTypeGroup3       = "（3）"  // 意思決定と裁量のグループ名 中央集権型〜
	DecisionTypeGroup4       = "（4）"  // 意思決定と裁量のグループ名 仕事の進め方にルールがある〜
	EmployeeCharacterGroup1  = "（1）"  // 組織・社員の特徴のグループ名 若手が活躍する〜
	EmployeeCharacterGroup2  = "（2）"  // 組織・社員の特徴のグループ名 挑戦的な社風〜
	EmployeeCharacterGroup3  = "（3）"  // 組織・社員の特徴のグループ名 活気がある〜
	EmployeeCharacterGroup4  = "（4）"  // 組織・社員の特徴のグループ名 上下関係が明確〜
	EmployeeCharacterGroup5  = "（5）"  // 組織・社員の特徴のグループ名 ビジネスライク〜
	EmployeeCharacterGroup6  = "（6）"  // 組織・社員の特徴のグループ名 アナログ組織運営〜
	EmployeeCharacterGroup7  = "（7）"  // 組織・社員の特徴のグループ名 体育会系〜
	EmployeeCharacterGroup8  = "（8）"  // 組織・社員の特徴のグループ名 仕事重視〜
	EmployeeCharacterGroup9  = "（9）"  // 組織・社員の特徴のグループ名 社内イベントが多い〜
	EmployeeCharacterGroup10 = "（10）" // 組織・社員の特徴のグループ名 上司との飲み会が多い〜
	EmployeeCharacterGroup11 = "（11）" // 組織・社員の特徴のグループ名 同僚との飲み会が多い〜
	EmployeeCharacterGroup12 = "（12）" // 組織・社員の特徴のグループ名 企業理念・ビジョンが浸透している〜
)

const (
	TraitValue1           = 1       // Deprecated:トレイトの値はBusinessのモデルにマッピングし、直接参照しない 5段階で指定できるトレイトバリューの数値
	TraitValue2           = 2       // Deprecated:トレイトの値はBusinessのモデルにマッピングし、直接参照しない 5段階で指定できるトレイトバリューの数値
	TraitValue3           = 3       // Deprecated:トレイトの値はBusinessのモデルにマッピングし、直接参照しない 5段階で指定できるトレイトバリューの数値
	TraitValue4           = 4       // Deprecated:トレイトの値はBusinessのモデルにマッピングし、直接参照しない 5段階で指定できるトレイトバリューの数値
	TraitValue5           = 5       // Deprecated:トレイトの値はBusinessのモデルにマッピングし、直接参照しない 5段階で指定できるトレイトバリューの数値
	TargetCustomerBtoB    = 1       // 対象顧客 BtoB
	TargetCustomerBtoC    = 2       // 対象顧客 BtoC
	Tangible              = 1       // 有形商材
	Intangible            = 2       // 無形商材
	TargetCustomerBtoBAll = 9000000 // [BtoB] 主な顧客の業界で「すべての業種」を選択した場合
)
