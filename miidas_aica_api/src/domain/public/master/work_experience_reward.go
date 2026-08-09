package master

const (
	workExperienceRewardIDNoSettings WorkExperienceRewardID = 0 // 未設定
	workExperienceRewardIDNoReward   WorkExperienceRewardID = 1 // 報酬なし
	workExperienceRewardIDReward     WorkExperienceRewardID = 2 // 報酬あり
)

type (
	WorkExperienceRewardID int

	WorkExperienceReward struct {
		ID        WorkExperienceRewardID
		Name      string
		SortOrder int
	}

	WorkExperienceRewards   = list[WorkExperienceRewardID, WorkExperienceReward]
	WorkExperienceRewardMap = Map[WorkExperienceRewardID, WorkExperienceReward]
)

func (w WorkExperienceReward) TableName() string {
	return "master.work_experience_reward"
}

func (w WorkExperienceReward) GetID() WorkExperienceRewardID {
	return w.ID
}

func (w WorkExperienceRewardID) IsReward() bool {
	return w == workExperienceRewardIDReward
}
