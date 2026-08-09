package position

import (
	tmock "aica/api/api/mcptool/testutil/mock"
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	pmodel "aica/api/api/mcptool/usecase/position/model"
	"aica/api/domain/position"
	uaposition "aica/api/domain/user/apply/position"
	"aica/api/domain/vectorizer"
	merr "aica/api/sdk/error"
	"aica/api/sdk/http"
	"errors"
	"miidas/m2/user/marketvalue/grpc/iface"
	"testing"

	"gorm.io/gorm"

	"github.com/pgvector/pgvector-go"
	"github.com/samber/lo"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// mockMvGateway MVGatewayのモック
type mockMvGateway struct {
	mock.Mock
}

func (m *mockMvGateway) GetWillPositionList(
	companyWill *iface.Company,
	businessWill *iface.Business,
	positionWill *iface.Position,
) ([]*iface.PositionListEntry, error) {
	args := m.Called(companyWill, businessWill, positionWill)
	return args.Get(0).([]*iface.PositionListEntry), args.Error(1)
}

// mockVectorizerRepository VectorizerRepositoryのモック
type mockVectorizerRepository struct {
	mock.Mock
}

func (m *mockVectorizerRepository) GenerateEmbedding(text string) (*pgvector.Vector, error) {
	args := m.Called(text)
	return args.Get(0).(*pgvector.Vector), args.Error(1)
}

func (m *mockVectorizerRepository) GenerateEmbeddings(embeddingTargets []*vectorizer.EmbeddingTarget) ([]*vectorizer.EmbeddingResult, error) {
	args := m.Called(embeddingTargets)
	return args.Get(0).([]*vectorizer.EmbeddingResult), args.Error(1)
}

// mockPositionRepository PositionRepositoryのモック
type mockPositionRepository struct {
	mock.Mock
}

func (m *mockPositionRepository) SemanticSearch(
	embedding string,
	distance float64,
	addConditions func(*gorm.DB) *gorm.DB,
) ([]*position.PositionSearchResult, error) {
	args := m.Called(embedding, distance, addConditions)
	return args.Get(0).([]*position.PositionSearchResult), args.Error(1)
}

// mockReadPositionRepository ReadPositionRepositoryのモック
type mockReadPositionRepository struct {
	mock.Mock
}

func (m *mockReadPositionRepository) GetByIDs(ids []uaposition.ID) (uaposition.Positions, error) {
	args := m.Called(ids)
	return args.Get(0).(uaposition.Positions), args.Error(1)
}

type params struct {
	req              *pmodel.GenericPositionSearchParams
	cityIDs          []int
	jobTypeSmallIDs  []int
	industrySmallIDs []int
	theme            pcontracts.PositionRecommendationTheme
}

type expectedResult struct {
	positionIDs []uaposition.ID
	positions   []*pmodel.PositionSummary
	err         error
}

func Test_SearchUseCase_Execute(t *testing.T) {
	embedding := pgvector.NewVector([]float32{0.1, 0.2, 0.3})

	tests := []struct {
		name                      string
		mockMVGatewaySetup        func(m *mockMvGateway)
		mockVectorizerRepoSetup   func(m *mockVectorizerRepository, keyword string)
		mockPositionRepoSetup     func(m *mockPositionRepository)
		mockReadPositionRepoSetup func(m *mockReadPositionRepository)
		params                    params
		expected                  expectedResult
	}{
		{
			name: "正常系: 意味情報検索のパラメータが空の場合、意味情報検索を行わずにMV2の検索結果を返す",
			mockMVGatewaySetup: func(m *mockMvGateway) {
				m.On("GetWillPositionList", mock.Anything, mock.Anything, mock.Anything).
					Return([]*iface.PositionListEntry{{PositionId: 101}, {PositionId: 102}}, nil).Once()
			},
			mockVectorizerRepoSetup: func(m *mockVectorizerRepository, keyword string) {},
			mockPositionRepoSetup:   func(m *mockPositionRepository) {},
			mockReadPositionRepoSetup: func(m *mockReadPositionRepository) {
				m.On("GetByIDs", []uaposition.ID{101, 102}).Return(uaposition.Positions{{ID: 101}, {ID: 102}}, nil).Once()
			},
			params: params{
				req:              &pmodel.GenericPositionSearchParams{},
				cityIDs:          nil,
				jobTypeSmallIDs:  nil,
				industrySmallIDs: nil,
				theme:            pcontracts.PositionRecommendationTheme(""),
			},
			expected: expectedResult{
				positionIDs: []uaposition.ID{101, 102},
				positions:   []*pmodel.PositionSummary{{ID: 101}, {ID: 102}},
				err:         nil,
			},
		},
		{
			name: "正常系: 意味情報検索のパラメータが存在する場合、意味情報検索を行い、距離順に並べた結果を返す",
			mockMVGatewaySetup: func(m *mockMvGateway) {
				m.On("GetWillPositionList", mock.Anything, mock.Anything, mock.Anything).
					Return([]*iface.PositionListEntry{{PositionId: 101}, {PositionId: 102}}, nil).Once()
			},
			mockVectorizerRepoSetup: func(m *mockVectorizerRepository, keyword string) {
				m.On("GenerateEmbedding", keyword).Return(lo.ToPtr(embedding), nil).Once()
			},
			mockPositionRepoSetup: func(m *mockPositionRepository) {
				m.On("SemanticSearch", embedding.String(), http.DEFAULT_DISTANCE, mock.Anything).
					Return([]*position.PositionSearchResult{{ID: 102, Distance: 0.1}, {ID: 101, Distance: 0.2}}, nil).Once()
			},
			mockReadPositionRepoSetup: func(m *mockReadPositionRepository) {
				m.On("GetByIDs", []uaposition.ID{102, 101}).Return(uaposition.Positions{{ID: 102}, {ID: 101}}, nil).Once()
			},
			params: params{
				req: &pmodel.GenericPositionSearchParams{
					PositionKeyword: "エンジニア",
				},
				cityIDs:          nil,
				jobTypeSmallIDs:  nil,
				industrySmallIDs: nil,
				theme:            pcontracts.PositionRecommendationTheme(""),
			},
			expected: expectedResult{
				positionIDs: []uaposition.ID{102, 101},
				positions:   []*pmodel.PositionSummary{{ID: 102}, {ID: 101}},
				err:         nil,
			},
		},
		{
			name: "正常系: Limitが指定されていない場合、デフォルトのLimit（http.DEFAULT_LIMIT = 5）件数分だけ結果を返す",
			mockMVGatewaySetup: func(m *mockMvGateway) {
				m.On("GetWillPositionList", mock.Anything, mock.Anything, mock.Anything).
					Return([]*iface.PositionListEntry{
						{PositionId: 101}, {PositionId: 102}, {PositionId: 103}, {PositionId: 104}, {PositionId: 105},
						{PositionId: 106}, {PositionId: 107}, {PositionId: 108}, {PositionId: 109}, {PositionId: 110},
						{PositionId: 111}, {PositionId: 112},
					}, nil).Once()
			},
			mockVectorizerRepoSetup: func(m *mockVectorizerRepository, keyword string) {},
			mockPositionRepoSetup:   func(m *mockPositionRepository) {},
			mockReadPositionRepoSetup: func(m *mockReadPositionRepository) {
				m.On("GetByIDs", []uaposition.ID{101, 102, 103, 104, 105}).
					Return(uaposition.Positions{
						{ID: 101}, {ID: 102}, {ID: 103}, {ID: 104}, {ID: 105},
					}, nil).Once()
			},
			params: params{
				req:              &pmodel.GenericPositionSearchParams{},
				cityIDs:          nil,
				jobTypeSmallIDs:  nil,
				industrySmallIDs: nil,
				theme:            pcontracts.PositionRecommendationTheme(""),
			},
			expected: expectedResult{
				positionIDs: []uaposition.ID{101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112},
				positions: []*pmodel.PositionSummary{
					{ID: 101}, {ID: 102}, {ID: 103}, {ID: 104}, {ID: 105},
				},
				err: nil,
			},
		},
		{
			name: "正常系: ポジション検索結果が存在しない場合、nilを返す",
			mockMVGatewaySetup: func(m *mockMvGateway) {
				m.On("GetWillPositionList", mock.Anything, mock.Anything, mock.Anything).Return([]*iface.PositionListEntry{}, nil).Once()
			},
			mockVectorizerRepoSetup:   func(m *mockVectorizerRepository, keyword string) {},
			mockPositionRepoSetup:     func(m *mockPositionRepository) {},
			mockReadPositionRepoSetup: func(m *mockReadPositionRepository) {},
			params: params{
				req:              &pmodel.GenericPositionSearchParams{},
				cityIDs:          nil,
				jobTypeSmallIDs:  nil,
				industrySmallIDs: nil,
				theme:            pcontracts.PositionRecommendationTheme(""),
			},
			expected: expectedResult{
				positionIDs: nil,
				positions:   nil,
				err:         nil,
			},
		},
		{
			name: "異常系: MV2の呼び出しに失敗した場合、エラーを返す",
			mockMVGatewaySetup: func(m *mockMvGateway) {
				m.On("GetWillPositionList", mock.Anything, mock.Anything, mock.Anything).
					Return([]*iface.PositionListEntry{}, errors.New("MVGateway internal error")).Once()
			},
			mockVectorizerRepoSetup:   func(m *mockVectorizerRepository, keyword string) {},
			mockPositionRepoSetup:     func(m *mockPositionRepository) {},
			mockReadPositionRepoSetup: func(m *mockReadPositionRepository) {},
			params: params{
				req:              &pmodel.GenericPositionSearchParams{},
				cityIDs:          nil,
				jobTypeSmallIDs:  nil,
				industrySmallIDs: nil,
				theme:            pcontracts.PositionRecommendationTheme(""),
			},
			expected: expectedResult{
				positionIDs: nil,
				positions:   nil,
				err:         merr.ErrInternalServer.WithCause(errors.New("MVGateway internal error")),
			},
		},
		{
			name: "異常系: GenerateEmbeddingに失敗した場合、エラーを返す",
			mockMVGatewaySetup: func(m *mockMvGateway) {
				m.On("GetWillPositionList", mock.Anything, mock.Anything, mock.Anything).
					Return([]*iface.PositionListEntry{{PositionId: 101}, {PositionId: 102}}, nil).Once()
			},
			mockVectorizerRepoSetup: func(m *mockVectorizerRepository, keyword string) {
				m.On("GenerateEmbedding", keyword).
					Return((*pgvector.Vector)(nil), errors.New("Generating embeddings failed")).Once()
			},
			mockPositionRepoSetup:     func(m *mockPositionRepository) {},
			mockReadPositionRepoSetup: func(m *mockReadPositionRepository) {},
			params: params{
				req: &pmodel.GenericPositionSearchParams{
					PositionKeyword: "エンジニア",
				},
				cityIDs:          nil,
				jobTypeSmallIDs:  nil,
				industrySmallIDs: nil,
				theme:            pcontracts.PositionRecommendationTheme(""),
			},
			expected: expectedResult{
				positionIDs: nil,
				positions:   nil,
				err:         errors.New("Generating embeddings failed"),
			},
		},
		{
			name: "異常系: PositionRepositoryのSearchに失敗した場合、エラーを返す",
			mockMVGatewaySetup: func(m *mockMvGateway) {
				m.On("GetWillPositionList", mock.Anything, mock.Anything, mock.Anything).
					Return([]*iface.PositionListEntry{{PositionId: 101}, {PositionId: 102}}, nil).Once()
			},
			mockVectorizerRepoSetup: func(m *mockVectorizerRepository, keyword string) {
				m.On("GenerateEmbedding", keyword).Return(lo.ToPtr(embedding), nil).Once()
			},
			mockPositionRepoSetup: func(m *mockPositionRepository) {
				m.On("SemanticSearch", embedding.String(), http.DEFAULT_DISTANCE, mock.Anything).
					Return([]*position.PositionSearchResult{}, errors.New("Search failed")).Once()
			},
			mockReadPositionRepoSetup: func(m *mockReadPositionRepository) {
			},
			params: params{
				req: &pmodel.GenericPositionSearchParams{
					PositionKeyword: "エンジニア",
				},
				cityIDs:          nil,
				jobTypeSmallIDs:  nil,
				industrySmallIDs: nil,
				theme:            pcontracts.PositionRecommendationTheme(""),
			},
			expected: expectedResult{
				positionIDs: nil,
				positions:   nil,
				err:         errors.New("Search failed"),
			},
		},
		{
			name: "異常系: ReadPositionRepositoryのGetByIDsに失敗した場合、エラーを返す",
			mockMVGatewaySetup: func(m *mockMvGateway) {
				m.On("GetWillPositionList", mock.Anything, mock.Anything, mock.Anything).
					Return([]*iface.PositionListEntry{{PositionId: 101}, {PositionId: 102}}, nil).Once()
			},
			mockVectorizerRepoSetup: func(m *mockVectorizerRepository, keyword string) {
				m.On("GenerateEmbedding", keyword).Return(lo.ToPtr(embedding), nil).Once()
			},
			mockPositionRepoSetup: func(m *mockPositionRepository) {
				m.On("SemanticSearch", embedding.String(), http.DEFAULT_DISTANCE, mock.Anything).
					Return([]*position.PositionSearchResult{{ID: 101, Distance: 0.1}}, nil).Once()
			},
			mockReadPositionRepoSetup: func(m *mockReadPositionRepository) {
				m.On("GetByIDs", []uaposition.ID{101}).Return(uaposition.Positions{}, errors.New("GetByIDs failed")).Once()
			},
			params: params{
				req: &pmodel.GenericPositionSearchParams{
					PositionKeyword: "エンジニア",
				},
				cityIDs:          nil,
				jobTypeSmallIDs:  nil,
				industrySmallIDs: nil,
				theme:            pcontracts.PositionRecommendationTheme(""),
			},
			expected: expectedResult{
				positionIDs: nil,
				positions:   nil,
				err:         errors.New("GetByIDs failed"),
			},
		},
	}

	runCase := func(tt struct {
		name                      string
		mockMVGatewaySetup        func(m *mockMvGateway)
		mockVectorizerRepoSetup   func(m *mockVectorizerRepository, keyword string)
		mockPositionRepoSetup     func(m *mockPositionRepository)
		mockReadPositionRepoSetup func(m *mockReadPositionRepository)
		params                    params
		expected                  expectedResult
	}) {
		t.Run(tt.name, func(t *testing.T) {
			mockLogger := new(tmock.MockLogger)
			mockVectorizerRepo := new(mockVectorizerRepository)
			mockMVGateway := new(mockMvGateway)
			mockPositionRepo := new(mockPositionRepository)
			mockReadPositionRepo := new(mockReadPositionRepository)
			tt.mockMVGatewaySetup(mockMVGateway)
			tt.mockVectorizerRepoSetup(mockVectorizerRepo, tt.params.req.PositionKeyword)
			tt.mockPositionRepoSetup(mockPositionRepo)
			tt.mockReadPositionRepoSetup(mockReadPositionRepo)

			allPositionIds, positions, err := NewGenericSearchUseCase(
				mockLogger,
				mockMVGateway,
				mockVectorizerRepo,
				mockPositionRepo,
				mockReadPositionRepo,
				nil,
				nil,
			).Execute(
				t.Context(),
				tt.params.req,
				tt.params.cityIDs,
				tt.params.jobTypeSmallIDs,
				tt.params.theme,
			)

			// 結果を確認
			assert.Equal(t, tt.expected.positionIDs, allPositionIds)
			assert.Equal(t, tt.expected.positions, positions)
			if tt.expected.err != nil {
				assert.EqualError(t, err, tt.expected.err.Error())
			} else {
				assert.Nil(t, err)
			}
			mockMVGateway.AssertExpectations(t)
			mockVectorizerRepo.AssertExpectations(t)
			mockPositionRepo.AssertExpectations(t)
			mockReadPositionRepo.AssertExpectations(t)
		})
	}

	runCase(tests[0])
	runCase(tests[1])
	runCase(tests[2])
	runCase(tests[3])
	runCase(tests[4])
	runCase(tests[5])
	runCase(tests[6])
	runCase(tests[7])
}
