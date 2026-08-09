package mockutil

import (
	"encoding/json"
	"io/fs"
	"os"
	"path/filepath"
	"runtime"
)

func MustLoadJSON[T any](fsys fs.FS, path string) T {
	var out T

	if _, filename, _, ok := runtime.Caller(1); ok {
		data, err := os.ReadFile(filepath.Join(filepath.Dir(filename), path))
		if err == nil {
			if err := json.Unmarshal(data, &out); err == nil {
				return out
			}
		}
	}

	data, err := fs.ReadFile(fsys, path)
	if err != nil {
		panic(err)
	}
	if err := json.Unmarshal(data, &out); err != nil {
		panic(err)
	}
	return out
}
