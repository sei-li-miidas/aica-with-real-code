package competency

//go:generate go run $GOPATH/src/miidas/domain/connect/enum/decorator/enumDecorator.go -type=Status,Axis,EvalCompetencyValue -output=enum_string.go

// Status 受験状態
type Status uint8

const (
	StatusNotTaken          Status = 0 // 未受験
	StatusPartOneInProgress Status = 1 // 第一部受験中
	StatusPartTwoInProgress Status = 2 // 第二部受験中
	StatusAllCompleted      Status = 3 // 全て完了
)

// IsNoResult 診断結果がまだでてない状態か
func (s Status) IsNoResult() bool {
	return s <= StatusPartOneInProgress
}

// Axis コンピテンシー指標名
type Axis string

const (
	// パーソナリティ
	ManagementStyle        Axis = "ManagementStyle"        // マネジメントスタイル
	Vitality               Axis = "Vitality"               // 活力
	Sociability            Axis = "Sociability"            // 人あたり
	Teamwork               Axis = "Teamwork"               // チームワーク
	Creativity             Axis = "Creativity"             // 創造性
	ProblemSolving         Axis = "ProblemSolving"         // 問題解決力
	PressureTolerance      Axis = "PressureTolerance"      // プレッシャーへの耐性
	Coordination           Axis = "Coordination"           // 調整力
	Leadership             Axis = "Leadership"             // リーダーシップ
	Adaptability           Axis = "Adaptability"           // 対応力
	Perseverance           Axis = "Perseverance"           // 粘り強さ
	Focus                  Axis = "Focus"                  // 一点集中
	Planning               Axis = "Planning"               // 計画性
	InterpersonalInfluence Axis = "InterpersonalInfluence" // 対人影響
	GoalSetting            Axis = "GoalSetting"            // 目標の立て方
	Decisiveness           Axis = "Decisiveness"           // 決断力
	AnalyticalAbility      Axis = "AnalyticalAbility"      // 分析力
	Conceptualization      Axis = "Conceptualization"      // 概念化
	Continuity             Axis = "Continuity"             // 継続力
	RelationshipBuilding   Axis = "RelationshipBuilding"   // 人間関係の構築
	Empathy                Axis = "Empathy"                // 共感力
	SelfLearning           Axis = "SelfLearning"           // 自学
	// ストレス要因
	UncertainSituations           Axis = "UncertainSituations"           // 不確実な状況
	ResponseToSuddenChanges       Axis = "ResponseToSuddenChanges"       // 急な変化への対応
	HardWork                      Axis = "HardWork"                      // ハードワーク
	LackOfPlanning                Axis = "LackOfPlanning"                // 計画性のなさ
	StrictManagement              Axis = "StrictManagement"              // 厳しい管理
	LackOfEvaluation              Axis = "LackOfEvaluation"              // 評価の欠如
	InabilityToExerciseInitiative Axis = "InabilityToExerciseInitiative" // 主体性が発揮できない
	ExclusionFromDecisionMaking   Axis = "ExclusionFromDecisionMaking"   // 意思決定に関与できない
	LowStandards                  Axis = "LowStandards"                  // 要求水準が低い
	HighAnalysis                  Axis = "HighAnalysis"                  // 高度な分析
	LackOfLearningOpportunities   Axis = "LackOfLearningOpportunities"   // 学習機会の不足
	FollowingPrecedents           Axis = "FollowingPrecedents"           // 前例踏襲
	RoutineWork                   Axis = "RoutineWork"                   // 定型業務
	DifficultDecisions            Axis = "DifficultDecisions"            // 困難な決断
	NegotiationTasks              Axis = "NegotiationTasks"              // 交渉業務
	ConsensusBuilding             Axis = "ConsensusBuilding"             // 合意形成
	ConflictWithOthers            Axis = "ConflictWithOthers"            // 周囲との対立
	DryWorkplace                  Axis = "DryWorkplace"                  // ドライな職場
	CaughtInTheMiddle             Axis = "CaughtInTheMiddle"             // 板挟み状態
	CollaborativeWork             Axis = "CollaborativeWork"             // 共同業務
	SolitaryWork                  Axis = "SolitaryWork"                  // 孤独な業務 NOTE: ミイダスラップ用。ミイダスラップを新ラベルで一新する時に削除予定です。
	// 上司部下適正
	Directive   Axis = "Directive"   // 指示型
	Delegation  Axis = "Delegation"  // 委任型
	Listening   Axis = "Listening"   // 傾聴型
	Dialogue    Axis = "Dialogue"    // 対話型
	Negotiation Axis = "Negotiation" // 交渉型
	Obedient    Axis = "Obedient"    // 従順型
	Autonomous  Axis = "Autonomous"  // 自律型
	Cooperative Axis = "Cooperative" // 協調型
	Proactive   Axis = "Proactive"   // 提案型
	Assertive   Axis = "Assertive"   // 主張型

	Vanity Axis = "Vanity" // 虚栄心 NOTE: 求職者側ポジション検索条件、ポジション特徴、ターゲット、評価グループの特徴に利用されることはない
)

// EvalCompetencyValue ポジションの「特に評価されるコンピテンシー」の相関値
type EvalCompetencyValue int

const (
	EvalCompetencyValueWeak   EvalCompetencyValue = 1 // 傾向が弱い（負の相関）
	EvalCompetencyValueStrong EvalCompetencyValue = 2 // 傾向が強い（正の相関）
)
