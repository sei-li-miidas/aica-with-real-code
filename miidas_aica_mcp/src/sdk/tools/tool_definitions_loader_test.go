package tools

import (
	"encoding/json"
	"io/fs"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
)

func TestLoadToolDefinitions(t *testing.T) {
	t.Run("定義を読み込み名前順にソートする", func(t *testing.T) {
		dir := t.TempDir()
		writeToolDefFile(t, dir, "b.tool.json", map[string]any{
			"name":        "b_tool",
			"description": "b",
			"parameters": map[string]any{
				"type": "object",
			},
		})
		writeToolDefFile(t, dir, "a.tool.json", map[string]any{
			"name":        "a_tool",
			"description": "a",
			"parameters": map[string]any{
				"type": "object",
			},
		})

		defs, err := loadToolDefinitionsFromDir(dir)
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}

		if len(defs) != 2 {
			t.Fatalf("expected 2 definitions, got %d", len(defs))
		}

		if defs[0].Name != "a_tool" || defs[1].Name != "b_tool" {
			t.Fatalf("definitions are not sorted by name: %v, %v", defs[0].Name, defs[1].Name)
		}
	})

	t.Run("定義名が重複している場合は失敗する", func(t *testing.T) {
		dir := t.TempDir()
		writeToolDefFile(t, dir, "a.tool.json", map[string]any{
			"name":        "dup_tool",
			"description": "a",
			"parameters": map[string]any{
				"type": "object",
			},
		})
		writeToolDefFile(t, dir, "b.tool.json", map[string]any{
			"name":        "dup_tool",
			"description": "b",
			"parameters": map[string]any{
				"type": "object",
			},
		})

		_, err := loadToolDefinitionsFromDir(dir)
		if err == nil || !strings.Contains(err.Error(), "duplicate tool definition name") {
			t.Fatalf("expected duplicate name error, got: %v", err)
		}
	})

	t.Run("parametersがオブジェクトでない場合は失敗する", func(t *testing.T) {
		dir := t.TempDir()
		writeToolDefFile(t, dir, "a.tool.json", map[string]any{
			"name":        "a_tool",
			"description": "a",
			"parameters":  "not-an-object",
		})

		_, err := loadToolDefinitionsFromDir(dir)
		if err == nil || !strings.Contains(err.Error(), "parameters must be json object") {
			t.Fatalf("expected parameters object error, got: %v", err)
		}
	})
}

func TestValidateToolDefinitionsAgainstHandlers(t *testing.T) {
	originalHandlers := ToolHanders
	t.Cleanup(func() {
		ToolHanders = originalHandlers
	})

	ToolHanders = map[string]createToolHandlerFunc{
		"tool_a": nil,
		"tool_b": nil,
	}

	t.Run("ツール定義とツールハンドラーに不足がある場合は失敗する", func(t *testing.T) {
		defs := []*ToolDefinition{
			{Name: "tool_a"},
			{Name: "tool_extra"},
		}
		err := ValidateToolDefinitionsAgainstHandlers(defs)
		if err == nil {
			t.Fatal("expected error, got nil")
		}

		msg := err.Error()
		if !strings.Contains(msg, "tool_extra") || !strings.Contains(msg, "tool_b") {
			t.Fatalf("unexpected mismatch message: %v", msg)
		}
	})
}

func TestRepositoryToolDefinitionsMatchHandlers(t *testing.T) {
	var defs []*ToolDefinition

	t.Run("埋め込み済みツール定義を読み込む", func(t *testing.T) {
		var err error
		defs, err = LoadToolDefinitionsEmbedded()
		if err != nil {
			t.Fatalf("load definitions: %v", err)
		}
	})

	t.Run("ツール定義と登録済みハンドラーが一致する", func(t *testing.T) {
		if err := ValidateToolDefinitionsAgainstHandlers(defs); err != nil {
			t.Fatalf("validate definitions against handlers: %v", err)
		}
	})
}

func TestNormalizeParametersSchema(t *testing.T) {
	t.Run("requiredとpropertiesを補完する", func(t *testing.T) {
		raw := json.RawMessage(`{"type":"object","properties":{"Foo":{"type":"string"}},"required":["Foo"]}`)
		normalized, err := NormalizeParametersSchema(raw)
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}

		var got map[string]any
		if err := json.Unmarshal(normalized, &got); err != nil {
			t.Fatalf("unmarshal normalized: %v", err)
		}

		requiredList, ok := got["required"].([]any)
		if !ok {
			t.Fatalf("required should be []any, got %T", got["required"])
		}
		requiredStrings := make([]string, 0, len(requiredList))
		for _, item := range requiredList {
			requiredStrings = append(requiredStrings, item.(string))
		}

		expected := []string{"Foo", "SessionID", "RequestID"}
		if !reflect.DeepEqual(requiredStrings, expected) {
			t.Fatalf("unexpected required list: got=%v want=%v", requiredStrings, expected)
		}

		properties, ok := got["properties"].(map[string]any)
		if !ok {
			t.Fatalf("properties should be object, got %T", got["properties"])
		}
		if _, ok := properties["SessionID"]; !ok {
			t.Fatal("SessionID property is missing")
		}
		if _, ok := properties["RequestID"]; !ok {
			t.Fatal("RequestID property is missing")
		}
	})

	t.Run("requiredの重複を排除する", func(t *testing.T) {
		raw := json.RawMessage(`{"type":"object","required":["SessionID","RequestID","SessionID"]}`)
		normalized, err := NormalizeParametersSchema(raw)
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}

		var got map[string]any
		if err := json.Unmarshal(normalized, &got); err != nil {
			t.Fatalf("unmarshal normalized: %v", err)
		}
		requiredList := got["required"].([]any)
		if len(requiredList) != 2 {
			t.Fatalf("expected 2 required entries after dedup, got %d (%v)", len(requiredList), requiredList)
		}
	})

	t.Run("requiredの形式が不正な場合は失敗する", func(t *testing.T) {
		raw := json.RawMessage(`{"type":"object","required":"SessionID"}`)
		_, err := NormalizeParametersSchema(raw)
		if err == nil || !strings.Contains(err.Error(), "required must be an array") {
			t.Fatalf("expected required array error, got: %v", err)
		}
	})

	t.Run("propertiesの形式が不正な場合は失敗する", func(t *testing.T) {
		raw := json.RawMessage(`{"type":"object","properties":"invalid"}`)
		_, err := NormalizeParametersSchema(raw)
		if err == nil || !strings.Contains(err.Error(), "properties must be an object") {
			t.Fatalf("expected properties object error, got: %v", err)
		}
	})
}

func writeToolDefFile(t *testing.T, dir, name string, data map[string]any) {
	t.Helper()
	content, err := json.Marshal(data)
	if err != nil {
		t.Fatalf("marshal tool def: %v", err)
	}
	if err := os.WriteFile(filepath.Join(dir, name), content, 0o644); err != nil {
		t.Fatalf("write tool def file: %v", err)
	}
}

func loadToolDefinitionsFromDir(dir string) ([]*ToolDefinition, error) {
	fsys := os.DirFS(dir)
	_, statErr := fs.Stat(fsys, ".")
	if statErr != nil {
		return nil, statErr
	}
	return loadToolDefinitionsFromFS(fsys)
}
