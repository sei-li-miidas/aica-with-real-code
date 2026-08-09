package env

const (
	Prefix = "AICA" // 環境変数のプレフィックス用
)

// Prefixer はプレフィックス付きの環境変数取得
//
// Prefixerはプレフィックス付き環境変数を簡単に扱えるようにしています。
type Prefixer struct {
	Exists     func(...string) bool
	Key        func(...string) string
	Get        func(...string) (string, error)
	MustGet    func(...string) string
	GetInt     func(...string) (int, error)
	MustGetInt func(...string) int
	GetStrCSV  func(...string) ([]string, error)
	GetBool    func(...string) (bool, error)
}

// NewPrefixer はPrefixerのコンストラクタ
func NewPrefixer(prefixes ...string) Prefixer {
	return Prefixer{
		Exists:     exists(prefixes...),
		Key:        key(prefixes...),
		Get:        get(prefixes...),
		MustGet:    mustGet(prefixes...),
		GetInt:     getInt(prefixes...),
		MustGetInt: mustGetInt(prefixes...),
		GetStrCSV:  getStrCSV(prefixes...),
		GetBool:    getBool(prefixes...),
	}
}
