package master

// SpotJobRequestID スポット依頼内容ID
type SpotJobRequestID int

// SpotJobRequest スポット依頼内容
type SpotJobRequest struct {
	ID                    SpotJobRequestID    // ID
	Name                  string              // 依頼内容
	SpotJobRequestGenreID string              // ジャンルID
	Category              string              // カテゴリ
	SpotExpLevelPattern   SpotExpLevelPattern // 熟練度パターン
}

func (s SpotJobRequest) GetID() SpotJobRequestID {
	return s.ID
}

// TableName .
func (s SpotJobRequest) TableName() string {
	return "master.spot_job_request"
}

type (
	SpotJobRequests   = list[SpotJobRequestID, SpotJobRequest]
	SpotJobRequestMap = Map[SpotJobRequestID, SpotJobRequests]
)
