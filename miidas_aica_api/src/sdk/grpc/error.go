package grpc

import (
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"

	merr "aica/api/sdk/error"
)

// ShouldIgnoreErr 握り潰して良いgrpcエラーか？ (API Server/Client側で使用)
// usecase内で grpcのエラーを merr.ErrClientClosedRequest に変換している箇所があるので、両方の場合に対応する。
func ShouldIgnoreErr(err error) bool {
	return status.Code(err) == codes.Canceled || merr.Is(err, merr.ErrClientClosedRequest)
}
