package position

//go:generate go run $GOPATH/src/miidas/domain/connect/enum/decorator/enumDecorator.go -type=CertificationRank -output=enum_string.go
type CertificationRank int

const (
	CertificationRankNon    CertificationRank = 0
	CertificationRankBronze CertificationRank = 1
	CertificationRankSilver CertificationRank = 2
	CertificationRankGold   CertificationRank = 3
)

// IsCertificated 認定ランクがBronze以上を取得しているか判定する。取得していればture
func (r CertificationRank) IsCertificated() bool {
	return r >= CertificationRankBronze
}
