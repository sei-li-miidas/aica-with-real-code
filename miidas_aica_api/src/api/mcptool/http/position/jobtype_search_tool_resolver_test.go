package position

import (
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	"aica/api/domain/jobtype"
	"errors"
	"reflect"
	"testing"
)

func TestCachedJobTypeSearchToolResolver_NilRepoIsSafe(t *testing.T) {
	resolver := newCachedJobTypeSearchToolResolver(nil)

	if got := resolver.ToolNameByJobtypeName("SE"); got != "" {
		t.Fatalf("expected empty tool name when repo is nil, got: %q", got)
	}

	if got := resolver.JobtypeNamesByToolName("search_job_postings"); got != nil {
		t.Fatalf("expected nil names when repo is nil, got: %#v", got)
	}
}

func TestCachedJobTypeSearchToolResolver_RetriesAfterLoadFailure(t *testing.T) {
	attempts := 0
	resolver := newCachedJobTypeSearchToolResolver(nil)
	resolver.loadMappings = func() ([]*jobtype.JobTypePositionSearchToolMapping, error) {
		attempts++
		if attempts == 1 {
			return nil, errors.New("temporary db failure")
		}
		return []*jobtype.JobTypePositionSearchToolMapping{
			{
				JobTypeName: "Webアプリ開発",
				ToolName:    pcontracts.ToolNameSearchJobPostingsForITEngineer,
			},
			{
				JobTypeName: "金融営業（法人）",
				ToolName:    pcontracts.ToolNameSearchJobPostingsForSalesFinancialSales,
			},
		}, nil
	}

	if got := resolver.ToolNameByJobtypeName("Webアプリ開発"); got != "" {
		t.Fatalf("expected empty tool name on initial load failure, got %q", got)
	}

	if got := resolver.ToolNameByJobtypeName("Webアプリ開発"); got != pcontracts.ToolNameSearchJobPostingsForITEngineer {
		t.Fatalf("expected resolver to retry and load IT mapping, got %q", got)
	}

	gotNames := resolver.JobtypeNamesByToolName(pcontracts.ToolNameSearchJobPostingsForSalesFinancialSales)
	wantNames := []string{"金融営業（法人）"}
	if !reflect.DeepEqual(gotNames, wantNames) {
		t.Fatalf("expected loaded financial sales mappings, got %#v", gotNames)
	}

	if attempts != 2 {
		t.Fatalf("expected 2 load attempts, got %d", attempts)
	}
}
