// Package gormio gormio はgorm.io向けのコネクション等を提供します。
//
// パニックの取り扱い
// これまであったCleanupTxの代わりに汎用的にpanicを取り扱う方法を用意しました。
// 通常は以下のようにRePanicを使ってpanicを処理します。
// RePanicはpanicをerrorに変換し、再panicさせます。これによりapiやbatchでpanicを拾い、正しく終了させます。
// import merr "miidas/sdk/error"
//
// tx := db.Begin()
//
//	defer merr.RePanic(func(err error) {
//	    tx.Rollback()
//	    // ここにログ出力などを書く。
//	})
//
// goroutineの中の場合、RePanicではなくCleanupを使います。RePanicとの違いは再panicさせるかどうかだけです。
// goroutineでは再panicさせるとmainが終了してしまうので、この使い分けは必ず守ってください。
package gormio

import (
	"database/sql"
	"os"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

// OpenPostgresSQL PostgresSQL向けのOpen gorm接続をOpenする。
// ロガーが自動で設定されます。
func OpenPostgresSQL(conn *sql.DB, category string, trace bool, opts ...gorm.Option) (*gorm.DB, error) {
	return gorm.Open(postgres.New(postgres.Config{Conn: conn}),
		append([]gorm.Option{ZeroLogger(category, trace)}, opts...)...)
}

// ZeroLogger zerologをロガーに設定する
func ZeroLogger(category string, trace bool) gorm.Option {
	return NewOption().SetApply(func(config *gorm.Config) error {
		config.Logger = NewLogger(os.Stdout, category, trace)
		return nil
	})
}

// NewOption *gorm.Optionの実装を返す。
// ApplyとAfterInitializeにはnop実装がセットされるので、必要な処理をセットしてください。
func NewOption() *Option {
	return &Option{
		apply:     nopApply,
		afterInit: nopAfterInit,
	}
}

// Option gorm.Optionの実装
type Option struct {
	apply     func(*gorm.Config) error
	afterInit func(*gorm.DB) error
}

func (o Option) Apply(cfg *gorm.Config) error {
	return o.apply(cfg)
}
func (o Option) AfterInitialize(db *gorm.DB) error {
	return o.afterInit(db)
}

// SetApply Applyメソッドで実行する処理を設定する
func (o *Option) SetApply(f func(*gorm.Config) error) *Option {
	o.apply = f
	return o
}

// SetAfterInit AfterInitializeで実行する処理を設定する
func (o *Option) SetAfterInit(f func(*gorm.DB) error) *Option {
	o.afterInit = f
	return o
}

// nopApply gorm.Option#Applyのnop実装
func nopApply(_ *gorm.Config) error {
	return nil
}

// nopAfterInit gorm.Option#AfterInitializeのnop実装
func nopAfterInit(_ *gorm.DB) error {
	return nil
}
