package master

import (
	"strconv"

	"github.com/samber/lo"

	"aica/api/sdk/vo"
)

type (
	JobTypeSmallID int32

	// Deprecated: メソッドもないので型不要
	JobTypeSmallIDs []JobTypeSmallID

	// JobTypeSmall 職種小分類
	JobTypeSmall struct {
		ID              JobTypeSmallID  // ID
		JobTypeMiddleID JobTypeMiddleID // 職種中分類ID
		Name            string          // 名前
		RecommendID     *int            // レコメンID
		SortOrder       int
	}

	JobTypeSmalls   list[JobTypeSmallID, JobTypeSmall]
	JobTypeSmallMap Map[JobTypeSmallID, JobTypeSmall]
)

func (j JobTypeSmall) TableName() string {
	return "master.job_type_small"
}

func (j JobTypeSmall) IntIDNamePair() *vo.IntIDNamePair {
	return vo.NewIntIDNamePair(j.ID, j.Name)
}

// JobTypeLargeID 職種小に紐づく職種大分類IDを取得
func (id JobTypeSmallID) JobTypeLargeID() JobTypeLargeID {
	return JobTypeLargeID(id / 10000)
}

// JobTypeMiddleID 職種小に紐づく職種中分類IDを取得
func (id JobTypeSmallID) JobTypeMiddleID() JobTypeMiddleID {
	return JobTypeMiddleID(id / 100)
}

func (id JobTypeSmallID) String() string {
	return strconv.Itoa(int(id))
}

func (j JobTypeSmall) GetID() JobTypeSmallID {
	return j.ID
}

func (j JobTypeSmall) GetName() string {
	return j.Name
}

func (js JobTypeSmalls) IDs() []JobTypeSmallID {
	if js == nil {
		return []JobTypeSmallID{}
	}

	return lo.Map(js, func(j *JobTypeSmall, _ int) JobTypeSmallID { return j.ID })
}

func (js JobTypeSmalls) ToMap() JobTypeSmallMap {
	return JobTypeSmallMap(list[JobTypeSmallID, JobTypeSmall](js).ToMap())
}

func (jm JobTypeSmallMap) Get(id JobTypeSmallID) (*JobTypeSmall, bool) {
	return Map[JobTypeSmallID, JobTypeSmall](jm).Get(id)
}

func (jm JobTypeSmallMap) IDNamePairs(ids []JobTypeSmallID) []vo.IDNamePair[JobTypeSmallID] {
	return lo.Map(ids, func(id JobTypeSmallID, _ int) vo.IDNamePair[JobTypeSmallID] {
		name := ""
		if j, found := jm[id]; found {
			name = j.Name
		}
		return *vo.NewIDNamePair(id, name)
	})
}
