// Package error /*
/*
共通のAppErrorを定義しています。

AppErrorのcodeのルール

共通は一桁の番号を使います。api個々のエラーは1001番から付与してください。
番号に依存する箇所はないと思いますが、人が見て分かるために。

同じ意味だけど別のメッセージを返したい場合はapi個々に定義してください。

ErrInvalidRequest

一般的な入力値のチェックはバリデーションで行われますが、ユースケース内でチェックしなければならないものも多々あります。
このエラーはこういった場合のエラーとして使います。

ErrUnauthorized

ログインが確認できない場合に使います。
もしかしたら使い所がないかもしれません

ErrForbidden

該当データの参照権限がない場合に使います。
例：自分が受け取っていないオファー、担当のポジションではないなど。

ErrResourceNotFound

該当データが見つからない場合に使います。
ErrForbiddenとの使い分けに注意してください。

例:GET /resource/:id で指定されたidのデータが存在しない。

ErrInvalidStatus

該当データの操作ができる状態ではないときに使います。
例：削除済みデータを削除しようとした。

ErrRequestExpired

操作をする期限が切れているときに使います。
例：メール認証の一週間の期限を過ぎて、リンクを踏まれた。

ErrValueConflict

ユニークでなければならない値がすでに使われているときに使います。
例：ユーザーが登録しようとしたの電話番号やメールアドレスがすでに使われている。

*/
package error

import (
	"fmt"
	"net/http"
)

// common application errors
var (
	ErrInvalidRequest          = NewErrCodeMessage(1, "")                        // 入力値エラー
	ErrUnauthorized            = NewErrCodeMessage(2, "unauthorized user")       // ログインしていない
	ErrForbidden               = NewErrCodeMessage(3, "forbidden")               // このリソースの参照権限がない
	ErrResourceNotFound        = NewErrCodeMessage(4, "resource not found")      // リソースがない
	ErrInvalidStatus           = NewErrCodeMessage(5, "invalid status")          // リソースの状態が良くない。解消可能。
	ErrRequestExpired          = NewErrCodeMessage(6, "expired")                 // 期限切れ
	ErrValueConflict           = NewErrCodeMessage(7, "value conflict")          // すでに値が使われている
	ErrRefUserAccessNotAllowed = NewErrCodeMessage(8, "なりすましユーザーにはできません")        // なりすましユーザーでは操作できない
	ErrInternalServer          = NewErrCodeMessage(9, "internal server error")   // 内部エラー
	ErrClientClosedRequest     = NewErrCodeMessage(10, "client closed request")  // クライアントがリクエストをキャンセルした
	ErrTooManyRequests         = NewErrCodeMessage(11, "too many requests")      // リクエストが多すぎる
	ErrExternalServiceFail     = NewErrCodeMessage(900, "external service fail") // 外部サービスのエラー
)

var (
	ErrMap = map[ErrCode]int{
		ErrInvalidRequest:          http.StatusBadRequest,
		ErrUnauthorized:            http.StatusUnauthorized,
		ErrForbidden:               http.StatusForbidden,
		ErrResourceNotFound:        http.StatusNotFound,
		ErrInvalidStatus:           http.StatusBadRequest,
		ErrRequestExpired:          http.StatusBadRequest,
		ErrValueConflict:           http.StatusConflict,
		ErrInternalServer:          http.StatusInternalServerError,
		ErrExternalServiceFail:     http.StatusServiceUnavailable,
		ErrRefUserAccessNotAllowed: http.StatusForbidden,
		ErrTooManyRequests:         http.StatusTooManyRequests,
		ErrTooManyRequests:         http.StatusTooManyRequests,
	}
)

// HTTPStatusMapper は共通的なAppErrorと固有のAppErrorにマッピングされたHTTPコードを返す関数を返します。
func HTTPStatusMapper(uniqMapping map[ErrCode]int) func(ErrCode) (int, bool) {
	codeMapping := make(map[int]int, len(uniqMapping))
	for k, v := range uniqMapping {
		if _, found := codeMapping[k.ErrCode()]; found {
			panic(fmt.Errorf("app error code:%d already exists", k.ErrCode()))
		}
		codeMapping[k.ErrCode()] = v
	}

	return func(err ErrCode) (int, bool) {
		if v, ok := ErrMap[err]; ok { // 共通
			return v, true
		}
		if v, ok := codeMapping[err.ErrCode()]; ok { // 固有
			return v, true
		}

		return http.StatusNotImplemented, false // 見つからない場合 （TODO: 599 に変更）
	}
}
