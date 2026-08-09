package client

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	perr "github.com/pkg/errors"
	"github.com/samber/lo"
	"google.golang.org/grpc"
	"google.golang.org/grpc/connectivity"
	"google.golang.org/grpc/credentials"
	credInscure "google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/keepalive"

	"aica/api/sdk/grpc/request_id"
)

type Option func(*Options)

type Options struct {
	hostname    string
	port        int
	dialOptions []grpc.DialOption
}

func (c Options) Target() string {
	return fmt.Sprintf("%s:%d", c.hostname, c.port)
}

var (
	KeepaliveParameters = keepalive.ClientParameters{
		Time:                1 * time.Minute,  // Ping送信間隔
		Timeout:             30 * time.Second, // Ping応答待ち時間
		PermitWithoutStream: true,             // ストリームがなくてもPing送信
	}

	defaultServiceConfig = serviceConfig{
		// grpc client側で接続先のserverをround_robinでLBする
		// - AWS CloudMapでgrpc serverのコンテナのIPアドレスの名前解決をgrpc client側から直接行う方式に対応するため
		// - 解決したIPアドレスが複数ある場合に、RPCごとに接続先が変わるようにし、LBされるようにする
		// - ref: https://github.com/grpc/grpc/blob/master/doc/load-balancing.md#round_robin
		LoadBalancingConfig: []loadBalancingConfig{newRoundRobinLoadBalancingConfig()},

		MethodConfig: []methodConfig{
			{
				// 全methodを対象にする
				// MethodConfig without names (empty list) will be skipped.
				// If the 'service' field is empty, the 'method' field must be empty, and this MethodConfig specifies the default for all methods (it's the default config).
				// ref: https://github.com/grpc/grpc-proto/blob/master/grpc/service_config/service_config.proto#L45-L52
				Name: []methodConfigName{{Service: "", Method: ""}},

				// なにか異常があった際に無限ブロックしないように一律上限を設ける
				// ref: https://github.com/grpc/grpc-proto/blob/23f5b568eefcb876e6ebc3b01725f1f20cff999e/grpc/service_config/service_config.proto#L90-L99
				Timeout: "60s",

				// レアケースかもしれないが、デプロイなどでgrpc server側のコンテナが入れ替わる際に、古いDNSキャッシュのTTLが残っていると、
				// そこで再解決されるIPアドレスが全て古いコンテナのものになり、全ての接続に失敗して、TRANSIENT_FAILUREの状態になる可能性がある。
				// そのときに呼ばれたRPCを即時失敗させるのではなく、新しいコンテナのIPアドレスを取得し直して復帰するまで待つようにする。
				// Timeoutと併用しないとserver側での異常発生時に無限ブロックすることになるので注意。
				// ref: https://github.com/grpc/grpc/blob/master/doc/wait-for-ready.md
				WaitForReady: true,
			},
		},
	}

	internalDialOptions = []grpc.DialOption{
		grpc.WithChainUnaryInterceptor(
			request_id.UnaryClientInterceptor(), // リクエストIDを付与する
		),
		grpc.WithChainStreamInterceptor(
			request_id.StreamClientInterceptor(), // リクエストIDを付与する
		),
		grpc.WithKeepaliveParams(KeepaliveParameters),
		grpc.WithDefaultServiceConfig(defaultServiceConfig.toJsonString()),
		// server側にservice configを設定していないので、disabledにして常に上で設定したdefaultServiceConfigを使うようにする
		// これによってDNSへの無駄な問い合わせを減らす
		// - Note that this dial option only disables service config from resolver. If default service config is provided, gRPC will use the default service config.
		grpc.WithDisableServiceConfig(),
	}
)

func Hostname(hostname string) Option {
	return func(c *Options) {
		c.hostname = hostname
	}
}

func Port(port int) Option {
	return func(c *Options) {
		c.port = port
	}
}

func AddDialOptions(dialOptions ...grpc.DialOption) Option {
	return func(c *Options) {
		c.dialOptions = append(c.dialOptions, dialOptions...)
	}
}

// NewSecureOption TLS通信を行うか、平文で通信を行うかのDialOptionを返す.
// insecure: true -> 平文, false -> TLS通信を行う
func NewSecureOption(insecure bool) grpc.DialOption {
	var cred credentials.TransportCredentials
	if insecure {
		cred = credInscure.NewCredentials()
	} else {
		cred = credentials.NewTLS(nil)
	}

	return grpc.WithTransportCredentials(cred)
}

// NewInternalClient 内部向けのクライアントを返します。
// このクライアントは内部向けを想定しています。
// ※AWSのロードバランサーがTLSのみ対応しているため、ミイダスでは原則TLSを使います
func NewInternalClient(ctx context.Context, opts ...Option) (*grpc.ClientConn, error) {
	o := evalOptions(opts...)

	// grpc.NewClient は、非同期（ノンブロッキング）でコネクションを作る設計のため、Dial 時にブロックしないので
	cc, err := grpc.NewClient(o.Target(), o.dialOptions...)
	if err != nil {
		return nil, perr.Wrapf(err, "grpc channel作成エラー。Target: %+v", o.Target())
	}

	// Ready になるのを待つ
	ctxWithTimeout, cancel := context.WithTimeoutCause(ctx, time.Minute*10, perr.New("timeout after 10 minutes"))
	defer cancel()

	cc.Connect()
	for {
		state := cc.GetState()
		if state == connectivity.Ready {
			break
		}
		if !cc.WaitForStateChange(ctxWithTimeout, state) {
			// タイムアウト
			return nil, perr.Wrapf(ctxWithTimeout.Err(), "grpc 接続タイムアウト。Target: %+v, state: %+v", o.Target(), state)
		}
	}

	return cc, nil
}

func evalOptions(opts ...Option) *Options {
	o := Options{}
	o.dialOptions = internalDialOptions
	for _, opt := range opts {
		opt(&o)
	}
	return &o
}

// ref: https://github.com/grpc/grpc/blob/master/doc/service_config.md
type serviceConfig struct {
	LoadBalancingConfig []loadBalancingConfig `json:"loadBalancingConfig"`
	MethodConfig        []methodConfig        `json:"methodConfig"`
}

// ref: https://github.com/grpc/grpc-proto/blob/23f5b568eefcb876e6ebc3b01725f1f20cff999e/grpc/service_config/service_config.proto#L44
type methodConfig struct {
	Name         []methodConfigName `json:"name"`
	Timeout      string             `json:"timeout"`
	WaitForReady bool               `json:"waitForReady"`
}

type loadBalancingConfig map[string]any

func newRoundRobinLoadBalancingConfig() loadBalancingConfig {
	return loadBalancingConfig{
		// ref:
		// - https://github.com/grpc/grpc-proto/blob/23f5b568eefcb876e6ebc3b01725f1f20cff999e/grpc/service_config/service_config.proto#L491
		// - https://github.com/grpc/grpc-proto/blob/23f5b568eefcb876e6ebc3b01725f1f20cff999e/grpc/service_config/service_config.proto#L202
		"round_robin": struct{}{},
	}
}

type methodConfigName struct {
	Service string `json:"service"`
	Method  string `json:"method"`
}

func (c serviceConfig) toJsonString() string {
	return string(lo.Must1(json.Marshal(c)))
}
