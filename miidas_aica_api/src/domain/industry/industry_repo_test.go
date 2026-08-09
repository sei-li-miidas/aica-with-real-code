package industry

import (
	"testing"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

func TestIndustrySmallRepository_SemanticSearch_AddConditionsApplied(t *testing.T) {
	db, err := gorm.Open(postgres.New(postgres.Config{
		DSN: "host=localhost user=test dbname=test sslmode=disable",
	}), &gorm.Config{
		DryRun:               true,
		DisableAutomaticPing: true,
	})
	if err != nil {
		t.Fatalf("failed to open gorm dryrun db: %v", err)
	}

	repo := NewIndustrySmallRepository(db)
	called := false

	_, err = repo.SemanticSearch("embedding", 0.8, func(query *gorm.DB) *gorm.DB {
		called = true
		return query.Where("industry_small.id IN ?", []int{1, 2})
	})
	if err != nil {
		t.Fatalf("SemanticSearch returned unexpected error: %v", err)
	}
	if !called {
		t.Fatal("expected addConditions to be called")
	}
}
