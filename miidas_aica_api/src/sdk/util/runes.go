package util

// 最後の文字以外を返す
func GetCharsExceptLast(s string) string {
	// 1. インプットを[]runeに変換
	runes := []rune(s)

	// 2. インプットが1文字以下であれば空文字を返す
	if len(runes) <= 1 {
		return ""
	}

	// 3. 最後のrune以外を含むsliceを作る
	trimmedRunes := runes[:len(runes)-1]

	// 4. []runeをstringに変換する
	return string(trimmedRunes)
}

// 最後の文字を返す
func GetLastCharacter(s string) string {
	// 空文字であれば空文字を返す
	if s == "" {
		return ""
	}

	// 1. インプットを[]runeに変換する
	runes := []rune(s)

	// 2. 最後のruneのみの[]runeを作る
	lastRune := runes[len(runes)-1]

	// 3. []runeをstringに変換する
	return string(lastRune)
}
