package initialize

import (
	"fmt"
	"sync"

	"aica/api/sdk/env"
)

func getApp() string {
	return env.MustGet(fmt.Sprintf("%s_ENV", env.Prefix))
}

// GetApp アプリケーション実行環境の取得
// sync.OnceValue() によりキャシュ化
var GetApp = sync.OnceValue(getApp)

func IsTest() bool {
	return GetApp() == "test"
}

func IsLocal() bool {
	return GetApp() == "local"
}

func IsProduction() bool {
	return GetApp() == "production"
}
