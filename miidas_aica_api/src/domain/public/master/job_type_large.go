package master

import (
	"database/sql/driver"
	"strconv"

	"github.com/samber/lo"

	"aica/api/sdk/gormio/serializer"
	"aica/api/sdk/vo"
)

type (
	JobTypeLargeID int16

	// JobTypeLarge 職種大分類
	JobTypeLarge struct {
		ID                   JobTypeLargeID // ID
		Name                 string         // 名前
		JobTypeAppealGroupID string         // 職種グループID
		Description          *string        // 説明
		Group                int            // グループ
		SortOrder            int
	}

	JobTypeLarges   list[JobTypeLargeID, JobTypeLarge]
	JobTypeLargeMap Map[JobTypeLargeID, JobTypeLarge]
)

// 職種大分類ID定数
const (
	JobTypeLargeIDFinancialSpecialist JobTypeLargeID = 17 // 金融専門職
	JobTypeLargeIDITSpecialist        JobTypeLargeID = 22 // IT専門職
)

func (j JobTypeLarge) TableName() string {
	return "master.job_type_large"
}

func (j JobTypeLarge) IntIDNamePair() *vo.IntIDNamePair {
	return vo.NewIntIDNamePair(j.ID, j.Name)
}

func (j JobTypeLarge) GetID() JobTypeLargeID {
	return j.ID
}

func (id JobTypeLargeID) String() string {
	return strconv.Itoa(int(id))
}

func (id JobTypeLargeID) Value() (driver.Value, error) {
	return serializer.JobIDValue(id)
}

func (id *JobTypeLargeID) Scan(value any) error {
	return serializer.JobIDScan(id, value)
}

func (id *JobTypeLargeID) UnmarshalJSON(value []byte) error {
	return serializer.JobIDUnmarshalJSON(id, value)
}

func (id JobTypeLargeID) MarshalJSON() ([]byte, error) {
	return serializer.JobIDMarshalJSON(id)
}

func (jl JobTypeLarges) ToMap() JobTypeLargeMap {
	return JobTypeLargeMap(list[JobTypeLargeID, JobTypeLarge](jl).ToMap())
}

func (jm JobTypeLargeMap) Get(id JobTypeLargeID) (*JobTypeLarge, bool) {
	return Map[JobTypeLargeID, JobTypeLarge](jm).Get(id)
}

func (jm JobTypeLargeMap) IDNamePairs(ids []JobTypeLargeID) []vo.IDNamePair[JobTypeLargeID] {
	return lo.Map(ids, func(id JobTypeLargeID, _ int) vo.IDNamePair[JobTypeLargeID] {
		name := ""
		if j, found := jm[id]; found {
			name = j.Name
		}
		return *vo.NewIDNamePair(id, name)
	})
}
