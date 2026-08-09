import { getKeys } from "@/types/utility-types";

export const COMPETENCY_NAVIGATION = {
  INDEX: "/competency", // コンピテンシー診断
  EXAM: "/competency/exam", // コンピテンシー診断回答
  RESULT: "/competency/result", // コンピテンシー診断結果
} as const;

// コンピテンシー診断の受験状態
export const COMPETENCY_EXAM_STATUS = {
  BEFORE_START: 0, // 未受験
  AFTER_START: 1, // 受験開始済み
  PART1_FINISHED: 2, // 第一部完了
  FINISHED: 3, // 第二部完了 or 旧コンピテンシー受験済（共感スキルは問わない）
} as const;

// コンピテンシー診断で1ページあたりに表示する質問数
export const COMPETENCY_QUESTION_NUMBER_PER_PAGE = 20;

// コンピテンシー診断のカテゴリ
export const COMPETENCY_ITEM_MAIN_CATEGORY = {
  PERSONALITY: {
    ID: "Personality",
    Label: "パーソナリティの傾向",
    Description:
      "仕事をするうえで活かせるあなたの強みや特徴について分析しています。",
  },
  STRESS: {
    ID: "Stress",
    Label: "ストレス要因",
    Description:
      "あなたが特にストレスを感じやすい職場環境について分析しています。",
  },
  HIERARCHY: {
    ID: "Hierarchy",
    Label: "上司・部下としての傾向",
    Description:
      "あなたが上司または部下としてどのような傾向があるか分析しています。",
  },
} as const;

// コンピテンシー診断のサブカテゴリ
export const COMPETENCY_ITEM_SUB_CATEGORY = {
  PERSONALITY: {
    MANAGEMENT: "マネジメントの傾向",
    APPROACH: "取り組み方の傾向",
    ENVIRONMENT: "環境適応の傾向",
    HUMAN_RELATIONS: "対人関係の傾向",
    ACTION: "思考・行動の傾向",
    WILL: "成長意欲の傾向",
  },
  STRESS: {
    ENVIRONMENT: "職場環境要因",
    WORK: "仕事要因",
    HUMAN_RELATIONS: "人間関係要因",
  },
  HIERARCHY: {
    BOSS: "上司として",
    MEMBER: "部下として",
  },
} as const;

// コンピテンシーの特徴の項目
export const COMPETENCY_ITEM = {
  /** マネジメントスタイル */
  ManagementStyle: {
    ID: "ManagementStyle",
    Label: "マネジメントスタイル",
    PointHighText:
      "長期的なビジョン達成に向けてメンバーや状況を把握した上で、自分が具体的に指揮をとる",
    PointLowText:
      "短期的な目標達成に向けてスケジュールやタスクを設定した上で、メンバーの自主性を尊重し委ねる",
    Description:
      "10に近いほど、長期的なビジョン達成に向けてメンバーや状況を把握した上で、自分が具体的に指揮をとる。1に近いほど、短期的な目標達成に向けてスケジュールやタスクを設定した上で、メンバーの自主性を尊重し委ねる。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.MANAGEMENT,
  },
  /** リーダーシップ */
  Leadership: {
    ID: "Leadership",
    Label: "リーダーシップ",
    PointHighText: "自分が先頭に立ってメンバーを牽引するほうが得意である",
    PointLowText: "自分は先頭に立たず、誰かをフォローするほうが得意である",
    Description:
      "10に近いほど、自ら先頭に立ってメンバーを牽引するほうが得意である。1に近いほど、自分は先頭に立たず、誰かをフォローするほうが得意である。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.MANAGEMENT,
  },
  /** 対人影響 */
  InterpersonalInfluence: {
    ID: "InterpersonalInfluence",
    Label: "対人影響",
    PointHighText:
      "相手の態度や行動に影響を与えるように働きかけるほうが得意である",
    PointLowText: "相手の態度や行動に干渉せずにはたらく方が得意である",
    Description:
      "10に近いほど、相手の態度や行動に影響を与えるように働きかけるほうが得意である。1に近いほど、相手の態度や行動に干渉せずはたらく方が得意である。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.MANAGEMENT,
  },
  /** 調整力 */
  Coordination: {
    ID: "Coordination",
    Label: "調整力",
    PointHighText: "周囲との調整が必要となる業務のほうが得意である",
    PointLowText: "周囲との調整が少ない業務のほうが得意である",
    Description:
      "10に近いほど、周囲との調整が必要となる業務のほうが得意である。1に近いほど、周囲との調整が少ない業務のほうが得意である。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.MANAGEMENT,
  },
  /** 決断力 */
  Decisiveness: {
    ID: "Decisiveness",
    Label: "決断力",
    PointHighText: "自分で物事を決断しながら業務に取り組むほうが得意である",
    PointLowText: "周囲から指示を受けながら業務に取り組むほうが得意である",
    Description:
      "10に近いほど、自分で物事を決断しながら業務に取り組むほうが得意である。1に近いほど、周囲から指示を受けながら業務に取り組むほうが得意である。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.MANAGEMENT,
  },
  /** 活力 */
  Vitality: {
    ID: "Vitality",
    Label: "活力",
    PointHighText:
      "周囲と競いながらエネルギッシュに業務に取り組むほうが得意である",
    PointLowText:
      "競争は好まず、自分のペースと効率を重視して業務に取り組むほうが得意である",
    Description:
      "10に近いほど、周囲と競いながらエネルギッシュに業務に取り組むほうが得意である。1に近いほど、競争を好まず、自分のペースと効率を重視しながら業務に取り組むほうが得意である。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.APPROACH,
  },
  /** 粘り強さ */
  Perseverance: {
    ID: "Perseverance",
    Label: "粘り強さ",
    PointHighText:
      "難しい問題に直面したとき、諦めずに粘り強く取り組むほうを優先する",
    PointLowText:
      "難しい問題に直面したとき、その問題より簡単に解ける問題に取り組むほうを優先する",
    Description:
      "10に近いほど、諦めずに粘り強く取り組むほうを優先する。1に近いほど、その問題より簡単に解ける問題に取り組むほうを優先する。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.APPROACH,
  },
  /** 一点集中 */
  Focus: {
    ID: "Focus",
    Label: "一点集中",
    PointHighText: "一つの作業に集中するほうが得意である",
    PointLowText: "複数の作業を並行して進めるほうが得意である",
    Description:
      "10に近いほど、一つの作業に集中するほうが得意である。1に近いほど、複数の作業を並行して進めるほうが得意である。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.APPROACH,
  },
  /** 継続力 */
  Continuity: {
    ID: "Continuity",
    Label: "継続力",
    PointHighText: "一つの目標に向けて努力を続けるほうが得意である",
    PointLowText: "状況に応じて目標を変えながら取り組むほうが得意である",
    Description:
      "10に近いほど、一つの目標に向けて努力を続けるほうが得意である。1に近いほど、状況に応じて目標を変えながら取り組むほうが得意である。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.APPROACH,
  },
  /** プレッシャーへの耐性 */
  PressureTolerance: {
    ID: "PressureTolerance",
    Label: "プレッシャーへの耐性",
    PointHighText: "プレッシャーやストレスが多い業務のほうが得意である",
    PointLowText: "プレッシャーやストレスが少ない業務のほうが得意である",
    Description:
      "10に近いほど、プレッシャーやストレスが多い業務のほうが得意である。1に近いほど、プレッシャーやストレスが少ない業務のほうが得意である。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.ENVIRONMENT,
  },
  /** 対応力 */
  Adaptability: {
    ID: "Adaptability",
    Label: "対応力",
    PointHighText: "臨機応変な対応が必要となる業務のほうが得意である",
    PointLowText: "一貫性のある考えや行動を求められる業務のほうが得意である",
    Description:
      "10に近いほど、臨機応変な対応が必要な業務のほうが得意である。1に近いほど、一貫性のある考えや行動を取ったり決まった方法を守る業務のほうが得意である。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.ENVIRONMENT,
  },
  /** 人あたり */
  Sociability: {
    ID: "Sociability",
    Label: "人あたり",
    PointHighText: "相手の意見を尊重し、好印象を与えるほうが得意である",
    PointLowText: "相手が受ける印象を気にせず自己主張するほうが得意である",
    Description:
      "10に近いほど、相手の意見を尊重して好印象を与えるほうが得意である。1に近いほど、相手が受ける印象を気にせず自己主張するほうが得意である。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.HUMAN_RELATIONS,
  },
  /** チームワーク */
  Teamwork: {
    ID: "Teamwork",
    Label: "チームワーク",
    PointHighText: "チームに溶け込んで、メンバーと一緒に取り組む方が得意である",
    PointLowText: "チームの一員として働くよりも、単独で取り組む方が得意である",
    Description:
      "10に近いほど、チームに溶け込んでメンバーと一緒に取り組む方が得意である。1に近いほど、チームの一員として働くよりも単独で取り組む方が得意である。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.HUMAN_RELATIONS,
  },
  /** 人間関係の構築 */
  RelationshipBuilding: {
    ID: "RelationshipBuilding",
    Label: "人間関係の構築",
    PointHighText:
      "状況に応じて新たに人間関係を築きながら業務に取り組むほうが得意である",
    PointLowText: "すでにある人間関係のなかで業務に取り組むほうが得意である",
    Description:
      "10に近いほど、状況に応じて新たに人間関係を築きながら業務に取り組むほうが得意である。1に近いほど、すでにある人間関係のなかで業務に取り組むほうが得意である。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.HUMAN_RELATIONS,
  },
  /** 共感力 */
  Empathy: {
    ID: "Empathy",
    Label: "共感力",
    PointHighText:
      "自分の都合だけでなく、周囲の事情に配慮しながら業務に取り組むほうが得意である",
    PointLowText:
      "周囲に気を使わず、自分の都合を優先して業務に取り組むほうが得意である",
    Description:
      "10に近いほど、自分の都合だけでなく、周囲の事情に配慮しながら業務に取り組むほうが得意である。1に近いほど、周囲に気を使わず、自分の都合を優先して業務に取り組むほうが得意である。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.HUMAN_RELATIONS,
  },
  /** 創造性 */
  Creativity: {
    ID: "Creativity",
    Label: "創造性",
    PointHighText:
      "これまでの発想や方法にとらわれず考え、行動するほうが得意である",
    PointLowText: "これまで通りの発想や方法にならって行動するほうが得意である",
    Description:
      "10に近いほど、これまでの発想や方法にとらわれずに考え、行動するほうが得意である。1に近いほど、これまで通りの発想や方法にならって行動するほうが得意である。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.ACTION,
  },
  /** 問題解決力 */
  ProblemSolving: {
    ID: "ProblemSolving",
    Label: "問題解決力",
    PointHighText: "自ら問題を見つけ、その解決に向けて取り組むほうが得意である",
    PointLowText:
      "問題意識をあまり持たず、目の前の業務に取り組むほうが得意である",
    Description:
      "10に近いほど、自ら問題を見つけ、解決に向けて取り組むほうが得意である。1に近いほど、問題意識をあまり持たず、目の前の業務に取り組むほうが得意である。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.ACTION,
  },
  /** 計画性 */
  Planning: {
    ID: "Planning",
    Label: "計画性",
    PointHighText: "しっかりと計画を立てて業務を進めるほうが得意である",
    PointLowText:
      "計画を立てずその場その場で考えて業務を進めるほうが得意である",
    Description:
      "10に近いほど、しっかりと計画を立てて業務を進めるほうが得意である。1に近いほど、計画を立てずにその場その場で考えて業務を進めるほうが得意である。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.ACTION,
  },
  /** 分析力 */
  AnalyticalAbility: {
    ID: "AnalyticalAbility",
    Label: "分析力",
    PointHighText: "高度な分析が求められる業務のほうが得意である",
    PointLowText: "分析作業が求められない業務のほうが得意である",
    Description:
      "10に近いほど、高度な分析が求められる業務のほうが得意である。1に近いほど、分析作業が求められない業務のほうが得意である。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.ACTION,
  },
  /** 概念化 */
  Conceptualization: {
    ID: "Conceptualization",
    Label: "概念化",
    PointHighText:
      "抽象的な物事に興味を持ち、本質を整理して業務に活かすほうが得意である",
    PointLowText: "具体的でわかりやすい業務に取り組むほうが得意である",
    Description:
      "10に近いほど、抽象的な物事に興味を持ち、本質を整理して業務に活かすほうが得意である。1に近いほど、具体的でわかりやすい業務に取り組むほうが得意である。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.ACTION,
  },
  /** 目標の立て方 */
  GoalSetting: {
    ID: "GoalSetting",
    Label: "目標の立て方",
    PointHighText:
      "失敗の可能性があっても高い目標を掲げ、挑戦を続ける傾向がある",
    PointLowText:
      "失敗の可能性が低い手堅い目標を立て、安定的に活動する傾向がある",
    Description:
      "10に近いほど、失敗の可能性があっても高い目標を掲げ、挑戦を続ける傾向がある。1に近いほど、失敗の可能性が低い手堅い目標を立て、安定的に活動する傾向がある。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.WILL,
  },
  /** 自学 */
  SelfLearning: {
    ID: "SelfLearning",
    Label: "自学",
    PointHighText:
      "わからないことがあれば、自ら調べるなど主体的に学ぶほうが得意である",
    PointLowText:
      "わからないことがあれば、誰かに教えてもらいながら学ぶほうが得意である",
    Description:
      "10に近いほど、わからないことは自ら調べるなど主体的に学ぶほうが得意である。1に近いほど、わからないことは誰かに教えてもらいながら学ぶほうが得意である。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.WILL,
  },
  /** 不確実性な状況 */
  UncertainSituations: {
    ID: "UncertainSituations",
    Label: "不確実な状況",
    PointHighText: "想定できない出来事が起こりやすい職場にストレスを感じやすい",
    PointLowText: "想定済みの出来事ばかり起こる職場にストレスを感じやすい",
    Description: "想定できない出来事が起こりやすい職場。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.STRESS,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.STRESS.ENVIRONMENT,
  },
  /** 急な変化への対応 */
  ResponseToSuddenChanges: {
    ID: "ResponseToSuddenChanges",
    Label: "急な変化への対応",
    PointHighText:
      "急な依頼や指示への対応が求められる職場にストレスを感じやすい",
    PointLowText:
      "変化がなく決められた対応しかできない職場にストレスを感じやすい",
    Description: "急な依頼・指示への対応が求められる職場。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.STRESS,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.STRESS.ENVIRONMENT,
  },
  /** ハードワーク */
  HardWork: {
    ID: "HardWork",
    Label: "ハードワーク",
    PointHighText:
      "多くの業務をこなすことが求められる職場にストレスを感じやすい",
    PointLowText: "時間を持て余す職場にストレスを感じやすい",
    Description: "多くの業務をこなすことが求められる職場。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.STRESS,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.STRESS.ENVIRONMENT,
  },
  /** 計画性のなさ */
  LackOfPlanning: {
    ID: "LackOfPlanning",
    Label: "計画性のなさ",
    PointHighText: "明確な目標や計画がない職場にストレスを感じやすい",
    PointLowText: "目標や計画をはっきりさせる職場にストレスを感じやすい",
    Description: "明確な目標・計画がない中で業務を遂行する職場。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.STRESS,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.STRESS.ENVIRONMENT,
  },
  /** 厳しい管理 */
  StrictManagement: {
    ID: "StrictManagement",
    Label: "厳しい管理",
    PointHighText:
      "管理が厳しく、指示や命令に従うことを求められる職場にストレスを感じやすい",
    PointLowText:
      "管理されず、自分で考えて動くことを求められる職場にストレスを感じやすい",
    Description: "管理が厳しく、指示や命令に従うことを求められる職場。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.STRESS,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.STRESS.ENVIRONMENT,
  },
  /** 評価の欠如 */
  LackOfEvaluation: {
    ID: "LackOfEvaluation",
    Label: "評価の欠如",
    PointHighText: "成果が評価されない職場にストレスを感じやすい",
    PointLowText: "成果を評価される職場にストレスを感じやすい",
    Description: "仕事の成果や業務に対する取り組み方が評価されない職場。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.STRESS,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.STRESS.ENVIRONMENT,
  },
  /** 主体性が発揮できない */
  InabilityToExerciseInitiative: {
    ID: "InabilityToExerciseInitiative",
    Label: "主体性が発揮できない",
    PointHighText: "自分のやり方で自由に取り組めない職場にストレスを感じやすい",
    PointLowText:
      "依頼や指示がなくやり方を任せられる職場にストレスを感じやすい",
    Description: "自分のやり方で自由に取り組めない職場。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.STRESS,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.STRESS.ENVIRONMENT,
  },
  /** 意思決定に関与できない */
  ExclusionFromDecisionMaking: {
    ID: "ExclusionFromDecisionMaking",
    Label: "意思決定に関与できない",
    PointHighText: "組織の意思決定に関与できない職場にストレスを感じやすい",
    PointLowText: "組織の意思決定に意見を求められる職場にストレスを感じやすい",
    Description: "自分の意見を主張し、組織の意思決定に関与できない職場。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.STRESS,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.STRESS.ENVIRONMENT,
  },
  /** 要求水準が低い */
  LowStandards: {
    ID: "LowStandards",
    Label: "要求水準が低い",
    PointHighText:
      "成果を出しても出さなくても評価が変わらない職場にストレスを感じやすい",
    PointLowText: "成果によって評価が大きく変わる環境にストレスを感じやすい",
    Description: "成果を出しても出さなくても評価が変わらない職場。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.STRESS,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.STRESS.ENVIRONMENT,
  },
  /** 高度な分析 */
  HighAnalysis: {
    ID: "HighAnalysis",
    Label: "高度な分析",
    PointHighText: "高度で複雑な知的業務にストレスを感じやすい",
    PointLowText: "単純な業務にストレスを感じやすい",
    Description: "複雑な物事を考えたり取り扱ったりする業務。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.STRESS,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.STRESS.WORK,
  },
  /** 学習機会の不足 */
  LackOfLearningOpportunities: {
    ID: "LackOfLearningOpportunities",
    Label: "学習機会の不足",
    PointHighText: "学ぶ機会がない業務にストレスを感じやすい",
    PointLowText: "学ぶ機会が多い業務にストレスを感じやすい",
    Description: "学ぶ機会がなく知的好奇心が満たされない業務。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.STRESS,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.STRESS.WORK,
  },
  /** 前例踏襲 */
  FollowingPrecedents: {
    ID: "FollowingPrecedents",
    Label: "前例踏襲",
    PointHighText: "これまで通りのやり方を求められる業務にストレスを感じやすい",
    PointLowText:
      "これまでにない新しい方法で取り組むことを求められる業務にストレスを感じやすい",
    Description:
      "新しいアイデアを自由に出せず、これまで通りのやり方を求められる業務。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.STRESS,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.STRESS.WORK,
  },
  /** 定型業務 */
  RoutineWork: {
    ID: "RoutineWork",
    Label: "定型業務",
    PointHighText: "同じ業務の繰り返しを求められることにストレスを感じやすい",
    PointLowText:
      "次々と新しい業務に取り組むよう求められることにストレスを感じやすい",
    Description: "同じ作業を日常的に繰り返す業務。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.STRESS,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.STRESS.WORK,
  },
  /** 困難な決断 */
  DifficultDecisions: {
    ID: "DifficultDecisions",
    Label: "困難な決断",
    PointHighText:
      "批判されると想定されるなかで決断を強いられることにストレスを感じやすい",
    PointLowText:
      "批判されると想定されるなかで自分では何も決断できないことにストレスを感じやすい",
    Description: "批判されると想定されるなかで決断を強いられる業務。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.STRESS,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.STRESS.WORK,
  },
  /** 交渉業務 */
  NegotiationTasks: {
    ID: "NegotiationTasks",
    Label: "交渉業務",
    PointHighText: "説得・交渉が多い業務にストレスを感じやすい",
    PointLowText: "説得・交渉が少ない業務にストレスを感じやすい",
    Description: "相手への説得・交渉が必要となる業務。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.STRESS,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.STRESS.WORK,
  },
  /** 合意形成 */
  ConsensusBuilding: {
    ID: "ConsensusBuilding",
    Label: "合意形成",
    PointHighText:
      "相手と話し合って合意を得なければならない状況にストレスを感じやすい",
    PointLowText:
      "話し合いをせず自分一人で決めなければならない状況にストレスを感じやすい",
    Description: "相手と話し合って合意を得なければならない状況。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.STRESS,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.STRESS.HUMAN_RELATIONS,
  },
  /** 周囲との対立 */
  ConflictWithOthers: {
    ID: "ConflictWithOthers",
    Label: "周囲との対立",
    PointHighText: "周囲と対立が起きやすい状況にストレスを感じやすい",
    PointLowText: "周囲との協調が求められる状況にストレスを感じやすい",
    Description: "周囲と対立が起きやすい状況。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.STRESS,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.STRESS.HUMAN_RELATIONS,
  },
  /** ドライな職場 */
  DryWorkplace: {
    ID: "DryWorkplace",
    Label: "ドライな職場",
    PointHighText:
      "業務に必要な会話や付き合いしかない職場にストレスを感じやすい",
    PointLowText:
      "業務に関係ない会話や付き合いが多い職場にストレスを感じやすい",
    Description: "業務に必要な会話や付き合いしかない状況。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.STRESS,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.STRESS.HUMAN_RELATIONS,
  },
  /** 板挟み状態 */
  CaughtInTheMiddle: {
    ID: "CaughtInTheMiddle",
    Label: "板挟み状態",
    PointHighText:
      "良くないことでも相手に伝えなければならない立場や状況にストレスを感じやすい",
    PointLowText:
      "相手に都合の悪いことを伝えられない立場や状況にストレスを感じる",
    Description: "良くないことでも相手に伝えなければならない立場や状況。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.STRESS,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.STRESS.HUMAN_RELATIONS,
  },
  /** 共同業務 */
  CollaborativeWork: {
    ID: "CollaborativeWork",
    Label: "共同業務",
    PointHighText: "相手と一緒に業務を進めることにストレスを感じやすい",
    PointLowText: "自分一人で業務を進めることにストレスを感じやすい",
    Description: "相手と一緒に業務を進める状況。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.STRESS,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.STRESS.HUMAN_RELATIONS,
  },
  // 「孤独な業務」は結果表示しない（「共同業務」に統合。ミイダスラップでは引き続き使用する。）
  /** 孤独な業務 */
  SolitaryWork: {
    ID: "SolitaryWork",
    Label: "孤独な業務",
    PointHighText: "",
    PointLowText: "",
    Description: "",
    MainCategory: null,
    SubCategory: null,
  },
  /** 指示型 */
  Directive: {
    ID: "Directive",
    Label: "指示型",
    PointHighText: "傾向が強い",
    PointLowText: "傾向が弱い",
    Description: "部下に細かく指示・指導を行うことができる。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.HIERARCHY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.HIERARCHY.BOSS,
  },
  /** 委任型 */
  Delegation: {
    ID: "Delegation",
    Label: "委任型",
    PointHighText: "傾向が強い",
    PointLowText: "傾向が弱い",
    Description: "部下のやり方に干渉せず、仕事を任せることができる。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.HIERARCHY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.HIERARCHY.BOSS,
  },
  /** 傾聴型 */
  Listening: {
    ID: "Listening",
    Label: "傾聴型",
    PointHighText: "傾向が強い",
    PointLowText: "傾向が弱い",
    Description:
      "自分の意見を押し付けず、部下からの意見や提案を聞くことができる。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.HIERARCHY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.HIERARCHY.BOSS,
  },
  /** 対話型 */
  Dialogue: {
    ID: "Dialogue",
    Label: "対話型",
    PointHighText: "傾向が強い",
    PointLowText: "傾向が弱い",
    Description: "部下と話し合いながら物事を進めることができる。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.HIERARCHY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.HIERARCHY.BOSS,
  },
  /** 交渉型 */
  Negotiation: {
    ID: "Negotiation",
    Label: "交渉型",
    PointHighText: "傾向が強い",
    PointLowText: "傾向が弱い",
    Description:
      "意見や考えが違う部下に対して、説得・交渉しながら働くことができる。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.HIERARCHY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.HIERARCHY.BOSS,
  },
  /** 従順型 */
  Obedient: {
    ID: "Obedient",
    Label: "従順型",
    PointHighText: "傾向が強い",
    PointLowText: "傾向が弱い",
    Description: "上司の意見や考えに従って働くことができる。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.HIERARCHY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.HIERARCHY.MEMBER,
  },
  /** 自律型 */
  Autonomous: {
    ID: "Autonomous",
    Label: "自律型",
    PointHighText: "傾向が強い",
    PointLowText: "傾向が弱い",
    Description: "上司から指示がなくても、自分で考えて行動できる。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.HIERARCHY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.HIERARCHY.MEMBER,
  },
  /** 協調型 */
  Cooperative: {
    ID: "Cooperative",
    Label: "協調型",
    PointHighText: "傾向が強い",
    PointLowText: "傾向が弱い",
    Description: "上司と協力しながら業務を遂行できる。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.HIERARCHY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.HIERARCHY.MEMBER,
  },
  /** 提案型 */
  Proactive: {
    ID: "Proactive",
    Label: "提案型",
    PointHighText: "傾向が強い",
    PointLowText: "傾向が弱い",
    Description: "上司に対して業務に必要な情報を積極的に提案できる。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.HIERARCHY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.HIERARCHY.MEMBER,
  },
  /** 主張型 */
  Assertive: {
    ID: "Assertive",
    Label: "主張型",
    PointHighText: "傾向が強い",
    PointLowText: "傾向が弱い",
    Description: "上司に自分の意見や考えをはっきり伝えることができる。",
    MainCategory: COMPETENCY_ITEM_MAIN_CATEGORY.HIERARCHY,
    SubCategory: COMPETENCY_ITEM_SUB_CATEGORY.HIERARCHY.MEMBER,
  },
} as const;

// カテゴリ「パーソナリティの傾向」サブカテゴリ「マネジメントの傾向」の項目を抽出
export const PERSONALITY_MANAGEMENT_CATEGORY_ITEM_KEYS = getKeys(
  COMPETENCY_ITEM,
).filter((key) => {
  return (
    COMPETENCY_ITEM[key].MainCategory ===
      COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY &&
    COMPETENCY_ITEM[key].SubCategory ===
      COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.MANAGEMENT
  );
});
// カテゴリ「パーソナリティの傾向」サブカテゴリ「取り組み方の傾向」の項目を抽出
export const PERSONALITY_APPROACH_CATEGORY_ITEM_KEYS = getKeys(
  COMPETENCY_ITEM,
).filter((key) => {
  return (
    COMPETENCY_ITEM[key].MainCategory ===
      COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY &&
    COMPETENCY_ITEM[key].SubCategory ===
      COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.APPROACH
  );
});
// カテゴリ「パーソナリティの傾向」サブカテゴリ「環境適応の傾向」の項目を抽出
export const PERSONALITY_ENVIRONMENT_CATEGORY_ITEM_KEYS = getKeys(
  COMPETENCY_ITEM,
).filter((key) => {
  return (
    COMPETENCY_ITEM[key].MainCategory ===
      COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY &&
    COMPETENCY_ITEM[key].SubCategory ===
      COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.ENVIRONMENT
  );
});
// カテゴリ「パーソナリティの傾向」サブカテゴリ「対人関係の傾向」の項目を抽出
export const PERSONALITY_HUMAN_RELATIONS_CATEGORY_ITEM_KEYS = getKeys(
  COMPETENCY_ITEM,
).filter((key) => {
  return (
    COMPETENCY_ITEM[key].MainCategory ===
      COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY &&
    COMPETENCY_ITEM[key].SubCategory ===
      COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.HUMAN_RELATIONS
  );
});
// カテゴリ「パーソナリティの傾向」サブカテゴリ「思考・行動の傾向」の項目を抽出
export const PERSONALITY_ACTION_CATEGORY_ITEM_KEYS = getKeys(
  COMPETENCY_ITEM,
).filter((key) => {
  return (
    COMPETENCY_ITEM[key].MainCategory ===
      COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY &&
    COMPETENCY_ITEM[key].SubCategory ===
      COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.ACTION
  );
});
// カテゴリ「パーソナリティの傾向」サブカテゴリ「成長意欲の傾向」の項目を抽出
export const PERSONALITY_WILL_CATEGORY_ITEM_KEYS = getKeys(
  COMPETENCY_ITEM,
).filter((key) => {
  return (
    COMPETENCY_ITEM[key].MainCategory ===
      COMPETENCY_ITEM_MAIN_CATEGORY.PERSONALITY &&
    COMPETENCY_ITEM[key].SubCategory ===
      COMPETENCY_ITEM_SUB_CATEGORY.PERSONALITY.WILL
  );
});

// カテゴリ「ストレス要因」サブカテゴリ「職場環境要因」の項目を抽出
export const STRESS_ENVIRONMENT_CATEGORY_ITEM_KEYS = getKeys(
  COMPETENCY_ITEM,
).filter((key) => {
  return (
    COMPETENCY_ITEM[key].MainCategory ===
      COMPETENCY_ITEM_MAIN_CATEGORY.STRESS &&
    COMPETENCY_ITEM[key].SubCategory ===
      COMPETENCY_ITEM_SUB_CATEGORY.STRESS.ENVIRONMENT
  );
});
// カテゴリ「ストレス要因」サブカテゴリ「仕事要因」の項目を抽出
export const STRESS_WORK_CATEGORY_ITEM_KEYS = getKeys(COMPETENCY_ITEM).filter(
  (key) => {
    return (
      COMPETENCY_ITEM[key].MainCategory ===
        COMPETENCY_ITEM_MAIN_CATEGORY.STRESS &&
      COMPETENCY_ITEM[key].SubCategory ===
        COMPETENCY_ITEM_SUB_CATEGORY.STRESS.WORK
    );
  },
);
// カテゴリ「ストレス要因」サブカテゴリ「上下関係適性」の項目を抽出
export const STRESS_HUMAN_RELATIONS_CATEGORY_ITEM_KEYS = getKeys(
  COMPETENCY_ITEM,
).filter((key) => {
  return (
    COMPETENCY_ITEM[key].MainCategory ===
      COMPETENCY_ITEM_MAIN_CATEGORY.STRESS &&
    COMPETENCY_ITEM[key].SubCategory ===
      COMPETENCY_ITEM_SUB_CATEGORY.STRESS.HUMAN_RELATIONS
  );
});

// カテゴリ「上司・部下としての傾向」サブカテゴリ「上司としてのタイプ」の項目を抽出
export const HIERARCHY_BOSS_CATEGORY_ITEM_KEYS = getKeys(
  COMPETENCY_ITEM,
).filter((key) => {
  return (
    COMPETENCY_ITEM[key].MainCategory ===
      COMPETENCY_ITEM_MAIN_CATEGORY.HIERARCHY &&
    COMPETENCY_ITEM[key].SubCategory ===
      COMPETENCY_ITEM_SUB_CATEGORY.HIERARCHY.BOSS
  );
});
// カテゴリ「上司・部下としての傾向」サブカテゴリ「部下としてのタイプ」の項目を抽出
export const HIERARCHY_MEMBER_CATEGORY_ITEM_KEYS = getKeys(
  COMPETENCY_ITEM,
).filter((key) => {
  return (
    COMPETENCY_ITEM[key].MainCategory ===
      COMPETENCY_ITEM_MAIN_CATEGORY.HIERARCHY &&
    COMPETENCY_ITEM[key].SubCategory ===
      COMPETENCY_ITEM_SUB_CATEGORY.HIERARCHY.MEMBER
  );
});

// コンピテンシー診断の回答選択肢
export const COMPETENCY_EXAM_OPTIONS = [
  {
    ID: 0,
    VALUE: "わからない",
  },
  {
    ID: 1,
    VALUE: "まったく\n当てはまらない",
  },
  {
    ID: 2,
    VALUE: "あまり\n当てはまらない",
  },
  {
    ID: 3,
    VALUE: "どちらかというと\n当てはまらない",
  },
  {
    ID: 4,
    VALUE: "どちらとも\nいえない",
  },
  {
    ID: 5,
    VALUE: "どちらかというと\n当てはまる",
  },
  {
    ID: 6,
    VALUE: "まあまあ\n当てはまる",
  },
  {
    ID: 7,
    VALUE: "とても当てはまる",
  },
];

// コンピテンシー診断の所要時間（分）
export const COMPETENCY_EXAM_MINUTES = {
  PART1: 12, // 第一部
  PART2: 8, // 第二部
  TOTAL: 20, // 全体
};
