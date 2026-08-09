package tools

type (
	// 共通のリクエストパラメーター
	commonRequest struct {
		SessionID string
		RequestID string
	}

	// 希望職種保存リクエストパラメーター
	SaveOccupationPreferenceRequest struct {
		commonRequest
		OccupationNames []string
	}

	// 業種の意味情報検索のリクエスト
	searchIndustriesBySentenceRequest struct {
		commonRequest
		Sentence string
	}

	// APIの職種検索結果
	jobtypeSearchAPIResult struct {
		ID          int
		Name        string
		Description string
	}

	// APIの職種セマンティック検索結果
	jobtypeSearchSemanticAPIResponse struct {
		Keyword  string                   `json:"Keyword"`
		Jobtypes []jobtypeSearchAPIResult `json:"Jobtypes"`
	}

	// 職種の意味情報検索のリクエスト
	searchOccupationsBySentenceRequest struct {
		commonRequest
		Sentence string
	}

	vectorSearchParams struct {
		Provider string
		Keyword  string
		Distance float64
		Limit    int
	}

	// 場所のリクエスト
	locationRequest struct {
		LocationType   string
		PrefectureName string
		CityName       string
	}

	applicationParams struct {
		commonRequest
		ApplicationType string //面接かカジュアル面談か
		// 応募先のポジションID
		PositionID int
	}

	registrationParams struct {
		commonRequest
		Registration bool
	}

	industry struct {
		ID          int
		Name        string
		Description string
	}

	saveUserPreferencesRequest struct {
		commonRequest
		Amount                       *int     `json:"Amount,omitempty"`
		Scope                        *string  `json:"Scope,omitempty"`
		JobtypeNames                 []string `json:"JobtypeNames,omitempty"`
		LocationPrefectureResidence  *string  `json:"Location_Prefecture_Residence,omitempty"`
		LocationCityResidence        *string  `json:"Location_City_Residence,omitempty"`
		LocationPrefecturePreference *string  `json:"Location_Prefecture_Preference,omitempty"`
		LocationCityPreference       *string  `json:"Location_City_Preference,omitempty"`
		AverageOvertime              *string  `json:"AverageOvertime,omitempty"`
		DayOffs                      *string  `json:"DayOffs,omitempty"`
		FullyRemoteWork              *bool    `json:"FullyRemoteWork,omitempty"`
		UserPreferencesInSentence    *string  `json:"UserPreferences_In_Sentence,omitempty"`
	}

	// ポジション検索の共通パラメータ
	positionSearchCommonParams struct {
		ToolName        string             // ツール名
		JobtypeNames    []string           // 職種
		Salary          int                // 希望年収（万円）
		Locations       []*locationRequest // 場所（勤務地）
		PositionKeyword *string            // ポジションのキーワード
		DayOffs         *[]string          // 休日
		AverageOvertime *string            // 平均残業時間
	}

	// 汎用ポジション検索パラメータ
	genericPositionSearchParams struct {
		commonRequest
		positionSearchCommonParams
	}

	// IT専門職ポジション検索パラメータ
	itEngineerPositionSearchParams struct {
		commonRequest
		positionSearchCommonParams

		RemoteWorkPossible *bool // リモート可

		ProgrammingLanguages    *[]string // 言語（all）
		ProjectScales           *[]string // プロジェクト規模（IT）
		ApplicationFrameworks   *[]string // アプリケーションフレームワーク（IT）
		CloudServices           *[]string // クラウドサービス（IT）
		Phases                  *[]string // 担当フェーズ（IT）
		Positions               *[]string // ポジション（IT）
		SystemScales            *[]string // システム規模（IT）
		DevelopmentProjectTypes *[]string // 開発案件種別（IT／業務系）
	}

	// 金融営業ポジション検索パラメータ
	financialSalesPositionSearchParams struct {
		commonRequest
		positionSearchCommonParams

		HandledFinancialProducts *[]string // 取扱商材（金融商品）
		Qualifications           *[]string // 保有資格活用（意味情報）
		IndividualSalesStyles    *[]string // 個人営業スタイル（意味情報検索）
		SalesStyleDive           *string   // 新規飛び込みあり/なし
		SalesMethodStyles        *[]string // 営業スタイル（提案型／ルート型）
		TargetCustomerTypes      *[]string // 対象顧客（新規／既存）
		IncentiveSystem          *string   // インセンティブ制度（意味情報検索）
	}

	// ワークフロー開始のリクエスト
	startWorkflowRequest struct {
		commonRequest
		WorkflowID string
	}
)
