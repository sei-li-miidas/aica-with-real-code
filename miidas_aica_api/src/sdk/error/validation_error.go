package error

import (
	"encoding/json"
)

//go:generate go run $GOPATH/src/miidas/domain/connect/enum/decorator/enumDecorator.go -type=validationErrCode -output=validation_error_string.go

// validationErrCode はバリデーションエラーコード型
type validationErrCode int

const (
	// 番号の後方互換性を保っています。_で始まるものは使用禁止ですが後方互換のためにあります。
	// 必ず末尾に追加してください。
	unknown          validationErrCode = iota // 定義されていないバリデーションエラー。validator内部で使用
	required                                  // 必須
	less                                      // 小さい
	more                                      // 大きい
	length                                    // 長さ、要素数が一致しない
	_regex                                    // deprecated 正規表現で表現されている型毎に定義を作ること（例えばemailの定義とか）
	unsupported                               // サポート外の型。validator内部で使用
	badParameter                              // タグのパラメータが間違っている。validator内部で使用
	unknownTag                                // validate タグが間違っている。validatorが内部で使用
	invalid                                   // validator内部で使用
	notMatch                                  // 列挙されたどれでもない
	_unsupportedType                          // deprecated unsuppoted を使うこと
	duplicate                                 // 重複
	noBlank                                   // 空白っぽい文字をtrim後のrequired
	_lenTooLong                               // deprecated longを使うこと
	_maxRune                                  // deprecated longを使うこと
	email                                     // emailアドレス
	_time                                     // deprecated 使っていない？
	phoneNo                                   // 電話番号
	password                                  // パスワード
	_login                                    // deprecated これはvalidationではない
	numeric                                   // 数値
	nameKana                                  // カタカナ
	nameHiraKana                              // ひらがな
	bankAccountKana                           // 銀行口座名義
	nonblank                                  // 空白以外
	emailDomain                               // メールアドレスのドメインが確認できない
	errMobilePhoneNo                          // 携帯電話番号
)

var (
	ErrUnknown         = NewFieldValidationError(unknown)
	ErrRequired        = NewFieldValidationError(required)
	ErrLess            = NewFieldValidationError(less)
	ErrMore            = NewFieldValidationError(more)
	ErrLength          = NewFieldValidationError(length)
	ErrUnsupported     = NewFieldValidationError(unsupported)
	ErrBadParameter    = NewFieldValidationError(badParameter)
	ErrUnknownTag      = NewFieldValidationError(unknownTag)
	ErrInvalid         = NewFieldValidationError(invalid)
	ErrNotMatch        = NewFieldValidationError(notMatch)
	ErrDuplicate       = NewFieldValidationError(duplicate)
	ErrNoBlank         = NewFieldValidationError(noBlank)
	ErrEmail           = NewFieldValidationError(email)
	ErrPhoneNo         = NewFieldValidationError(phoneNo)
	ErrPassword        = NewFieldValidationError(password)
	ErrNumeric         = NewFieldValidationError(numeric)
	ErrNameKana        = NewFieldValidationError(nameKana)
	ErrNameHiraKana    = NewFieldValidationError(nameHiraKana)
	ErrBankAccountKana = NewFieldValidationError(bankAccountKana)
	ErrNonBlank        = NewFieldValidationError(nonblank)
	ErrEmailDomain     = NewFieldValidationError(emailDomain)
	ErrMobilePhoneNo   = NewFieldValidationError(errMobilePhoneNo)
)

type (
	// StructValidationError は構造体全体のバリデーションエラーです
	StructValidationError interface {
		Error
		Add(string, FieldValidationError)
		Fields() map[string]FieldValidationError
		Valid() bool
	}

	structValidationError struct {
		*errCodeMessage
		fields map[string]FieldValidationError
	}
)

func NewStructValidationError() StructValidationError {
	return &structValidationError{
		errCodeMessage: &errCodeMessage{
			code:    0,
			message: "",
		},
		fields: map[string]FieldValidationError{},
	}
}

func (e *structValidationError) Add(fieldName string, fErr FieldValidationError) {
	e.fields[fieldName] = fErr
}

func (e *structValidationError) Fields() map[string]FieldValidationError {
	return e.fields
}

func (e *structValidationError) Bare() ErrCode {
	return e.errCodeMessage
}

func (e *structValidationError) Type() string {
	return StructValidationErrorType
}

func (e *structValidationError) Error() string {
	if b, err := json.Marshal(e.fields); err != nil {
		return err.Error()
	} else {
		return string(b)
	}
}

// Valid はエラーが無いときtrueを返します。
func (e structValidationError) Valid() bool {
	return len(e.fields) == 0
}

type (
	// FieldValidationError はフィールドごとのバリデーションエラーです
	FieldValidationError interface {
		Error
	}

	fieldValidationError struct {
		*errCodeMessage
		internal error
	}
)

// NewFieldValidationError はFieldValidationErrorのコンストラクタ
func NewFieldValidationError(code validationErrCode) FieldValidationError {
	return &fieldValidationError{
		errCodeMessage: &errCodeMessage{
			code:    int(code),
			message: code.String(),
		},
	}
}

func NewUnknownFieldValidationError(internal error) FieldValidationError {
	return &fieldValidationError{
		errCodeMessage: &errCodeMessage{
			code:    int(unknown),
			message: unknown.String(),
		},
		internal: internal,
	}
}

func (e *fieldValidationError) MarshalJSON() ([]byte, error) {
	type inner struct {
		Code     int    `json:"Code"`
		Message  string `json:"Message"`
		Internal error  `json:"Internal,omitempty"`
	}
	return json.Marshal(inner{Code: e.ErrCode(), Message: e.ErrMessage()})
}

func (e *fieldValidationError) Bare() ErrCode {
	return e.errCodeMessage
}

func (e *fieldValidationError) Type() string {
	return FieldValidationErrorType
}

func (e *fieldValidationError) Error() string {
	return errorMessage(e)
}
