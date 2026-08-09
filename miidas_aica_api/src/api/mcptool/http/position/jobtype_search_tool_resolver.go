package position

import (
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	"aica/api/domain/jobtype"
	"strings"
	"sync"
)

type cachedJobTypeSearchToolResolver struct {
	repo *jobtype.JobTypeRepository

	mu     sync.RWMutex
	loaded bool

	loadMappings func() ([]*jobtype.JobTypePositionSearchToolMapping, error)

	jobtypeToTool map[string]string
	toolToNames   map[string][]string
}

// newCachedJobTypeSearchToolResolver は職種名と検索ツール名の対応をキャッシュするリゾルバを生成する。
// 初期状態では空の対応表だけを持たせ、実データの読み込みは最初の参照時に遅延実行する。
func newCachedJobTypeSearchToolResolver(repo *jobtype.JobTypeRepository) *cachedJobTypeSearchToolResolver {
	return &cachedJobTypeSearchToolResolver{
		repo:          repo,
		jobtypeToTool: map[string]string{},
		toolToNames:   map[string][]string{},
	}
}

// ToolNameByJobtypeName は職種名に対応する検索ツール名を返す。
// 必要なら先にキャッシュを読み込み、正規化した職種名をキーに対応表から値を取得する。
func (r *cachedJobTypeSearchToolResolver) ToolNameByJobtypeName(name string) string {
	r.load()
	return r.jobtypeToTool[strings.TrimSpace(name)]
}

// JobtypeNamesByToolName は検索ツール名に紐づく職種名一覧を返す。
// キャッシュ読み込み後に対応する一覧を取り出し、呼び出し側で破壊されないようコピーして返す。
func (r *cachedJobTypeSearchToolResolver) JobtypeNamesByToolName(toolName string) []string {
	r.load()
	names := r.toolToNames[strings.TrimSpace(toolName)]
	if len(names) == 0 {
		return nil
	}
	return append([]string{}, names...)
}

// load は職種名と検索ツール名の対応表を一度だけ読み込み、キャッシュへ構築する。
// まず read lock でロード済みかを確認し、未ロード時だけ write lock を取り直して DB 由来の対応表を整形・保存する。
func (r *cachedJobTypeSearchToolResolver) load() {
	r.mu.RLock()
	if r.loaded {
		r.mu.RUnlock()
		return
	}
	r.mu.RUnlock()

	r.mu.Lock()
	defer r.mu.Unlock()

	if r.loaded {
		return
	}

	mappings, err := r.fetchMappings()
	if err != nil {
		return
	}

	// 職種名から ToolName を引くための正引きマップ。
	jobtypeToTool := map[string]string{}
	// ToolName から属する職種名一覧を引くための逆引きマップ。
	toolToNames := map[string][]string{}
	for _, mapping := range mappings {
		if mapping == nil {
			continue
		}

		jobTypeName := strings.TrimSpace(mapping.JobTypeName)
		toolName := strings.TrimSpace(mapping.ToolName)
		if jobTypeName == "" || toolName == "" {
			continue
		}

		jobtypeToTool[jobTypeName] = toolName
		toolToNames[toolName] = append(toolToNames[toolName], jobTypeName)
	}

	r.jobtypeToTool = jobtypeToTool
	r.toolToNames = toolToNames
	r.loaded = true
}

// fetchMappings はキャッシュ構築に使う職種名と検索ツール名の対応一覧を取得する。
// テスト差し替え用の loadMappings があればそれを優先し、なければ repository から対象 ToolName 分の対応を取得する。
func (r *cachedJobTypeSearchToolResolver) fetchMappings() ([]*jobtype.JobTypePositionSearchToolMapping, error) {
	if r.loadMappings != nil {
		return r.loadMappings()
	}
	if r.repo == nil {
		return nil, nil
	}
	return r.repo.GetPositionSearchToolMappings([]string{
		pcontracts.ToolNameSearchJobPostingsForITEngineer,
		pcontracts.ToolNameSearchJobPostingsForSalesFinancialSales,
	})
}
