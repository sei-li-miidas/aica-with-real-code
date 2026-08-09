export const BIAS_GAME_NAVIGATION = {
  INDEX: "/bias_game", // バイアス診断ゲーム 同意画面
  RESULT: "/bias_game/result", // バイアス診断ゲーム 結果画面
};

export const BIAS_GAME_EXAM_STATUS = {
  NOT_TAKEN: 0, // 未受験
  IN_PROGRESS: 1, // 受験中
  FINISHED: 2, // 受験済み
};

// バイアス診断ゲームのベースリンク
export const SECRET_BIAS_GAME_BASE_LINK = "/bias/game/index.html?groupId=";

// バイアス診断ゲーム結果のカテゴリー
export const BIAS_GAME_RESULT_CATEGORY = {
  // 回避したい状況
  EMOTION_BIAS_CONTROL_SITUATIONAL_TRENDS: {
    ID: "emotionBiasControlSituationalTrends",
    Note: "回避したい状況の違いによって、感情やバイアスの強さに傾向があるか",
  },
  // 自己と他者の影響
  EMOTION_BIAS_CONTROL_RANGE_OF_INFLUENCE: {
    ID: "emotionBiasControlRangeOfInfluence",
    Note: "影響範囲が自分のみか、他者に及ぶか、その違いによって感情やバイアスの制御力に傾向があるか",
  },
};

// バイアス診断ゲーム結果の各項目のキー
export const BIAS_GAME_RESULT_KEY = {
  FRAMING_EFFECT: "FramingEffect", // フレーミング効果
  STATUS_QUO: "StatusQuo", // 現状維持バイアス
  SUNK_COST: "SunkCost", // サンクコスト効果
  IMPATIENCE: "Impatience", // 時間選好(せっかち度)
  IMPULSE_CONTROL: "ImpulseControl", // 衝動制御
  PREDICTIVE_BEHAVIOR: "PredictiveBehavior", // 予測態度
  RISK_TOLERANCE: "RiskTolerance", // リスク許容度
  ALTRUISM_SELFISHNESS_EVALUATION: "AltruismSelfishnessEvaluation", // 利他性・利己性の10段階評価
  ALTRUISM_SELFISHNESS_TYPE: "AltruismSelfishnessType", // 利他性・利己性のタイプ
  DIVIDED_ATTENTION: "DividedAttention", // 全体的注意
  FOCUSED_ATTENTION: "FocusedAttention", // 焦点的注意
  NEGATIVE_EMOTIONS: "NegativeEmotions", // 否定的感情
  CONFORMITY: "Conformity", // 同調度
  EMPATHY: "Empathy", // 共感性
  ENDS_MEANS: "EndsMeans", // 目的思考
  BIAS_CONTROL: "BiasControl", // バイアス制御
  DECLINE_EVALUATION_AVERSION: "DeclineEvaluationAversion", // 評価下落回避
  LOSS_AVERSION: "LossAversion", // 損失回避
  EFFORT_AVERSION: "EffortAversion", // 労力回避
  REGRET_AVERSION: "RegretAversion", // 失敗回避
  RANGE_MYSELF: "RangeMyself", // 個人要因バイアス
  RANGE_OTHERS: "RangeOthers", // 他人要因バイアス
  PURPOSE_OF_WORK: "PurposeOfWork", // 仕事の目的 ※バック側には存在しない
  PURPOSE_OF_WORK_1: "PurposeOfWork1", // 仕事の目的1
  PURPOSE_OF_WORK_2: "PurposeOfWork2", // 仕事の目的2
};

// バイアス診断ゲーム結果の各項目
// Todo: ラベルのFix待ち。
export const BIAS_GAME_RESULT_ITEM = {
  [BIAS_GAME_RESULT_KEY.FOCUSED_ATTENTION]: {
    Label: "焦点注意",
    PointLowText: "細部にこだわることが苦手である",
    PointHighText: "細部にこだわることが得意である",
    LowCharacteristic:
      "細部にこだわらず、どちらかと言えば全体を俯瞰する仕事や抽象度の高い仕事を好む。",
    HighCharacteristic:
      "細部にこだわることが得意である一方で、細部（例：クオリティー）に目を向けるあまり、他の要素（例：納期・コストなど）を度外視してしまう傾向がある。",
    LowDescription:
      "求められている基準を正しく理解し、最低限それを満たす必要があることを意識しましょう。",
    HighDescription:
      "仕事において細部（例：クオリティー）にばかり固執せず、他の要素（例：コスト・納期など）も意識するよう心がけましょう。",
    Note: "多くの情報から必要な情報を選択する際、全体よりも細部にこだわって意思決定を行う働き",
  },
  [BIAS_GAME_RESULT_KEY.DIVIDED_ATTENTION]: {
    Label: "全体注意",
    PointLowText: "全体を俯瞰することが苦手である",
    PointHighText: "全体を俯瞰することが得意である",
    LowCharacteristic:
      "全体を俯瞰することは苦手である一方で、細部にこだわることができる。",
    HighCharacteristic:
      "全体を俯瞰することは得意である一方で、細部がおろそかになる場合もある。",
    LowDescription:
      "重要な意思決定を行う際は、一度立ち止まり、全体を俯瞰できているか自問自答してみましょう。",
    HighDescription:
      "全体に目を向けるあまり、細部がおろそかにならないよう注意しましょう。",
    Note: "多くの情報から必要な情報を選択する際、全体を俯瞰した上で意思決定を行う働き",
  },
  [BIAS_GAME_RESULT_KEY.ENDS_MEANS]: {
    Label: "目的思考",
    PointLowText: "手段を重視する",
    PointHighText: "目的を重視する",
    Characteristic:
      "たとえば「売上目標を達成するためにはイノベーション（革新）が必要だ」と言われた場合、",
    LowCharacteristic:
      "手段であるイノベーションを重視し、どうやったらイノベーションを生み出せるのか考える。",
    HighCharacteristic:
      "目的である売上目標達成を重視し、イノベーションも含めた達成方法を考える。",
    LowDescription:
      "作業や議論の目的は何なのか、常に意識する癖をつけましょう。また、仕事を依頼された場合は、その仕事の目的を確認することが大切です。そうすれば無駄が減り、スムーズに仕事が進みます。また、自分で何か意思決定する際にも、それは目的なのか、手段なのか意識して考えるようにしましょう。",
    HighDescription:
      "自分が作業を依頼する立場になったとき、作業者の中には手段を目的化してしまう人がいることを理解し、目的を明確に伝えることを習慣化しましょう。",
    Note: "目的を重視するか、手段を重視するか",
  },
  [BIAS_GAME_RESULT_KEY.ALTRUISM_SELFISHNESS_EVALUATION]: {
    Label: "協力行動",
    PointLowText: "相手より自分の利益を優先する",
    PointHighText: "相手と自分の利益を優先する",
    Characteristic: "協力行動は3つのタイプに分類されます。",
    CharacteristicType: {
      A: "相手が誰でも、相手と自分の両者の利益を優先するタイプ（29.7％）",
      B: "相手が信頼できる場合のみ、相手と自分の両者の利益を優先するタイプ（25.7％）",
      C: "相手が誰でも、相手より自分の利益を優先するタイプ（44.6％）",
    },
    DescriptionType: {
      A: "どんな相手にも協力するよう働きかけることで、両者の利益を最大化できる可能性があります。ただし、相手の出方を見極めた上で判断するように気をつけましょう。",
      B: "知らない相手を理解しようとすること、非協力的な相手に協力するよう働きかけることで、両者の利益を最大化できる可能性があります。意識してみましょう。",
      C: "両者の利益の最大化を目指すことで、最終的には自分の利益も最大化される事例が増えてきています。意識してみましょう。",
    },
    Note: "集団内で行動する時の利益に対する考え方",
    // AltruismSelfishnessTypeの値をキー(ID)として取得
    Values: [
      {
        ID: 1,
        Type: "A",
        Label: "相手が誰でも、相手と自分の両者の利益を優先する",
      },
      {
        ID: 2,
        Type: "B",
        Label: "相手が信頼できる場合のみ、相手と自分の両者の利益を優先する",
      },
      {
        ID: 3,
        Type: "C",
        Label: "相手が誰でも、相手より自分の利益を優先する",
      },
    ],
  },
  [BIAS_GAME_RESULT_KEY.EMPATHY]: {
    Label: "共感性",
    PointLowText: "他者への共感性が低い",
    PointHighText: "他者への共感性が高い",
    LowCharacteristic:
      "他者の感情により影響を受けにくい人。たとえば、悩みを相談されても何が辛いのかわからなかったり、興味がないと思ってしまう。また、映画やドラマで可哀想なシーン、辛いシーンがあっても何とも思わない。",
    HighCharacteristic:
      "他者の感情により影響を受けやすい人。たとえば、悩みを相談されると自分のことのように心が痛んだり、映画やドラマで可哀想なシーン、辛いシーンがあると涙する。",
    LowDescription:
      "人からの信頼を得るには、相手に共感すること、そしてそれを相手に伝えることが重要です。表情や仕草、言葉を使って「共感している」ということを伝えてみましょう。",
    HighDescription:
      "共感は、相手からの信頼を得るために重要な要素の一つです。ただし、共感するあまりあなた自身の目的を見失わないように気をつけましょう。",
    Note: "他者への共感、同情、感情移入のしやすさ",
  },
  [BIAS_GAME_RESULT_KEY.PREDICTIVE_BEHAVIOR]: {
    Label: "予測態度",
    PointLowText: "不確かな状況において、衝動や感情を優先して行動しようとする",
    PointHighText:
      "不確かな状況においても冷静に思考し、物事や状況の規則性、法則性を把握・予測しようとする",
    LowCharacteristic:
      "衝動、感情、想いを重視して行動する積極派タイプ。起業家や経営者に多い。",
    HighCharacteristic: "予測や計画性を重視して行動する慎重派タイプ。",
    Description:
      "精度の高い予測や計画を立てることは重要ですが、変化が激しく、複雑で予測困難な時代においては難しい場合も。予測の手がかりがない状況でも行動する力が求められています。\n状況に応じて適切に判断するためにも、まずは自分が「慎重派」「積極派」どちらのタイプかを把握し、日々の意思決定で気を付けてみましょう。",
    Note: "不確かで見通しの悪い状況においても冷静に思考し、規則性や法則性を把握・予測しようとする態度",
  },
  [BIAS_GAME_RESULT_KEY.CONFORMITY]: {
    Label: "同調度",
    PointLowText: "意思決定の際、周囲の意見に影響を受けにくい",
    PointHighText: "意思決定の際、周囲の意見に大きく影響されやすい",
    LowCharacteristic:
      "周囲の意見よりも自分の信念に則って行動することを好むが、時として他者の意見を受け入れない意固地な人に見られてしまうこともある。",
    HighCharacteristic:
      "周囲から嫌われたり孤立することを恐れ、「周りに合わせれば安全」という心理が働きやすい。",
    LowDescription:
      "大きな意思決定を行うときには、周囲の意見も意識的に聞いてみると良いでしょう。",
    HighDescription:
      "大きな意思決定を行うときには、自分が周囲の意見に影響を受けやすいタイプであることを意識しましょう。",
    Note: "意思決定を行う際、周囲の言動から影響を受ける度合い",
  },
  [BIAS_GAME_RESULT_KEY.IMPULSE_CONTROL]: {
    Label: "衝動制御",
    PointLowText: "衝動をセルフコントロールする力が弱い",
    PointHighText: "衝動をセルフコントロールし行動しようとする",
    LowCharacteristic:
      "衝動・行動のセルフコントロールは苦手。その一方、好奇心旺盛で新しいチャレンジを好み、並行していくつものことに対応するマルチタスクが得意な人や自由な発想力、創造力が高い人もいる。",
    HighCharacteristic:
      "目的を達成するために、衝動・行動をセルフコントロールしながら集中力を持続できる。",
    LowDescription:
      "持ち前の好奇心やチャレンジ精神を活かして行動しましょう。ただし、衝動に駆られて物事を途中で放置したり、事後処理を他人に任せることがないように注意が必要です。",
    HighDescription:
      "セルフコントロールを行い集中力を持続すること（衝動抑制）が苦手な人もいますが、その中には好奇心旺盛で、新しいチャレンジを好み、並行していくつものことに対応するマルチタスクが得意な人もいます。周囲にそのような人がいた場合は、それを理解し、得意なところを活かせるようサポートしてみましょう。",
    Note: "自分の衝動をセルフコントロールし、集中力を持続させること",
  },
  [BIAS_GAME_RESULT_KEY.FRAMING_EFFECT]: {
    Label: "フレーミング効果",
    PointLowText:
      "表現方法が変わっても同じ情報であれば意思決定に影響は受けにくい",
    PointHighText:
      "同じ情報でも表現方法が変わることで意思決定に影響を受けやすい",
    Characteristic:
      "たとえば、自分が就職したい会社について、「100人応募すると10人採用される」「100人応募すると90人が不採用になる」という2つの情報が与えられたとする。",
    LowCharacteristic:
      "どちらの情報を与えられても、自分の意思決定を変えることがない。",
    HighCharacteristic:
      "同じことを言っているにもかかわらず、前者の情報を与えられると応募し、後者の情報を与えられると諦めることがある。",
    Description:
      "表現方法や伝え方が変わると、同じ情報でも印象が変わり、意思決定に影響を及ぼすことがあります。まずはこの事実を認識しましょう。\n自分が情報を受け取る側の場合、伝えられ方により意思決定が変わる可能性があることを認識し、表現の装飾に惑わされないよう気をつけましょう。一方で、自分が情報を発する側の場合は、このフレーミング効果を効果的に活用しましょう。",
    Note: "表現方法によって判断が変わりやすいかどうか",
  },
  [BIAS_GAME_RESULT_KEY.STATUS_QUO]: {
    Label: "現状維持",
    PointLowText: "既知や未知、体験の有無を問わず、フラットに意思決定する",
    PointHighText:
      "現状維持が選択肢に含まれる場合、未知・未体験である選択肢よりも現状維持を選ぶ傾向にある",
    LowCharacteristic:
      "「大きな問題はない現状のやり方を継続する」または「より改善できる可能性のある新しいやり方に変える」という判断を迫られた場合、現状に固執せず新しいやり方を選択する傾向がある。",
    HighCharacteristic:
      "「大きな問題はない現状のやり方を継続する」または「より改善できる可能性のある新しいやり方に変える」という判断を迫られた場合、現状維持を選択する傾向がある。",
    LowDescription:
      "周囲には、やり方を変えずに現状維持を好む人の方が多いことを理解しましょう。",
    HighDescription:
      "難しい判断を求められた場合、現状維持を優先していないか、現状維持を選択する理由を探していないか意識してみましょう。",
    Note: "未知のものや未体験のものを受け入れたくないと感じ、現状維持を望みやすい心理効果",
  },
  [BIAS_GAME_RESULT_KEY.RANGE_MYSELF]: {
    Label: "自分の好み",
    PointLowText: "感情やバイアスの制御が苦手",
    PointHighText: "感情やバイアスの制御が得意",
    LowCharacteristic:
      "目的の達成よりも、自分の好み、感情、負担の影響を優先させて行動するタイプ",
    HighCharacteristic:
      "自分の好み、感情、負担に影響されず目的の達成に向けた行動をとるタイプ",
    LowDescription:
      "自分の好みや感情で選ぶ行動と目的の達成のために必要な行動が一致しているかを意識しましょう。もしも両者にズレがあるならどちらを優先すべきかを落ち着いて考えましょう。",
    HighDescription:
      "自分の好みや感情だけに流されずに目的達成のための行動を取れる傾向にあります。好みや感情を押さえ込むことで不満を溜め込みすぎないように同僚などと会話するなどしてみましょう。",
    Note: "自分の好みに関係した感情やバイアスの制御",
    Category:
      BIAS_GAME_RESULT_CATEGORY.EMOTION_BIAS_CONTROL_RANGE_OF_INFLUENCE.ID,
  },
  [BIAS_GAME_RESULT_KEY.RANGE_OTHERS]: {
    Label: "他者の評価",
    PointLowText: "感情やバイアスの制御が苦手",
    PointHighText: "感情やバイアスの制御が得意",
    LowCharacteristic:
      "自分に対する他者からの評価に影響がある場合、目的遂行よりも評価を優先する傾向がある。",
    HighCharacteristic:
      "自分に対する他者からの評価に影響がある場合でも、気にせず目的遂行を優先する。",
    LowDescription:
      "自分に対する他者の評価があると、いつの間にか本来の目的からそれた行動を取ってしまっているかもしれません。他者から評価を得られる行動と元々の目的達成のための行動が一致しているかを意識してみましょう。それらが一致しない場合には、目先の評価ばかりを優先しすぎないことを心がけましょう。",
    HighDescription:
      "他者からの評価にとらわれない姿勢は良いことですが、その態度を面白く思わない人がいたり、攻撃される場合があるかもしれません。他者との良好な関係づくりに注意してみましょう。",
    Note: "他者の評価に関係した感情やバイアスの制御",
    Category:
      BIAS_GAME_RESULT_CATEGORY.EMOTION_BIAS_CONTROL_RANGE_OF_INFLUENCE.ID,
  },
  [BIAS_GAME_RESULT_KEY.DECLINE_EVALUATION_AVERSION]: {
    Label: "評価下落回避",
    PointLowText: "他者の評価を気にしない",
    PointHighText: "他者の評価を気にする",
    HighCharacteristic:
      "他者からの評価を下げたくないという感情を優先して意思決定する傾向がある",
    HighDescription:
      "「他者の評価を下げないこと」が目的にすり替わってしまっているかもしれません。他者の評価を上げるよりも優先すべき目的はないのか、常に確認することを心がけましょう。",
    Note: "他者からの評価に対する感度",
    Category:
      BIAS_GAME_RESULT_CATEGORY.EMOTION_BIAS_CONTROL_SITUATIONAL_TRENDS.ID,
  },
  [BIAS_GAME_RESULT_KEY.REGRET_AVERSION]: {
    Label: "失敗回避",
    PointLowText: "失敗を気にしない",
    PointHighText: "失敗しないことを優先する",
    HighCharacteristic:
      "失敗をしたくないという感情を優先して意思決定する傾向がある",
    HighDescription:
      "「失敗を回避すること」が目的にすり替わってしまっているかもしれません。失敗を回避するよりも優先すべき目的はないのか、常に確認することを心がけましょう。",
    Note: "失敗に対する感度",
    Category:
      BIAS_GAME_RESULT_CATEGORY.EMOTION_BIAS_CONTROL_SITUATIONAL_TRENDS.ID,
  },
  [BIAS_GAME_RESULT_KEY.EFFORT_AVERSION]: {
    Label: "労力回避",
    PointLowText: "労力の投資に抵抗がない",
    PointHighText: "労力の投資に慎重",
    HighCharacteristic:
      "なるべく労力をかけたくないという感情を優先して意思決定する傾向がある",
    HighDescription:
      "「労力をかけないこと」が目的にすり替わってしまっているかもしれません。労力を最小限に抑えるよりも優先すべき目的はないのか、常に確認することを心がけましょう。",
    Note: "労力に対する感度",
    Category:
      BIAS_GAME_RESULT_CATEGORY.EMOTION_BIAS_CONTROL_SITUATIONAL_TRENDS.ID,
  },
  [BIAS_GAME_RESULT_KEY.LOSS_AVERSION]: {
    Label: "損失回避",
    PointLowText: "損失よりも利益を優先する",
    PointHighText: "損失回避を優先する",
    HighCharacteristic:
      "損をしたくないという感情を優先して意思決定する傾向がある",
    HighDescription:
      "「損失を生まないこと」が目的にすり替わってしまっているかもしれません。損失の回避よりも優先すべき目的はないのか、常に確認することを心がけましょう。",
    Note: "損失に対する感度",
    Category:
      BIAS_GAME_RESULT_CATEGORY.EMOTION_BIAS_CONTROL_SITUATIONAL_TRENDS.ID,
  },
  [BIAS_GAME_RESULT_KEY.NEGATIVE_EMOTIONS]: {
    Label: "否定的感情",
    PointLowText: "物事に対して否定的な感情になりにくい",
    PointHighText: "物事に対して否定的な感情を抱きやすい",
    LowCharacteristic:
      "相手の表情や仕草をあまり気にせず、肯定的な感情で解釈しやすい傾向がある。",
    HighCharacteristic:
      "相手の表情や仕草を気にしすぎるあまり、否定的な感情で解釈しやすい。一方、何事にも慎重で、疑い深いゆえに物事を多面的に見る傾向がある。",
    LowDescription:
      "周囲には、過度に否定的な解釈をしやすいタイプもいます。あなたの何気ない表情や仕草、言葉にも過敏に反応する人もいるので気をつけましょう。",
    HighDescription:
      "自分が物事に対して否定的な解釈をしやすいタイプであることを自覚しましょう。解釈に迷ったときは、考え過ぎている可能性もあるため、肯定的な解釈を意識することが大切です。",
    Note: "物事に対するネガティブな感情の抱きやすさ",
  },
  [BIAS_GAME_RESULT_KEY.IMPATIENCE]: {
    Label: "現在志向",
    PointLowText: "「現在の価値」を高く感じにくい",
    PointHighText: "「現在の価値」を高く感じやすい",
    LowCharacteristic:
      "「将来の価値」を高く評価するため、一貫性や客観性、合理性があり、長期的な目標を立てて計画通りに実行することが得意。その一方で、今しかない貴重な機会を損失する可能性があるとも言える。",
    HighCharacteristic:
      "「現在の価値」を高く評価し優先するため、長期的な目標に対して計画通りに実行することが苦手。その一方で、今しかない貴重な機会を逃さずに実行に移せる可能性があるとも言える。",
    Description:
      "変化が激しく予測困難で、長期的な目標を立てづらい時代においては、状況に応じて長期的視点・短期的視点の両方を使いこなす必要があります。そのためにも、まずは自分の現在志向を把握し、重要な意思決定をする際に注意する必要があります。\nまた、物事の価値は、状況やタイミングによって変動します。仕事においても「現在」という価値が、その対象の価値そのものに大きく影響を与えることも珍しくありません。物事の価値を正しく見極めるには、時間軸を考慮することは重要ですが難しくもあります。適切に判断するためにも、自分が「現在の価値」を高く感じる傾向にあるか、そうではないのか、自分の現在思考を把握しておきましょう",
    Note: "物事には「現在の価値」と「将来の価値」があり、本質的には同じ価値だとしても、先々の価値より、目に見える「現在の価値」を高く評価する度合い（将来の価値を低く評価する度合い）。",
  },
  [BIAS_GAME_RESULT_KEY.RISK_TOLERANCE]: {
    Label: "リスク許容度",
    PointLowText: "リスクをとることに抵抗がある",
    PointHighText: "リスクをとることに抵抗がない",
    LowCharacteristic:
      "リスクがある選択を迫られた場合、リターンよりも損失を警戒し、リスクを避けた選択をする傾向がある。",
    HighCharacteristic:
      "リスクがある選択を迫られた場合、リターンを優先し、積極的にリスクをとる傾向がある。ドキドキ感やスリルを優先した選択を好む。",
    Description:
      "リスク許容度は「リスクに対して鈍感か、敏感か」を示しています。必要以上にリスクを取ることも、必要以上にリスクを拒絶することも望ましくありません。自らのリスク許容度に振り回されることなく、適切にリスクとリターンを見極めることが大切です。合理的な意思決定をするためにも、まずは自分のリスク許容度について知っておきましょう。",
    Note: "リスクをとることに対する許容度",
  },
  [BIAS_GAME_RESULT_KEY.BIAS_CONTROL]: {
    Label: "感情・バイアス制御",
    PointLowText: "シチュエーションに応じた合理的な意思決定が苦手",
    PointHighText: "シチュエーションに応じた合理的な意思決定が得意",
    Characteristic:
      "たとえば、「年々上昇していく給与体系A」と「年々減少していく給与体系B」（在籍期間中に受け取る給与総額は、AとBで同額とする）のどちらかを選択できるとする。",
    LowCharacteristic:
      "感情やバイアスを優先して意思決定をする。上記の例では、「給与は上がるもの」という常識や「自分が頑張ったのに給与が下がっていく」ことへの否定的感情から、合理的ではないAを選択する。",
    HighCharacteristic:
      "感情やバイアスを制御して意思決定をする。上記の例では、会社の倒産リスク、自分が数年後体調不良になるかもしれない健康リスク、資産運用資金として使える金額、といった点を考えて給与Bを選択する。",
    LowDescription:
      "自分の感情・バイアス制御を自覚しましょう。苦手な方、気をつけたい方は、重要な意思決定の際に、感情やバイアスを制御できる人の話を聞くなどして冷静に判断することをおすすめします。",
    Note: "感情やバイアスを制御して意思決定できるかどうか",
  },
  [BIAS_GAME_RESULT_KEY.PURPOSE_OF_WORK]: {
    Label: "職場における価値基準",
    Description:
      "職場の上司・部下・同僚は、一人ひとり価値基準が異なります。共に働く仲間の価値基準を理解することは、円滑なコミュニケーションや良好な関係構築、人材配置、組織の生産性を考える上でとても重要です。",
    Note: "現在の職場で重要視していること",
    // PurposeOfWork1,PurposeOfWork2の値をキー(ID)として取得
    Values: [
      {
        ID: 1,
        Label: "自分の役割責任を果たすこと",
      },
      {
        ID: 2,
        Label: "自分の報酬、役職、権限などを高めること",
      },
      {
        ID: 3,
        Label: "自分にとって働きやすい環境（仕事内容や人間関係など）にすること",
      },
      {
        ID: 4,
        Label: "自分の人生における自己実現を果たすこと",
      },
      {
        ID: 5,
        Label: "会社、事業、組織の利益（業績や成果指標）を追求すること",
      },
      {
        ID: 6,
        Label: "評価者からの自分の評価を高めること",
      },
      {
        ID: 7,
        Label: "所属組織の良好な人間関係、平等を守ること",
      },
      {
        ID: 8,
        Label: "所属組織のロイヤリティ、一体感を高めること",
      },
    ],
  },
  [BIAS_GAME_RESULT_KEY.SUNK_COST]: {
    Label: "サンクコスト効果",
    PointLowText:
      "過去投資したリソース（金、時間、労力）に影響されにくく、切り替えが早い。目的や手段を変えることに抵抗なく取り組める。",
    PointHighText:
      "過去投資したリソース（金、時間、労力）に影響されやすく、切り替えに時間がかかる。目的や手段を変えることに抵抗を感じる。",
    LowCharacteristic:
      "これまでの取り組みや投資がうまくいかないと分かると、すぐに撤退し、次の取り組みに移る。",
    HighCharacteristic:
      "これまでの取り組みや投資がうまくいかないと分かっても、「せっかく今までやってきたことだから活かしたい、挽回したい」と考え、固執する。",
    Description:
      "物事がうまくいかない場合、固執しすぎずに次の取り組みに移ることが望ましい一方で、すぐに諦めることで機会損失になってしまうことも。本当にうまくいかないのかを検証しきることが重要です。自分のサンクコスト効果を把握しておき、意思決定の精度を高めていきましょう。",
    Note: "過去にリソース（金・時間・労力）を投資したが、すでに回収不可能な状態に陥っており、これ以上継続すれば損失拡大の可能性が高いと分かっていながらも、投資を継続してしまう心理効果",
  },
};
