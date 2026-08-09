//go:build mock

package mv2

import (
	"aica/api/sdk/logger"
	"miidas/m2/user/marketvalue/grpc/iface"
)

// MockMVGateway はgRPCを呼び出さずにモックデータを返すゲートウェイ
type MockMVGateway struct {
	logger logger.LevelLogger
}

func NewMockMarketValueGateway(logger logger.LevelLogger) MarketValueGateway {
	logger.Info("【モック】MV2モックゲートウェイを使用します")
	return &MockMVGateway{logger: logger}
}

func (m MockMVGateway) GetWillPositionList(
	companyWill *iface.Company, businessWill *iface.Business, positionWill *iface.Position,
) ([]*iface.PositionListEntry, error) {
	m.logger.Info("【モック】MV2モックデータを返します")

	return []*iface.PositionListEntry{
		{PositionId: 1, CompanyId: 1, BusinessId: 1},
		{PositionId: 2, CompanyId: 1, BusinessId: 1},
		{PositionId: 3, CompanyId: 2, BusinessId: 2},
	}, nil
}
