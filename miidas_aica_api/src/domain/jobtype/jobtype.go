package jobtype

import "github.com/pgvector/pgvector-go"

type JobTypeSmall struct {
	ID          int
	Name        string
	Description string
}

func (JobTypeSmall) TableName() string {
	return "job_type_small"
}

type JobTypeSmallVector struct {
	JobTypeSmallID int
	ChunkSeq       int
	Chunk          string
	Embedding      pgvector.Vector `pg:"type:vector(1024)"`
}

func (JobTypeSmallVector) TableName() string {
	return "job_type_small_vector"
}
