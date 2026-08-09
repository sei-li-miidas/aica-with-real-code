package master

import "aica/api/sdk/vo"

type (
	LangLevelID int
	// LangLevel 語学レベル
	LangLevel struct {
		ID          LangLevelID // ID
		Name        string      // 名前
		Description string      // 説明
		SortOrder   int
	}

	LangLevels   = list[LangLevelID, LangLevel]
	LangLevelMap = Map[LangLevelID, LangLevel]
)

func (l LangLevel) TableName() string {
	return "master.lang_level"
}

func (l LangLevel) IDNamePair() *vo.IDNamePair[LangLevelID] {
	return vo.NewIDNamePair(l.ID, l.Name)
}

func (l LangLevel) GetID() LangLevelID {
	return l.ID
}

//go:generate go run $GOPATH/src/miidas/domain/connect/enum/decorator/enumDecorator.go -type=LangLevelID

// 言語レベル
const (
	LangLevelIDNone     LangLevelID = 1 // あてはまるものはない
	LangLevelIDNormal   LangLevelID = 2 // 日常会話レベル
	LangLevelIDBusiness LangLevelID = 3 // ビジネス会話レベル
	LangLevelIDNative   LangLevelID = 4 // ネイティブレベル
)
