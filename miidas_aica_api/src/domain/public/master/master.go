package master

import (
	"strconv"

	"aica/api/sdk/vo"
)

// ToIdNamePairList IntIdNamePairのリストを返す
func ToIdNamePairList[T vo.IntIDAndName](list []T) []*vo.IntIDNamePair {
	ret := make([]*vo.IntIDNamePair, 0, len(list))
	for _, e := range list {
		ret = append(ret, e.IntIDNamePair())
	}
	return ret
}

// IdNamePair IdNamePairを返す。要素がnilや見つかってないときはnilを返します。
func IdNamePair(e vo.IntIDAndName, found bool) *vo.IntIDNamePair {
	if found && e != nil {
		return e.IntIDNamePair()
	}
	return nil
}

// ValidIdNamePair IdNamePairを返す
//
// 対象がなかった場合、空のIdNamePairを返します。
func ValidIdNamePair(e vo.IntIDAndName, found bool) *vo.IntIDNamePair {
	if found && e != nil {
		return e.IntIDNamePair()
	}
	return &vo.IntIDNamePair{}
}

// StrIdNamePair 互換性維持のために用意
func StrIdNamePair(e vo.IntIDAndName, found bool) *vo.StrIDNamePair {
	if found && e != nil {
		v := e.IntIDNamePair()
		return vo.NewStrIDNamePair(strconv.Itoa(v.ID), v.Name)
	}
	return nil
}

// NameHolder なんらかの名前を持つインタフェース
type NameHolder interface {
	GetName() string
}

// IDHolder なんらかのIDを持つインタフェース
type IDHolder[I comparable] interface {
	GetID() I
}
