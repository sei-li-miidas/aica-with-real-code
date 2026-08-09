package position

import (
	"aica/api/cli/domain/aica"
	"aica/api/domain/position"
	"aica/api/domain/provider"
	miidasPosition "aica/api/domain/user/apply/position"
	"aica/api/domain/vectorizer"
	"aica/api/sdk/logger"
	"errors"
	"testing"
	"time"

	"github.com/pgvector/pgvector-go"
	"github.com/samber/lo"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// MockLogger logger.LevelLoggerのモック
type MockLogger struct{}

func (m *MockLogger) Info(message string, fields ...any)  {}
func (m *MockLogger) Error(message string, fields ...any) {}
func (m *MockLogger) Warn(message string, fields ...any)  {}
func (m *MockLogger) Fatal(message string, fields ...any) {}

// mockMigrationRepository MigrationRepositoryのモック
type mockMigrationRepository struct {
	mock.Mock
}

func (m *mockMigrationRepository) GetLastImportedAtAndSourceID(tableName string) (*time.Time, *int, error) {
	args := m.Called(tableName)
	return args.Get(0).(*time.Time), args.Get(1).(*int), args.Error(2)
}

func (m *mockMigrationRepository) Save(migration *aica.Migrations) error {
	args := m.Called(migration)
	return args.Error(0)
}

// mockMiidasPositionRepository MiidasPositionRepositoryのモック
type mockMiidasPositionRepository struct {
	mock.Mock
}

func (m *mockMiidasPositionRepository) GetLatest(
	importedAt time.Time,
	sourceID int,
	chunkSize int,
) (miidasPosition.Positions, error) {
	args := m.Called(importedAt, sourceID, chunkSize)
	return args.Get(0).(miidasPosition.Positions), args.Error(1)
}

// mockPositionVectorRepository PositionVectorRepositoryのモック
type mockPositionVectorRepository struct {
	mock.Mock
}

func (m *mockPositionVectorRepository) Create(positionVectors []*position.PositionVector) error {
	args := m.Called(positionVectors)
	return args.Error(0)
}

func (m *mockPositionVectorRepository) Delete(positionID []miidasPosition.ID) error {
	args := m.Called(positionID)
	return args.Error(0)
}

// mockVectorizerFactory VectorizerFactoryのモック
type mockVectorizerFactory struct {
	mock.Mock
}

func (m *mockVectorizerFactory) NewVectorizerRepository(
	p provider.Provider,
	logger logger.LevelLogger,
) (vectorizer.VectorizerRepository, error) {
	args := m.Called(p, logger)
	return args.Get(0).(vectorizer.VectorizerRepository), args.Error(1)
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

func newTestPosition(id int, publishedAt *time.Time, importedAt time.Time) *miidasPosition.Position {
	p := &miidasPosition.Position{
		ID:          miidasPosition.ID(id),
		PublishedAt: publishedAt,
		ImportedAt:  importedAt,
	}
	return p
}

func Test_VectorizerUseCase_Execute(t *testing.T) {
	tests := []struct {
		name                              string
		lastMigration                     *aica.Migrations
		positions                         miidasPosition.Positions
		mockMigrationRepositorySetup      func(m *mockMigrationRepository, lastImportedAt *time.Time, lastSourceID *int)
		mockMiidasPositionRepositorySetup func(m *mockMiidasPositionRepository, positions miidasPosition.Positions)
		mockPositionVectorRepositorySetup func(m *mockPositionVectorRepository)
		mockVectorizerFactorySetup        func(m *mockVectorizerFactory, mockLogger *MockLogger, mockVectorizerRepo *mockVectorizerRepository)
		mockVectorizerRepoSetup           func(m *mockVectorizerRepository)
		expected                          error
	}{
		{
			name: "正常系: 公開済みと非公開の両方のポジションが存在する場合",
			lastMigration: &aica.Migrations{
				ID:             1,
				Name:           "position",
				LastImportedAt: time.Now().Add(-24 * time.Hour),
				LastSourceID:   100,
			},
			positions: miidasPosition.Positions{
				// 公開済みと非公開の両方を含む
				newTestPosition(1, lo.ToPtr(time.Now().Add(-1*time.Hour)), time.Now().Add(-2*time.Hour)),
				newTestPosition(2, nil, time.Now().Add(-4*time.Hour)),
			},
			mockMigrationRepositorySetup: func(m *mockMigrationRepository, lastImportedAt *time.Time, lastSourceID *int) {
				m.On("GetLastImportedAtAndSourceID", "position").Return(lastImportedAt, lastSourceID, nil).Once()
				m.On("Save", mock.Anything).Return(nil).Once()
			},
			mockMiidasPositionRepositorySetup: func(m *mockMiidasPositionRepository, positions miidasPosition.Positions) {
				// 1回目：データあり
				m.On("GetLatest", mock.Anything, mock.Anything, 2).Return(positions, nil).Once()
				// 2回目：データなし
				m.On("GetLatest", mock.Anything, mock.Anything, 2).Return(miidasPosition.Positions{}, nil).Once()
			},
			mockPositionVectorRepositorySetup: func(m *mockPositionVectorRepository) {
				m.On("Create", mock.Anything).Return(nil).Once()
				m.On("Delete", mock.Anything).Return(nil).Twice() // 公開済みと非公開の両方で呼ばれる
			},
			mockVectorizerFactorySetup: func(m *mockVectorizerFactory, mockLogger *MockLogger, mockVectorizerRepo *mockVectorizerRepository) {
				m.On("NewVectorizerRepository", provider.ProviderOpenAI, mockLogger).Return(mockVectorizerRepo, nil).Once()
			},
			mockVectorizerRepoSetup: func(m *mockVectorizerRepository) {
				m.On("GenerateEmbeddings", mock.Anything).Return([]*vectorizer.EmbeddingResult{}, nil).Once()
			},
			expected: nil,
		},
		{
			name: "正常系: 公開済のポジションのみ存在する場合",
			lastMigration: &aica.Migrations{
				ID:             1,
				Name:           "position",
				LastImportedAt: time.Now().Add(-24 * time.Hour),
				LastSourceID:   100,
			},
			positions: miidasPosition.Positions{
				newTestPosition(1, lo.ToPtr(time.Now().Add(-1*time.Hour)), time.Now().Add(-2*time.Hour)),
				newTestPosition(2, lo.ToPtr(time.Now().Add(-2*time.Hour)), time.Now().Add(-4*time.Hour)),
			},
			mockMigrationRepositorySetup: func(m *mockMigrationRepository, lastImportedAt *time.Time, lastSourceID *int) {
				m.On("GetLastImportedAtAndSourceID", "position").Return(lastImportedAt, lastSourceID, nil).Once()
				m.On("Save", mock.Anything).Return(nil).Twice() // ループごとに呼ばれる
			},
			mockMiidasPositionRepositorySetup: func(m *mockMiidasPositionRepository, positions miidasPosition.Positions) {
				// 1回目：データあり
				m.On("GetLatest", mock.Anything, mock.Anything, 2).Return(positions, nil).Once()
				// 2回目：データあり
				m.On("GetLatest", mock.Anything, mock.Anything, 2).Return(positions, nil).Once()
				// 3回目：データなし
				m.On("GetLatest", mock.Anything, mock.Anything, 2).Return(miidasPosition.Positions{}, nil).Once()
			},
			mockPositionVectorRepositorySetup: func(m *mockPositionVectorRepository) {
				m.On("Create", mock.Anything).Return(nil).Twice()
				m.On("Delete", mock.Anything).Return(nil).Twice()
			},
			mockVectorizerFactorySetup: func(m *mockVectorizerFactory, mockLogger *MockLogger, mockVectorizerRepo *mockVectorizerRepository) {
				m.On("NewVectorizerRepository", provider.ProviderOpenAI, mockLogger).Return(mockVectorizerRepo, nil).Twice()
			},
			mockVectorizerRepoSetup: func(m *mockVectorizerRepository) {
				m.On("GenerateEmbeddings", mock.Anything).Return([]*vectorizer.EmbeddingResult{}, nil).Twice()
			},
			expected: nil,
		},
		{
			name: "正常系: 非公開のポジションのみ存在する場合",
			lastMigration: &aica.Migrations{
				ID:             1,
				Name:           "position",
				LastImportedAt: time.Now().Add(-24 * time.Hour),
				LastSourceID:   100,
			},
			positions: miidasPosition.Positions{
				newTestPosition(1, nil, time.Now().Add(-2*time.Hour)),
				newTestPosition(2, nil, time.Now().Add(-4*time.Hour)),
			},
			mockMigrationRepositorySetup: func(m *mockMigrationRepository, lastImportedAt *time.Time, lastSourceID *int) {
				m.On("GetLastImportedAtAndSourceID", "position").Return(lastImportedAt, lastSourceID, nil).Once()
				m.On("Save", mock.Anything).Return(nil).Twice()
			},
			mockMiidasPositionRepositorySetup: func(m *mockMiidasPositionRepository, positions miidasPosition.Positions) {
				// 1回目：データあり
				m.On("GetLatest", mock.Anything, mock.Anything, 2).Return(positions, nil).Once()
				// 2回目：データあり
				m.On("GetLatest", mock.Anything, mock.Anything, 2).Return(positions, nil).Once()
				// 3回目：データなし
				m.On("GetLatest", mock.Anything, mock.Anything, 2).Return(miidasPosition.Positions{}, nil).Once()
			},
			mockPositionVectorRepositorySetup: func(m *mockPositionVectorRepository) {
				m.On("Delete", mock.Anything).Return(nil).Twice()
			},
			mockVectorizerFactorySetup: func(m *mockVectorizerFactory, mockLogger *MockLogger, mockVectorizerRepo *mockVectorizerRepository) {
				// モックは呼ばれない
			},
			mockVectorizerRepoSetup: func(m *mockVectorizerRepository) {
				// モックは呼ばれない
			},
			expected: nil,
		},
		{
			name: "異常系: ポジション取得時にエラーが発生した場合、マイグレーションデータが保存されること",
			lastMigration: &aica.Migrations{
				ID:             1,
				Name:           "position",
				LastImportedAt: time.Now().Add(-24 * time.Hour),
				LastSourceID:   100,
			},
			positions: miidasPosition.Positions{},
			mockMigrationRepositorySetup: func(m *mockMigrationRepository, lastImportedAt *time.Time, lastSourceID *int) {
				m.On("GetLastImportedAtAndSourceID", "position").Return(lastImportedAt, lastSourceID, nil).Once()
				m.On("Save", mock.Anything).Return(nil).Once()
			},
			mockMiidasPositionRepositorySetup: func(m *mockMiidasPositionRepository, positions miidasPosition.Positions) {
				m.On("GetLatest", mock.Anything, mock.Anything, 2).Return(positions, errors.New("GetLatest error")).Once()
			},
			mockPositionVectorRepositorySetup: func(m *mockPositionVectorRepository) {
			},
			mockVectorizerFactorySetup: func(m *mockVectorizerFactory, mockLogger *MockLogger, mockVectorizerRepo *mockVectorizerRepository) {
			},
			mockVectorizerRepoSetup: func(m *mockVectorizerRepository) {
			},
			expected: errors.New("GetLatest error"),
		},
		{
			name: "異常系: エンべディング処理でエラーが発生した場合、マイグレーションデータが保存されること",
			lastMigration: &aica.Migrations{
				ID:             1,
				Name:           "position",
				LastImportedAt: time.Now().Add(-24 * time.Hour),
				LastSourceID:   100,
			},
			positions: miidasPosition.Positions{
				newTestPosition(1, lo.ToPtr(time.Now().Add(-1*time.Hour)), time.Now().Add(-2*time.Hour)),
				newTestPosition(2, lo.ToPtr(time.Now().Add(-2*time.Hour)), time.Now().Add(-4*time.Hour)),
			},
			mockMigrationRepositorySetup: func(m *mockMigrationRepository, lastImportedAt *time.Time, lastSourceID *int) {
				m.On("GetLastImportedAtAndSourceID", "position").Return(lastImportedAt, lastSourceID, nil).Once()
				m.On("Save", mock.Anything).Return(nil).Once()
			},
			mockMiidasPositionRepositorySetup: func(m *mockMiidasPositionRepository, positions miidasPosition.Positions) {
				m.On("GetLatest", mock.Anything, mock.Anything, 2).Return(positions, nil).Once()
			},
			mockPositionVectorRepositorySetup: func(m *mockPositionVectorRepository) {
				m.On("Delete", mock.Anything).Return(nil).Once()
			},
			mockVectorizerFactorySetup: func(m *mockVectorizerFactory, mockLogger *MockLogger, mockVectorizerRepo *mockVectorizerRepository) {
				m.On("NewVectorizerRepository", provider.ProviderOpenAI, mockLogger).Return(mockVectorizerRepo, nil).Once()
			},
			mockVectorizerRepoSetup: func(m *mockVectorizerRepository) {
				m.On("GenerateEmbeddings", mock.Anything).Return([]*vectorizer.EmbeddingResult{}, errors.New("GenerateEmbeddings error")).Once()
			},
			expected: errors.New("GenerateEmbeddings error"),
		},
		{
			name: "異常系: 非公開ポジションの削除処理でエラーが発生した場合に、マイグレーションデータが保存されること",
			lastMigration: &aica.Migrations{
				ID:             1,
				Name:           "position",
				LastImportedAt: time.Now().Add(-24 * time.Hour),
				LastSourceID:   100,
			},
			positions: miidasPosition.Positions{
				newTestPosition(1, nil, time.Now().Add(-2*time.Hour)),
				newTestPosition(2, nil, time.Now().Add(-4*time.Hour)),
			},
			mockMigrationRepositorySetup: func(m *mockMigrationRepository, lastImportedAt *time.Time, lastSourceID *int) {
				m.On("GetLastImportedAtAndSourceID", "position").Return(lastImportedAt, lastSourceID, nil).Once()
				m.On("Save", mock.Anything).Return(nil).Once()
			},
			mockMiidasPositionRepositorySetup: func(m *mockMiidasPositionRepository, positions miidasPosition.Positions) {
				m.On("GetLatest", mock.Anything, mock.Anything, 2).Return(positions, nil).Once()
			},
			mockPositionVectorRepositorySetup: func(m *mockPositionVectorRepository) {
				m.On("Delete", mock.Anything).Return(errors.New("Delete error")).Once()
			},
			mockVectorizerFactorySetup: func(m *mockVectorizerFactory, mockLogger *MockLogger, mockVectorizerRepo *mockVectorizerRepository) {
			},
			mockVectorizerRepoSetup: func(m *mockVectorizerRepository) {
			},
			expected: errors.New("Delete error"),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// モックインスタンスを作成
			mockLogger := new(MockLogger)
			mockMigrationRepo := new(mockMigrationRepository)
			mockMiidasPositionRepo := new(mockMiidasPositionRepository)
			mockPositionVectorRepo := new(mockPositionVectorRepository)
			mockVectorizerRepo := new(mockVectorizerRepository)
			mockVectorizerFac := new(mockVectorizerFactory)
			// モックの振る舞いを定義
			tt.mockMigrationRepositorySetup(mockMigrationRepo, &tt.lastMigration.LastImportedAt, &tt.lastMigration.LastSourceID)
			tt.mockMiidasPositionRepositorySetup(mockMiidasPositionRepo, tt.positions)
			tt.mockPositionVectorRepositorySetup(mockPositionVectorRepo)
			tt.mockVectorizerFactorySetup(mockVectorizerFac, mockLogger, mockVectorizerRepo)
			tt.mockVectorizerRepoSetup(mockVectorizerRepo)

			// 実行
			err := NewVectorizerUseCase(
				mockLogger,
				mockMigrationRepo,
				mockMiidasPositionRepo,
				mockPositionVectorRepo,
				func(p provider.Provider, logger logger.LevelLogger) (vectorizer.VectorizerRepository, error) {
					return mockVectorizerFac.NewVectorizerRepository(p, logger)
				},
				provider.ProviderOpenAI,
				2,
			).Execute()

			// 結果を確認
			assert.Equal(t, tt.expected, err)
			// モックが期待通りに呼び出されたことを確認
			mockMigrationRepo.AssertExpectations(t)
			mockMiidasPositionRepo.AssertExpectations(t)
			mockPositionVectorRepo.AssertExpectations(t)
			mockVectorizerFac.AssertExpectations(t)
			mockVectorizerRepo.AssertExpectations(t)
		})
	}
}
