package mv2

import (
	"github.com/samber/lo"

	"aica/api/sdk/logger"
	"context"
	"io"
	"miidas/m2/user/marketvalue/grpc/iface"
	gbusiness "miidas/m2/user/marketvalue/grpc/iface/business"
	gcompany "miidas/m2/user/marketvalue/grpc/iface/company"
	gposition "miidas/m2/user/marketvalue/grpc/iface/position"
	"miidas/m2/user/marketvalue/grpc/iface/user"
	"time"

	"github.com/mostynb/go-grpc-compression/lz4"
	"google.golang.org/grpc"
	"google.golang.org/protobuf/types/known/timestamppb"
)

type (
	// MarketValueGateway はMV2ゲートウェイのインターフェース
	MarketValueGateway interface {
		GetWillPositionList(companyWill *iface.Company, businessWill *iface.Business, positionWill *iface.Position) ([]*iface.PositionListEntry, error)
	}

	MVGateway struct {
		client iface.MarketValueClient
		logger logger.LevelLogger
	}

	WithError[T any] struct {
		Value T
		Error error
	}

	CompanyWithError  = WithError[*gcompany.Company]
	BusinessWithError = WithError[*gbusiness.Business]
	PositionWithError = WithError[*gposition.Position]
)

const (
	timeout = 10 * time.Minute
)

func NewMarketValueGateway(logger logger.LevelLogger) MarketValueGateway {
	return &MVGateway{
		client: iface.NewMarketValueClient(clientConnection()),
		logger: logger,
	}
}

func (m MVGateway) GetWillPositionList(
	companyWill *iface.Company, businessWill *iface.Business, positionWill *iface.Position,
) ([]*iface.PositionListEntry, error) {
	req := iface.WillPositionListRequest{
		Profile: &user.Profile{
			UserId: lo.ToPtr(int32(-1)),
			Job: &user.JobInfo{
				ManagementExpTermId:   lo.ToPtr(int32(0)),
				ManagementPeopleQtyId: 0,
				ExpCompanyId:          0,
				RetireMonth:           0,
				CompanyNameId:         0,
			},
			Lang: &user.LangInfo{
				EngLevel:  0,
				EngToeic:  0,
				EngToefli: 0,
				EngToeflp: 0,
			},
			RegisteredAt: &timestamppb.Timestamp{
				Seconds: time.Now().Unix(),
			},
		},
		CompanyWill:  companyWill,
		BusinessWill: businessWill,
		PositionWill: positionWill,
	}

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	// grpcのサービスリクエスト
	stream, err := m.client.GetWillPositionList(ctx, &req, m.callOptions()...)
	if err != nil {
		m.logger.Error("failed to get will position list", err)
		return nil, err
	}

	var positions []*iface.PositionListEntry
	for {
		pb, err := stream.Recv()
		if err == io.EOF {
			break
		}
		if err != nil {
			m.logger.Error("failed to receive will position list", "error", err)
			return nil, err
		}

		positions = append(positions, pb)
	}

	return positions, nil
}

func (m MVGateway) callOptions() []grpc.CallOption {
	return []grpc.CallOption{
		grpc.UseCompressor(lz4.Name),
	}
}
