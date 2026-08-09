package tools

import (
	"context"
	"fmt"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

type toolSearchJobPostingsForSalesFinancialSales struct {
	name string
}

func newToolSearchJobPostingsForSalesFinancialSales() *toolSearchJobPostingsForSalesFinancialSales {
	return &toolSearchJobPostingsForSalesFinancialSales{name: "search_job_postings_for_sales_financial_sales"}
}

func (t toolSearchJobPostingsForSalesFinancialSales) getName() string {
	return t.name
}

func (t toolSearchJobPostingsForSalesFinancialSales) createToolHandler(apiServer string, getProvider func() string) server.ToolHandlerFunc {
	// create TypedHandlerFunc
	handler := func(ctx context.Context,
		request mcp.CallToolRequest,
		args financialSalesPositionSearchParams) (*mcp.CallToolResult, error,
	) {
		logger, errorToolResult := initializeTool(t.name, &args.commonRequest)
		if errorToolResult != nil {
			return errorToolResult, nil
		}

		url := fmt.Sprintf("%s/aica/mcptool/positions/search/financial_sales", apiServer)
		return executeSearchJobPostingsRequest(logger, t.name, args.commonRequest, url, args), nil
	}

	// return server.ToolHandlerFunc
	return mcp.NewTypedToolHandler(handler)
}

func init() {
	tool := newToolSearchJobPostingsForSalesFinancialSales()
	addToolHandler(tool)
}
