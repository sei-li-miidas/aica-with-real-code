package tools

import "embed"

//go:embed *.tool.json
var toolDefinitionsFS embed.FS
