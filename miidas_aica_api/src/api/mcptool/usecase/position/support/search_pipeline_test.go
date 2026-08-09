package support

import (
	"errors"
	"os"
	"testing"

	"miidas/m2/user/marketvalue/grpc/iface"

	"github.com/pgvector/pgvector-go"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"gorm.io/gorm"

	tmock "aica/api/api/mcptool/testutil/mock"
	pmodel "aica/api/api/mcptool/usecase/position/model"
	dposition "aica/api/domain/position"
	"aica/api/domain/user/apply/position"
	"aica/api/domain/vectorizer"
	"aica/api/sdk/http"
)

type stubVectorizer struct {
	vec *pgvector.Vector
	err error
}

func (s *stubVectorizer) GenerateEmbedding(_ string) (*pgvector.Vector, error) {
	return s.vec, s.err
}
func (s *stubVectorizer) GenerateEmbeddings(_ []*vectorizer.EmbeddingTarget) ([]*vectorizer.EmbeddingResult, error) {
	return nil, nil
}

type stubSemanticRepo struct {
	ret []*dposition.PositionSearchResult
	err error
}

func (s *stubSemanticRepo) SemanticSearch(_ string, _ float64, addConditions func(*gorm.DB) *gorm.DB) ([]*dposition.PositionSearchResult, error) {
	if addConditions != nil {
		func() {
			defer func() { _ = recover() }()
			_ = addConditions(&gorm.DB{})
		}()
	}
	return s.ret, s.err
}

type stubPositionGetter struct {
	ret position.Positions
	err error
}

func (s *stubPositionGetter) GetByIDs(_ []position.ID) (position.Positions, error) {
	return s.ret, s.err
}

func TestGetPositionSearchResultsFromPositionIDs_WithoutKeyword(t *testing.T) {
	got, err := GetPositionSearchResultsFromPositionIDs("", nil, nil, []position.ID{1, 2})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(got) != 2 || got[0].ID != 1 || got[1].ID != 2 {
		t.Fatalf("unexpected result: %+v", got)
	}
}

func TestGetPositionSearchResultsFromPositionIDs_WithKeyword(t *testing.T) {
	vec := pgvector.NewVector([]float32{0.1})
	got, err := GetPositionSearchResultsFromPositionIDs(
		"go",
		&stubVectorizer{vec: &vec},
		&stubSemanticRepo{ret: []*dposition.PositionSearchResult{
			{ID: 2, Distance: 0.1},
			{ID: 2, Distance: 0.2},
			{ID: 1, Distance: 0.3},
		}},
		[]position.ID{1, 2},
	)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(got) != 2 {
		t.Fatalf("expected deduped results, got %d", len(got))
	}
}

func TestSemanticSearch_Branches(t *testing.T) {
	t.Run("埋め込み生成がエラーになる場合", func(t *testing.T) {
		_, err := SemanticSearch(
			&stubVectorizer{err: errors.New("embedding failed")},
			&stubSemanticRepo{},
			&http.VectorSearchParams{Keyword: "go", Distance: 0.8},
			nil,
		)
		if err == nil {
			t.Fatalf("expected error")
		}
	})

	t.Run("リポジトリがエラーを返す場合", func(t *testing.T) {
		vec := pgvector.NewVector([]float32{0.1})
		_, err := SemanticSearch(
			&stubVectorizer{vec: &vec},
			&stubSemanticRepo{err: errors.New("repo failed")},
			&http.VectorSearchParams{Keyword: "go", Distance: 0.8},
			[]position.ID{1},
		)
		if err == nil {
			t.Fatalf("expected error")
		}
	})

	t.Run("正常に処理できる", func(t *testing.T) {
		vec := pgvector.NewVector([]float32{0.1})
		out, err := SemanticSearch(
			&stubVectorizer{vec: &vec},
			&stubSemanticRepo{ret: []*dposition.PositionSearchResult{{ID: 1}}},
			&http.VectorSearchParams{Keyword: "go", Distance: 0.8},
			[]position.ID{1},
		)
		if err != nil || len(out) != 1 {
			t.Fatalf("unexpected result: %v %v", out, err)
		}
	})
}

func TestFillPositionData_Branches(t *testing.T) {
	logger := &tmock.MockLogger{}
	t.Run("IDが空の場合", func(t *testing.T) {
		got, err := FillPositionData(&stubPositionGetter{}, logger, nil)
		if err != nil || len(got) != 0 {
			t.Fatalf("unexpected: %v %v", got, err)
		}
	})

	t.Run("リポジトリがエラーを返す場合", func(t *testing.T) {
		_, err := FillPositionData(&stubPositionGetter{err: errors.New("db failed")}, logger, []position.ID{1})
		if err == nil {
			t.Fatalf("expected error")
		}
	})

	t.Run("positionと画像パスが欠けている場合", func(t *testing.T) {
		t.Setenv("MIIDAS_S3_USER_ASSETS_ENDPOINT", "assets.example.com")
		got, err := FillPositionData(&stubPositionGetter{
			ret: position.Positions{
				{
					ID: 1,
					Detail: position.Detail{
						Title:       "t1",
						MainJobText: "m1",
						GuaranteedIncome: &position.GuaranteedIncome{
							BulkIncomeFrom: func() *int { v := 100; return &v }(),
							BulkIncomeTo:   func() *int { v := 200; return &v }(),
						},
						Images: position.Images{{DisplayType: 1, FilePath: "a.png"}},
					},
				},
			},
		}, logger, []position.ID{1, 2})
		if err != nil || len(got) != 1 || got[0].Image == "" {
			t.Fatalf("unexpected: %v %v", got, err)
		}
	})

	t.Run("画像URL生成時にエンドポイントが未設定の場合", func(t *testing.T) {
		_ = os.Unsetenv("MIIDAS_S3_USER_ASSETS_ENDPOINT")
		got, err := FillPositionData(&stubPositionGetter{
			ret: position.Positions{
				{
					ID: 1,
					Detail: position.Detail{
						Title:       "t1",
						MainJobText: "m1",
						Images:      position.Images{{DisplayType: 1, FilePath: "a.png"}},
					},
				},
			},
		}, logger, []position.ID{1})
		if err != nil || len(got) != 1 {
			t.Fatalf("unexpected: %v %v", got, err)
		}
	})
}

func TestExecutePositionSearch_Branches(t *testing.T) {
	logger := &tmock.MockLogger{}
	t.Run("gRPCがキャンセルされた場合", func(t *testing.T) {
		_, _, err := ExecutePositionSearch(
			logger,
			func(_ *iface.Company, _ *iface.Business, _ *iface.Position) ([]*iface.PositionListEntry, error) {
				return nil, status.Error(codes.Canceled, "canceled")
			},
			&iface.Company{},
			&iface.Business{},
			&iface.Position{Job: &iface.Job{Value: &iface.JobValue{}}},
			"",
			nil,
			nil,
			&stubPositionGetter{},
		)
		if err == nil {
			t.Fatalf("expected error")
		}
	})

	t.Run("一般的なゲートウェイエラーの場合", func(t *testing.T) {
		_, _, err := ExecutePositionSearch(
			logger,
			func(_ *iface.Company, _ *iface.Business, _ *iface.Position) ([]*iface.PositionListEntry, error) {
				return nil, errors.New("mv failed")
			},
			&iface.Company{},
			&iface.Business{},
			&iface.Position{Job: &iface.Job{Value: &iface.JobValue{}}},
			"",
			nil,
			nil,
			&stubPositionGetter{},
		)
		if err == nil {
			t.Fatalf("expected error")
		}
	})

	t.Run("リストが空の場合", func(t *testing.T) {
		ids, rows, err := ExecutePositionSearch(
			logger,
			func(_ *iface.Company, _ *iface.Business, _ *iface.Position) ([]*iface.PositionListEntry, error) {
				return []*iface.PositionListEntry{}, nil
			},
			&iface.Company{},
			&iface.Business{},
			&iface.Position{Job: &iface.Job{Value: &iface.JobValue{}}},
			"",
			nil,
			nil,
			&stubPositionGetter{},
		)
		if err != nil || ids != nil || rows != nil {
			t.Fatalf("unexpected result")
		}
	})

	t.Run("検索結果取得がエラーになる場合", func(t *testing.T) {
		_, _, err := ExecutePositionSearch(
			logger,
			func(_ *iface.Company, _ *iface.Business, _ *iface.Position) ([]*iface.PositionListEntry, error) {
				return []*iface.PositionListEntry{{PositionId: 1}}, nil
			},
			&iface.Company{},
			&iface.Business{},
			&iface.Position{Job: &iface.Job{Value: &iface.JobValue{}}},
			"go",
			&stubVectorizer{err: errors.New("emb failed")},
			&stubSemanticRepo{},
			&stubPositionGetter{},
		)
		if err == nil {
			t.Fatalf("expected error")
		}
	})

	t.Run("position補完でエラーになる場合", func(t *testing.T) {
		_, _, err := ExecutePositionSearch(
			logger,
			func(_ *iface.Company, _ *iface.Business, _ *iface.Position) ([]*iface.PositionListEntry, error) {
				return []*iface.PositionListEntry{{PositionId: 1}}, nil
			},
			&iface.Company{},
			&iface.Business{},
			&iface.Position{Job: &iface.Job{Value: &iface.JobValue{}}},
			"",
			nil,
			nil,
			&stubPositionGetter{err: errors.New("db failed")},
		)
		if err == nil {
			t.Fatalf("expected error")
		}
	})

	t.Run("正常に処理できる", func(t *testing.T) {
		t.Setenv("MIIDAS_S3_USER_ASSETS_ENDPOINT", "assets.example.com")
		ids, rows, err := ExecutePositionSearch(
			logger,
			func(_ *iface.Company, _ *iface.Business, _ *iface.Position) ([]*iface.PositionListEntry, error) {
				return []*iface.PositionListEntry{{PositionId: 1}, {PositionId: 2}}, nil
			},
			&iface.Company{},
			&iface.Business{},
			&iface.Position{Job: &iface.Job{Value: &iface.JobValue{}}},
			"",
			nil,
			nil,
			&stubPositionGetter{ret: position.Positions{{ID: 1}, {ID: 2}}},
		)
		if err != nil || len(ids) != 2 || len(rows) == 0 {
			t.Fatalf("unexpected result")
		}
	})
}

var _ pmodel.PositionSummary
