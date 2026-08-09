package tools

import (
	"encoding/json"
	"fmt"
)

const (
	sessionIDKey = "SessionID"
	requestIDKey = "RequestID"
)

func sessionIDProperty() map[string]any {
	return map[string]any{
		"type":        "string",
		"description": "セッションID",
	}
}

func requestIDProperty() map[string]any {
	return map[string]any{
		"type":        "string",
		"description": "リクエストID。なるべく重複しないよう任意のuuidを生成して、リクエストごとにユニークな値を設定してください",
	}
}

func NormalizeParametersSchema(raw json.RawMessage) (json.RawMessage, error) {
	var parameters map[string]any
	if err := json.Unmarshal(raw, &parameters); err != nil {
		return nil, fmt.Errorf("unmarshal parameters: %w", err)
	}

	requiredRaw, hasRequired := parameters["required"]
	required := make([]string, 0, 2)
	seen := map[string]struct{}{}
	if hasRequired {
		requiredList, ok := requiredRaw.([]any)
		if !ok {
			return nil, fmt.Errorf("required must be an array")
		}
		for _, item := range requiredList {
			s, ok := item.(string)
			if !ok {
				return nil, fmt.Errorf("required must contain only strings")
			}
			if _, exists := seen[s]; exists {
				continue
			}
			seen[s] = struct{}{}
			required = append(required, s)
		}
	}

	if _, exists := seen[sessionIDKey]; !exists {
		required = append(required, sessionIDKey)
		seen[sessionIDKey] = struct{}{}
	}
	if _, exists := seen[requestIDKey]; !exists {
		required = append(required, requestIDKey)
	}
	parameters["required"] = required

	propertiesRaw, hasProperties := parameters["properties"]
	properties := map[string]any{}
	if hasProperties {
		var ok bool
		properties, ok = propertiesRaw.(map[string]any)
		if !ok {
			return nil, fmt.Errorf("properties must be an object")
		}
	}

	properties[sessionIDKey] = sessionIDProperty()
	properties[requestIDKey] = requestIDProperty()
	parameters["properties"] = properties

	normalized, err := json.Marshal(parameters)
	if err != nil {
		return nil, fmt.Errorf("marshal normalized parameters: %w", err)
	}

	return json.RawMessage(normalized), nil
}
