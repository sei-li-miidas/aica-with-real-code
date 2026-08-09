package master

import "strings"

// SkillName スキル名
type SkillName string

const skillNameSeparator = "$"

// GetDisplayName スキル名の$で区切られた最後を取得する
func (sn SkillName) GetDisplayName() string {
	splitName := strings.Split(string(sn), skillNameSeparator)
	return splitName[len(splitName)-1]
}

// GetDummyGroupName スキル名の$で区切られた最初を取得する
func (sn SkillName) GetDummyGroupName() string {
	splitName := strings.Split(string(sn), skillNameSeparator)
	if len(splitName) == 1 { // "$"で区切られていない場合は空文字
		return ""
	}
	return splitName[0]
}
