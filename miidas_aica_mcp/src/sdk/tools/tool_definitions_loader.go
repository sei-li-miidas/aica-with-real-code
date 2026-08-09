package tools

import (
	"encoding/json"
	"fmt"
	"io/fs"
	"sort"
	"strings"
)

type ToolDefinition struct {
	Name        string          `json:"name"`
	Description string          `json:"description"`
	Parameters  json.RawMessage `json:"parameters"`
}

// LoadToolDefinitionsEmbedded loads tool definitions from files embedded in the binary
func LoadToolDefinitionsEmbedded() ([]*ToolDefinition, error) {
	return loadToolDefinitionsFromFS(toolDefinitionsFS)
}

func loadToolDefinitionsFromFS(fsys fs.FS) ([]*ToolDefinition, error) {
	entries, err := fs.ReadDir(fsys, ".")
	if err != nil {
		return nil, fmt.Errorf("read tool definitions: %w", err)
	}

	definitions := make([]*ToolDefinition, 0)
	seen := make(map[string]string)

	for _, entry := range entries {
		if entry.IsDir() || !strings.HasSuffix(entry.Name(), ".tool.json") {
			continue
		}

		data, err := fs.ReadFile(fsys, entry.Name())
		if err != nil {
			return nil, fmt.Errorf("read tool definition %s: %w", entry.Name(), err)
		}

		var def ToolDefinition
		if err := json.Unmarshal(data, &def); err != nil {
			return nil, fmt.Errorf("parse tool definition %s: %w", entry.Name(), err)
		}

		if strings.TrimSpace(def.Name) == "" {
			return nil, fmt.Errorf("tool definition %s: name is required", entry.Name())
		}
		if strings.TrimSpace(def.Description) == "" {
			return nil, fmt.Errorf("tool definition %s: description is required", entry.Name())
		}
		if len(def.Parameters) == 0 {
			return nil, fmt.Errorf("tool definition %s: parameters is required", entry.Name())
		}

		var parameters map[string]any
		if err := json.Unmarshal(def.Parameters, &parameters); err != nil {
			return nil, fmt.Errorf("tool definition %s: parameters must be json object: %w", entry.Name(), err)
		}

		if previousPath, exists := seen[def.Name]; exists {
			return nil, fmt.Errorf("duplicate tool definition name %q in %s and %s", def.Name, previousPath, entry.Name())
		}
		seen[def.Name] = entry.Name()

		definitions = append(definitions, &def)
	}

	if len(definitions) == 0 {
		return nil, fmt.Errorf("no tool definitions found")
	}

	sort.Slice(definitions, func(i, j int) bool {
		return definitions[i].Name < definitions[j].Name
	})

	return definitions, nil
}

func ValidateToolDefinitionsAgainstHandlers(defs []*ToolDefinition) error {
	definitionSet := make(map[string]struct{}, len(defs))
	for _, def := range defs {
		definitionSet[def.Name] = struct{}{}
	}

	missingHandlers := make([]string, 0)
	for _, def := range defs {
		if _, ok := ToolHanders[def.Name]; !ok {
			missingHandlers = append(missingHandlers, def.Name)
		}
	}

	missingDefinitions := make([]string, 0)
	for handlerName := range ToolHanders {
		if _, ok := definitionSet[handlerName]; !ok {
			missingDefinitions = append(missingDefinitions, handlerName)
		}
	}

	sort.Strings(missingHandlers)
	sort.Strings(missingDefinitions)

	if len(missingHandlers) == 0 && len(missingDefinitions) == 0 {
		return nil
	}

	return fmt.Errorf("tool definitions mismatch: missing handlers for definitions=%v, missing definitions for handlers=%v", missingHandlers, missingDefinitions)
}
