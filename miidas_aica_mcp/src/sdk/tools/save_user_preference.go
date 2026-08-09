package tools

import (
	"context"
	"encoding/json"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

type toolSaveUserPreferences struct {
	name string
}

func newToolSaveUserPreferences() *toolSaveUserPreferences {
	return &toolSaveUserPreferences{name: "save_user_preference"}
}

func (t toolSaveUserPreferences) getName() string {
	return t.name
}

func (t toolSaveUserPreferences) createToolHandler(apiServer string, getProvider func() string) server.ToolHandlerFunc {

	// create TypedHandlerFunc
	handler := func(ctx context.Context, request mcp.CallToolRequest, args saveUserPreferencesRequest) (*mcp.CallToolResult, error) {
		_, errorToolResult := initializeTool(t.name, &args.commonRequest)
		if errorToolResult != nil {
			return errorToolResult, nil
		}

		// Build result map
		resultMap := map[string]any{}

		// ポジション検索の際に給料が必須ですが、
		// このツールが呼び出されるときに、常にすべてのフィールドに値が入っているわけではない
		if isNegativePtrInt(args.Amount) {
			return NewErrorCallToolResultInvalidArgument("Amount"), nil
		}

		if args.Amount != nil {
			if !isBlankPtrString(args.Scope) && *args.Scope != "Minimum" {
				return NewErrorCallToolResultInvalidArgument("Scope"), nil
			}

			resultMap["Salary"] = *args.Amount
		}

		// Validate DayOff_Preference if provided
		if ptrStringNotIn(args.DayOffs, []string{
			"土日祝休み",
			"毎週2日休み",
			"その他",
		}) {
			return NewErrorCallToolResultInvalidArgument("DayOff_Preference"), nil
		}

		// Validate AverageOverTime_Preference if provided
		if !isBlankPtrString(args.AverageOvertime) && *args.AverageOvertime != "10時間以内" {
			return NewErrorCallToolResultInvalidArgument("AverageOverTime_Preference"), nil
		}

		if len(args.JobtypeNames) > 0 {
			resultMap["JobtypeNames"] = args.JobtypeNames
		}

		locations := []map[string]string{}
		if !isBlankPtrString(args.LocationPrefectureResidence) && !isBlankPtrString(args.LocationCityResidence) {

			locations = append(locations, map[string]string{
				"LocationType":   "居住地",
				"PrefectureName": *args.LocationPrefectureResidence,
				"CityName":       *args.LocationCityResidence,
			})
		}
		if !isBlankPtrString(args.LocationPrefecturePreference) && !isBlankPtrString(args.LocationCityPreference) {
			locations = append(locations, map[string]string{
				"LocationType":   "希望勤務地",
				"PrefectureName": *args.LocationPrefecturePreference,
				"CityName":       *args.LocationCityPreference,
			})
		}
		if len(locations) > 0 {
			resultMap["Locations"] = locations
		}

		if !isBlankPtrString(args.DayOffs) {
			resultMap["DayOffs"] = *args.DayOffs
		}

		if !isBlankPtrString(args.AverageOvertime) {
			resultMap["AverageOvertime"] = *args.AverageOvertime
		}

		if args.FullyRemoteWork != nil {
			resultMap["FullyRemoteWork"] = *args.FullyRemoteWork
		}

		resultMap[messageToLLMKey] = "情報を保存しました。"

		content, err := json.Marshal(resultMap)
		if err != nil {
			return NewErrorCallToolResult("情報を保存できませんでした。"), nil
		}

		return &mcp.CallToolResult{
			Content: []mcp.Content{
				mcp.NewTextContent(string(content)),
			},
		}, nil
	}

	// return server.ToolHandlerFunc
	return mcp.NewTypedToolHandler(handler)
}

func init() {
	tool := newToolSaveUserPreferences()
	addToolHandler(tool)
}
