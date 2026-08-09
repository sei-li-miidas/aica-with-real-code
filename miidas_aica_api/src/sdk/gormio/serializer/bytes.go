package serializer

import "unsafe"

// string と []byte の相互変換を高速・zero copyで行う。
// スタック上の変数について変換後に一部の値を変えると go 自体がクラッシュする。
// このパッケージのみで使用する。
// ex)
//   s := "hello"
//   b := StringToBytes(s)
//   b[0] = 'h'
//   fmt.Println(s)   ここで go 自体がクラッシュする。
//
// https://mattn.kaoriya.net/software/lang/go/20220907112622.htm

// s2bs string を []byte として扱う
func s2bs(s string) []byte {
	if len(s) == 0 {
		return []byte{}
	}
	return unsafe.Slice(unsafe.StringData(s), len(s))
}

// bs2s []byte を string として扱う
func bs2s(b []byte) string {
	if len(b) == 0 {
		return ""
	}
	return unsafe.String(&b[0], len(b))
}
