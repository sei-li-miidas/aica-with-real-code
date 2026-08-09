package internal

import (
	"aica/api/sdk/gormio"

	"gorm.io/gorm"
)

var (
	semanticDB *gorm.DB
	miidasDB   *gorm.DB
)

func SetupRDB(serviceName string, category string, debugMode bool) error {
	var err error

	semanticDB, err = gormio.OpenAgentDB(serviceName, category, debugMode)
	if err != nil {
		return err
	}

	miidasDB, err = gormio.OpenMiidasDBReader(serviceName, category, debugMode)
	if err != nil {
		return err
	}

	return nil
}

func SemanticDBWriter() *gorm.DB {
	return semanticDB
}

func MiidasDBReader() *gorm.DB {
	return miidasDB
}
