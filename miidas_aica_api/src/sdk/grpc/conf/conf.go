package conf

import (
	"aica/api/sdk/env"
)

func GetClientConf(category string) (host string, port int, insecure bool, err error) {

	prefix := "MV2"
	pf := env.NewPrefixer(env.Prefix, category, prefix)

	// AICA_API_MV2_HOST 必須
	host = pf.MustGet("HOST")

	// AICA_API_MV2_PORT
	port = pf.MustGetInt("PORT")

	// AICA_API_MV2_INSECURE
	insecure, err = pf.GetBool("INSECURE")
	if err != nil {
		insecure = false
		err = nil
	}

	return
}
