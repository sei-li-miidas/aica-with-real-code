package s3

import (
	"net/url"
	"strings"

	"aica/api/sdk/env"
)

// GetEndpoint 環境変数からエンドポイントURLを取得する
func GetEndpoint(envName string) (url *url.URL, err error) {
	domain, err := env.Get(envName)
	if err != nil {
		return nil, err
	}

	var scheme string
	if strings.Contains(domain, "localhost:") {
		scheme = "http"
	} else {
		scheme = "https"
	}

	u, err := url.Parse(scheme + "://" + domain)
	if err != nil {
		return nil, err
	}
	return u, nil
}

// GetUserEndpoint はユーザーのS3エンドポイントURLを返します。
func GetUserEndpoint() (url *url.URL, err error) {
	return GetEndpoint("MIIDAS_S3_USER_ASSETS_ENDPOINT")
}

func GetImageUrl(path string) (url *url.URL, err error) {
	endpoint, err := GetUserEndpoint()
	if err != nil {
		return nil, err
	}
	return endpoint.JoinPath(path), nil
}
