package support

import (
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	"strings"
)

func RequestedJobTypeNames(input *pcontracts.JobSpecificSearchInput) []string {
	if input == nil {
		return nil
	}
	seen := map[string]struct{}{}
	names := make([]string, 0, len(input.JobTypeNames))
	for _, name := range input.JobTypeNames {
		n := strings.TrimSpace(name)
		if n == "" {
			continue
		}
		if _, ok := seen[n]; ok {
			continue
		}
		seen[n] = struct{}{}
		names = append(names, n)
	}
	return names
}

func ExtractPositionKeyword(input *pcontracts.JobSpecificSearchInput) string {
	if input == nil || input.Custom == nil {
		return ""
	}
	carrier, ok := input.Custom.(pcontracts.KeywordCarrier)
	if !ok {
		return ""
	}
	return strings.TrimSpace(carrier.Keyword())
}

func StringPtrIfNonEmpty(value string) *string {
	if strings.TrimSpace(value) == "" {
		return nil
	}
	v := value
	return &v
}
