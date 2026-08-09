package util

// sliceに値Tが含まれるかどうかを確認する(完全一致)
func SliceContains[T comparable](slice []T, target T) bool {
	for _, v := range slice {
		if v == target {
			return true
		}
	}
	return false
}
