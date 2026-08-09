package company

//go:generate go run $GOPATH/src/miidas/domain/connect/enum/decorator/enumDecorator.go -type=RegistrationStatus -output=enum_string.go

// 企業登録ステータス
type RegistrationStatus int

const (
	RegistrationStatusTemporary  RegistrationStatus = 1 // 仮登録
	RegistrationStatusRegistered RegistrationStatus = 2 // 本登録
	RegistrationStatusWithdrawn  RegistrationStatus = 3 // 退会
)
