package conf

type AppConfig struct {
	Nfs string
}

var GetAppConfig func() *AppConfig
