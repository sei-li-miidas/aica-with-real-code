package internal

import (
	"aica/api/sdk/gormio"
	"context"

	"gorm.io/gorm"
)

var (
	agentDB  *gorm.DB
	miidasDB *gorm.DB
)

func SetupRDB(serviceName string, category string, debugMode bool) error {
	var err error

	agentDB, err = gormio.OpenAgentDB(serviceName, category, debugMode)
	if err != nil {
		return err
	}

	miidasDB, err = gormio.OpenMiidasDBReader(serviceName, category, debugMode)
	if err != nil {
		return err
	}

	return nil
}

func AgentDBWriter() *gorm.DB {
	return agentDB
}

func MiidasDBReader() *gorm.DB {
	return miidasDB
}

func MasterDBReader(_ context.Context) *gorm.DB {
	return miidasDB
}
