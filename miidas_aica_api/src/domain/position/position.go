package position

import (
	miidasPosition "aica/api/domain/user/apply/position"

	"github.com/pgvector/pgvector-go"
)

type PositionVector struct {
	// EmbeddingUuid string `gorm:"column:embedding_uuid"`
	PositionID miidasPosition.ID
	ChunkSeq   int
	Chunk      string
	Embedding  pgvector.Vector `pg:"type:vector(1024)"`
}

func (PositionVector) TableName() string {
	return "position_vector"
}
