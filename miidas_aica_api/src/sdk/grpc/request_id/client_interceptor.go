// Package request_id リクエストIDを設定します
//
// クライアントで設定したものをサーバーで取得します。取得はloggerパッケージで行っています。
package request_id

import (
	"context"

	"github.com/google/uuid"
	"github.com/grpc-ecosystem/go-grpc-middleware/v2/metadata"
	"google.golang.org/grpc"

	mmeta "aica/api/sdk/grpc/metadata"
)

// KeyHTTPRequestID sdk/echo/middleware/request_id.key と同じkey
const KeyHTTPRequestID = "http-request-id"

func UnaryClientInterceptor() grpc.UnaryClientInterceptor {
	return func(parentCtx context.Context, method string, req, reply any, cc *grpc.ClientConn, invoker grpc.UnaryInvoker, opts ...grpc.CallOption) error {
		md := metadata.ExtractOutgoing(parentCtx)
		id := parentCtx.Value(KeyHTTPRequestID)
		if id != nil {
			md.Add(KeyHTTPRequestID, id.(string))
		}
		md.Add(mmeta.KeyRequestID, uuid.NewString())
		ctx := md.ToOutgoing(parentCtx)
		return invoker(ctx, method, req, reply, cc, opts...)
	}
}

func StreamClientInterceptor() grpc.StreamClientInterceptor {
	return func(parentCtx context.Context, desc *grpc.StreamDesc, cc *grpc.ClientConn, method string, streamer grpc.Streamer, opts ...grpc.CallOption) (grpc.ClientStream, error) {
		md := metadata.ExtractOutgoing(parentCtx)
		id := parentCtx.Value(KeyHTTPRequestID)
		if id != nil {
			md.Add(KeyHTTPRequestID, id.(string))
		}
		md.Add(mmeta.KeyRequestID, uuid.NewString())
		ctx := md.ToOutgoing(parentCtx)
		return streamer(ctx, desc, cc, method, opts...)
	}
}
