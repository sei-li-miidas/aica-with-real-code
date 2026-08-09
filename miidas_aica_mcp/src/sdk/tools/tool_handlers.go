package tools

import (
	"github.com/mark3labs/mcp-go/server"
)

type (
	createToolHandlerFunc func(apiServer string, getProvider func() string) server.ToolHandlerFunc
	toolHandler           interface {
		getName() string
		createToolHandler(apiServer string, getProvider func() string) server.ToolHandlerFunc
	}
)

var ToolHanders map[string]createToolHandlerFunc = make(map[string]createToolHandlerFunc)

func addToolHandler(handler toolHandler) {
	if _, ok := ToolHanders[handler.getName()]; ok {
		panic("tool handler already exists")
	}

	ToolHanders[handler.getName()] = handler.createToolHandler
}
