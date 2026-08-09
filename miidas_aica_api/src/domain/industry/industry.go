package industry

import "github.com/pgvector/pgvector-go"

type IndustrySmall struct {
	ID          int
	Name        string
	Description string
}

func (IndustrySmall) TableName() string {
	return "industry_small"
}

type IndustrySmallVector struct {
	IndustrySmallId int
	ChunkSeq        int
	Chunk           string
	Embedding       pgvector.Vector `pg:"type:vector(1024)"`
}

func (IndustrySmallVector) TableName() string {
	return "industry_small_vector"
}
