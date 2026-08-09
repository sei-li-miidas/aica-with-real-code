package jobtype

const (
	DEFAULT_MIN_NATURE_SCORE   float32 = 1.0 // 最低の性質スコア（最低は0.0）
	DEFAULT_MIN_JOB_TYPE_SCORE float32 = 0.4 // 最低の類似度スコア（ミイダス職種vsJobTag職務）

	// Jobtagの職業の必要な実務経験の除外スコア
	// 　入植前に必要な実務経験値を0.0〜1.0で表現しているデータ
	// 　が存在する（IPD_04_08_001）。
	// 　その値の範囲は0.0〜1.0（0に近いほど実務経験不要という意味）。
	// 　この設定値を超えると除外される（つまりこれより実務経験
	// 　が必要とされているのであれば除外される）。
	DEFAULT_MAX_PRIOR_EXPERIENCE_REQUIRED float32 = 0.5

	// Jobtagの性質から除外するスコア
	// 　避けたい性質と希望する性質を同時に設定した場合、
	// 　このスコア以上だと希望する性質のスコアが高くても、
	// 　除外する（避けたい性質は絶対にやりたくないものとする）
	DEFAULT_NATURE_EXCLUDE_SCORE_THRESHOLD float32 = 2.5
)
