package filter

import (
	"encoding/json"
	"errors"
	"strings"

	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	pinterfaces "aica/api/api/mcptool/usecase/position/interfaces"
	pmodel "aica/api/api/mcptool/usecase/position/model"
	psupport "aica/api/api/mcptool/usecase/position/support"
	address "aica/api/api/mcptool/usecase/shared"
	jobfilter "aica/api/domain/jobfilter"
	merr "aica/api/sdk/error"
	"aica/api/sdk/logger"

	"github.com/samber/lo"
	"gorm.io/datatypes"
)

type JobSearchFilterService struct {
	logger                  logger.LevelLogger
	repository              pinterfaces.JobSearchFilterRepository
	marshal                 func(v any) ([]byte, error)
	locationLookup          genericLocationLookup
	locationRequestResolver locationRequestResolver
}

const commonSelectedFilterKey = pcontracts.SelectedFilterOptionsCommonKey

type genericLocationLookup interface {
	GetCommutingAreasFromResidence(prefectureName string, cityName string) ([]int, error)
}

type locationRequestResolver interface {
	GetLocationRequestsFromCityIDs(cityIDs []int32) []*address.LocationRequest
}

// NewJobSearchFilterService は JobSearchFilterService を生成する。
// 検索フィルタの取得・マージ・保存に必要な repository と JSON シリアライズ手段を束ねて保持する。
func NewJobSearchFilterService(logger logger.LevelLogger, repository pinterfaces.JobSearchFilterRepository) *JobSearchFilterService {
	return &JobSearchFilterService{
		logger:     logger,
		repository: repository,
		marshal:    json.Marshal,
	}
}

// WithGenericLocationPersistence configures optional dependencies needed to persist
// derived commuting areas for generic searches driven only by residence.
func (s *JobSearchFilterService) WithGenericLocationPersistence(
	lookup genericLocationLookup,
	resolver locationRequestResolver,
) *JobSearchFilterService {
	if s == nil {
		return nil
	}
	s.locationLookup = lookup
	s.locationRequestResolver = resolver
	return s
}

// GetBySessionID は sessionID で保存済みの検索フィルタを取得する。
// sessionID が空の場合は問い合わせを行わず nil を返し、それ以外は repository から型付きフィルタを読み出す。
func (s *JobSearchFilterService) GetBySessionID(sessionID string) (*jobfilter.JobSearchFilter, error) {
	if sessionID == "" {
		return nil, nil
	}
	return s.repository.GetTypedJobSearchFilterBySessionID(sessionID)
}

// MergeJobTypes は jobfilter.jobtypes にリクエスト内容をマージして保存する。
// 既存フィルタを読み出して職種グループ単位で選択状態を更新し、保存用に整形して upsert する。
func (s *JobSearchFilterService) MergeJobTypes(sessionID string, selectedGroupKey string, groupedJobtypeNames map[string][]string) error {
	if sessionID == "" {
		return merr.ErrInvalidRequest.WithCause(errors.New("session id is required"))
	}

	current, err := s.repository.GetTypedJobSearchFilterBySessionID(sessionID)
	if err != nil {
		return err
	}
	if current == nil {
		current = &jobfilter.JobSearchFilter{}
	}

	current.Jobtypes = mergeRequestedJobTypeGroups(current.Jobtypes, selectedGroupKey, groupedJobtypeNames)
	// 保存対象を参照共有しないよう、マージ結果を persistence 用の構造へ詰め替える。
	toPersist := cloneForPersistence(current)
	payload, err := s.marshal(toPersist)
	if err != nil {
		return err
	}
	return s.repository.UpsertJobSearchFilter(sessionID, datatypes.JSON(payload))
}

// PersistFromSearchInput は検索入力を既存フィルタにマージし、永続化する。
// 職種特化検索の入力から職種・勤務地・年収・その他フィルタを更新し、保存後に再読込した結果を返す。
func (s *JobSearchFilterService) PersistFromSearchInput(sessionID string, input *pcontracts.JobSpecificSearchInput, commutingAreas []*address.LocationRequest, searchFilters *jobfilter.JobSearchFilter) (*jobfilter.JobSearchFilter, error) {
	if sessionID == "" {
		// セッションIDなしでは保存先を特定できないため何もしない。
		return nil, nil
	}
	if input == nil {
		return nil, merr.ErrInvalidRequest.WithCause(errors.New("search input is required"))
	}

	// 既存フィルタを取得し、差分マージする。
	current, err := s.repository.GetTypedJobSearchFilterBySessionID(sessionID)
	if err != nil {
		return nil, err
	}
	if current == nil {
		// 初回保存時は空のフィルタを起点にする。
		current = &jobfilter.JobSearchFilter{}
	}

	// 職種・勤務地・年収を今回の入力で更新する。
	current.Jobtypes = mergeRequestedJobTypeGroups(current.Jobtypes, jobtypesGroupKeyForInput(input), map[string][]string{jobtypesGroupKeyForInput(input): psupport.RequestedJobTypeNames(input)})
	var remoteOptionState *pcontracts.RemotePositionOptionState
	if input.Custom != nil {
		remoteOptionState = input.Custom.RemotePositionOptionState()
	}
	current.Locations = mergeLocations(current.Locations, input.Locations, commutingAreas, remoteOptionState)
	current.Salary = int(input.Salary)
	positionKeyword := psupport.ExtractPositionKeyword(input)
	current.SelectedOtherFilterOptions = mergeSelectedOtherFilterOptions(
		current.SelectedOtherFilterOptions,
		selectedFilterOptionsKey(input),
		selectedFilterOptionsByKey(searchFilters, selectedFilterOptionsKey(input)),
		positionKeyword,
	)
	current.PositionKeyword = psupport.StringPtrIfNonEmpty(positionKeyword)

	persisted := &jobfilter.JobSearchFilter{
		Jobtypes:                   current.Jobtypes,
		Locations:                  current.Locations,
		Salary:                     current.Salary,
		PositionKeyword:            current.PositionKeyword,
		SelectedOtherFilterOptions: current.SelectedOtherFilterOptions,
	}
	// DB保存フォーマットに変換してupsertする。
	jobSearchFilterJSON, err := s.marshal(cloneForPersistence(persisted))
	if err != nil {
		return nil, err
	}

	err = s.repository.UpsertJobSearchFilter(sessionID, datatypes.JSON(jobSearchFilterJSON))
	if err != nil {
		return nil, err
	}

	return s.reloadPersistedFilter(sessionID, persisted), nil
}

// PersistFromGenericSearchParams は汎用検索入力を job_search_filters に保存する。
// 汎用検索で扱う職種・勤務地・年収・共通キーワードを既存フィルタへ反映し、保存後の状態を返却する。
func (s *JobSearchFilterService) PersistFromGenericSearchParams(sessionID string, params *pmodel.GenericPositionSearchParams) (*jobfilter.JobSearchFilter, error) {
	if sessionID == "" {
		return nil, nil
	}
	if params == nil {
		return nil, merr.ErrInvalidRequest.WithCause(errors.New("search params is required"))
	}

	current, err := s.repository.GetTypedJobSearchFilterBySessionID(sessionID)
	if err != nil {
		return nil, err
	}
	if current == nil {
		current = &jobfilter.JobSearchFilter{}
	}

	requestedLocations := s.expandGenericLocationsForPersistence(params)

	selectedOtherFilterOptions := mergeCommonPositionKeyword(current.SelectedOtherFilterOptions, params.PositionKeyword)
	persisted := &jobfilter.JobSearchFilter{
		Jobtypes:                   mergeRequestedJobTypeGroups(current.Jobtypes, pcontracts.ToolNameSearchJobPostings, map[string][]string{pcontracts.ToolNameSearchJobPostings: params.JobtypeNames}),
		Locations:                  mergeGenericLocations(current.Locations, requestedLocations),
		Salary:                     int(params.Salary),
		PositionKeyword:            psupport.StringPtrIfNonEmpty(params.PositionKeyword),
		SelectedOtherFilterOptions: selectedOtherFilterOptions,
	}

	payload, err := s.marshal(cloneForPersistence(persisted))
	if err != nil {
		return nil, err
	}
	if err := s.repository.UpsertJobSearchFilter(sessionID, datatypes.JSON(payload)); err != nil {
		return nil, err
	}
	return s.reloadPersistedFilter(sessionID, persisted), nil
}

func (s *JobSearchFilterService) expandGenericLocationsForPersistence(params *pmodel.GenericPositionSearchParams) []*address.LocationRequest {
	if params == nil || len(params.Locations) == 0 {
		return nil
	}

	requested := append([]*address.LocationRequest{}, params.Locations...)
	if hasFullRemoteLocation(requested) || hasExplicitCommutingAreas(requested) {
		return requested
	}

	residence := firstResidenceLocation(requested)
	if residence == nil || s.locationLookup == nil || s.locationRequestResolver == nil {
		return requested
	}

	cityIDs, err := s.locationLookup.GetCommutingAreasFromResidence(residence.PrefectureName, residence.CityName)
	if err != nil {
		if s.logger != nil {
			s.logger.Warn(
				"failed to derive commuting areas for generic search filter persistence",
				"prefecture_name", residence.PrefectureName,
				"city_name", residence.CityName,
				"error", err,
			)
		}
		return requested
	}

	commutingAreas := s.locationRequestResolver.GetLocationRequestsFromCityIDs(toInt32IDs(cityIDs))
	if len(commutingAreas) == 0 {
		return requested
	}

	return append(requested, commutingAreas...)
}

func hasFullRemoteLocation(locations []*address.LocationRequest) bool {
	for _, location := range locations {
		if location != nil && location.LocationType == address.LOCATION_TYPE_FULL_REMOTE_WORK {
			return true
		}
	}
	return false
}

func hasExplicitCommutingAreas(locations []*address.LocationRequest) bool {
	for _, location := range locations {
		if location != nil && location.LocationType == address.LOCATION_TYPE_COMMUTING_AREAS {
			return true
		}
	}
	return false
}

func firstResidenceLocation(locations []*address.LocationRequest) *address.LocationRequest {
	for _, location := range locations {
		if location != nil && location.LocationType == address.LOCATION_TYPE_RESIDENCE {
			return location
		}
	}
	return nil
}

func toInt32IDs(values []int) []int32 {
	return lo.Map(values, func(v int, _ int) int32 { return int32(v) })
}

// reloadPersistedFilter は upsert 後の保存値を再取得し、取得できない場合は fallback を返す。
// DB 側の整形結果を優先して返したい場面で使い、再読込失敗時は warning を記録して処理を継続する。
func (s *JobSearchFilterService) reloadPersistedFilter(sessionID string, fallback *jobfilter.JobSearchFilter) *jobfilter.JobSearchFilter {
	if sessionID == "" {
		return fallback
	}

	reloaded, err := s.repository.GetTypedJobSearchFilterBySessionID(sessionID)
	if err != nil {
		s.logger.Warn("failed to reload job_search_filter after upsert", "session_id", sessionID, "error", err)
		return fallback
	}
	if reloaded == nil {
		return fallback
	}
	return reloaded
}

// mergeLocations は居住地・通勤圏・希望勤務地を既存フィルタへ反映して返す。
func mergeLocations(
	current *jobfilter.JobSearchFilterLocations,
	requested []*address.LocationRequest,
	commutingAreas []*address.LocationRequest,
	remoteOptionState *pcontracts.RemotePositionOptionState,
) *jobfilter.JobSearchFilterLocations {
	// 既存値をコピーしてから更新する（参照共有による副作用を防ぐ）。
	merged := &jobfilter.JobSearchFilterLocations{
		WorkLocations:      append([]*jobfilter.JobSearchFilterLocationSelectableItem{}, currentWorkLocations(current)...),
		RemoteWorkPossible: currentRemoteWorkPossible(current),
	}
	if current != nil && current.Residence != nil {
		// Residence 配下は「住所 + その住所に紐づく通勤圏」の単位で保持する。
		// 既存値があれば、今回のリクエストで上書き・選択更新する前提として丸ごとコピーしておく。
		var addressCopy *jobfilter.JobSearchFilterAddress
		if current.Residence.Address != nil {
			addressCopy = &jobfilter.JobSearchFilterAddress{
				PrefectureName: current.Residence.Address.PrefectureName,
				CityName:       current.Residence.Address.CityName,
			}
		}
		merged.Residence = &jobfilter.JobSearchFilterResidence{
			Address:        addressCopy,
			CommutingAreas: append([]*jobfilter.JobSearchFilterLocationSelectableItem{}, current.Residence.CommutingAreas...),
		}
	}

	requestedResidence, requestedCommutingAreas, requestedWorkLocations := splitRequestedLocations(requested)
	requestedWorkLocationsByName := locationRequestsByName(requested, address.LOCATION_TYPE_WORK_LOCATION)
	if requestedResidence != nil {
		// 居住地が指定された場合は住所と通勤圏を再構築する。
		if merged.Residence == nil {
			merged.Residence = &jobfilter.JobSearchFilterResidence{}
		}
		merged.Residence.Address = &jobfilter.JobSearchFilterAddress{
			PrefectureName: requestedResidence.PrefectureName,
			CityName:       requestedResidence.CityName,
		}
		merged.Residence.CommutingAreas = toSelectedSelectableItemsFromLocations(commutingAreas)
	} else if merged.Residence != nil && len(requestedCommutingAreas) > 0 {
		// 通勤圏は居住地に従属する情報として扱う。
		// そのため、住所が無い invalid な「通勤圏だけ」の入力は新規保存せず、
		// 既存の Residence がある場合だけ候補の選択状態を更新する。
		setSelected(merged.Residence.CommutingAreas, requestedCommutingAreas)
	}

	// 希望勤務地は既存選択状態を更新し、未登録の選択項目は追加する。
	setSelected(merged.WorkLocations, requestedWorkLocations)
	addMissingSelectedItems(&merged.WorkLocations, requestedWorkLocations, requestedWorkLocationsByName)

	// リモート選択状態更新
	applyRemoteWorkPossible(merged, remoteOptionState)

	// 無効入力の切り捨てなどで有効な場所条件が何も残らなければ nil に畳み込む。
	return nilIfLocationsEmpty(merged)
}

// applyRemoteWorkPossible は職種ごとのリモート可否オプション有無に応じて RemoteWorkPossible を更新する。
func applyRemoteWorkPossible(merged *jobfilter.JobSearchFilterLocations, remoteOptionState *pcontracts.RemotePositionOptionState) {
	if merged == nil {
		return
	}
	if remoteOptionState == nil || !remoteOptionState.HasOption {
		// リモート選択肢を持たない職種では値を保持しない。
		merged.RemoteWorkPossible = nil
		return
	}
	merged.RemoteWorkPossible = &remoteOptionState.CurrentChoice
}

// currentWorkLocations は既存の希望勤務地一覧を返す。current が nil の場合は nil。
func currentWorkLocations(current *jobfilter.JobSearchFilterLocations) []*jobfilter.JobSearchFilterLocationSelectableItem {
	if current == nil {
		return nil
	}
	return current.WorkLocations
}

// currentRemoteWorkPossible は既存フィルタのリモート勤務可否状態を取り出す。
// current が nil の場合は何も保持されていないものとして nil を返す。
func currentRemoteWorkPossible(current *jobfilter.JobSearchFilterLocations) *bool {
	if current == nil {
		return nil
	}
	return current.RemoteWorkPossible
}

// splitRequestedLocations はリクエスト場所を居住地・通勤圏・希望勤務地に分解する。
func splitRequestedLocations(requested []*address.LocationRequest) (*address.LocationRequest, []string, []string) {
	var residence *address.LocationRequest
	commutingAreas := make([]string, 0)
	workLocations := make([]string, 0)

	for _, loc := range requested {
		name := locationRequestName(loc)
		if name == "" {
			continue
		}

		switch loc.LocationType {
		case address.LOCATION_TYPE_RESIDENCE:
			if residence == nil {
				residence = &address.LocationRequest{
					LocationType:   address.LOCATION_TYPE_RESIDENCE,
					PrefectureName: loc.PrefectureName,
					CityName:       loc.CityName,
				}
			}
		case address.LOCATION_TYPE_COMMUTING_AREAS:
			commutingAreas = append(commutingAreas, name)
		case address.LOCATION_TYPE_WORK_LOCATION:
			workLocations = append(workLocations, name)
		}
	}

	return residence, lo.Uniq(commutingAreas), lo.Uniq(workLocations)
}

// toSelectedSelectableItemsFromLocations は LocationRequest 配列を「選択済み項目」配列へ変換する。
func toSelectedSelectableItemsFromLocations(locations []*address.LocationRequest) []*jobfilter.JobSearchFilterLocationSelectableItem {
	items := make([]*jobfilter.JobSearchFilterLocationSelectableItem, 0, len(locations))
	for _, loc := range locations {
		if loc == nil {
			continue
		}
		name := normalizeLocationName(loc.PrefectureName, loc.CityName)
		if name == "" {
			continue
		}
		items = append(items, &jobfilter.JobSearchFilterLocationSelectableItem{
			Label:          name,
			PrefectureName: loc.PrefectureName,
			CityName:       loc.CityName,
			Selected:       true,
		})
	}
	return items
}

// setSelected は selectedNames に含まれる項目のみ Selected=true に更新する。
func setSelected(items []*jobfilter.JobSearchFilterLocationSelectableItem, selectedNames []string) {
	// O(1) 判定のため選択対象を集合化する。
	selectedSet := lo.SliceToMap(selectedNames, func(name string) (string, struct{}) {
		return name, struct{}{}
	})

	for i := range items {
		if items[i] == nil {
			// nil 要素が混在しても落ちないように防御する。
			continue
		}
		itemName := locationSelectableItemName(items[i])
		_, ok := selectedSet[itemName]
		items[i].Selected = ok
	}
}

// addMissingSelectedItems は選択対象にあるが未登録の項目を追加する。
func addMissingSelectedItems(items *[]*jobfilter.JobSearchFilterLocationSelectableItem, selectedNames []string, selectedByName map[string]*address.LocationRequest) {
	// 既存項目名を先に集めて重複追加を防ぐ。
	existingSet := make(map[string]struct{}, len(*items))
	for _, item := range *items {
		existingName := locationSelectableItemName(item)
		if existingName == "" {
			continue
		}
		existingSet[existingName] = struct{}{}
	}

	for _, name := range selectedNames {
		if _, ok := existingSet[name]; ok {
			continue
		}
		var prefectureName string
		var cityName string
		if loc, ok := selectedByName[name]; ok && loc != nil {
			prefectureName = loc.PrefectureName
			cityName = loc.CityName
		}
		// 既存にない選択項目は追加して選択状態にする。
		*items = append(*items, &jobfilter.JobSearchFilterLocationSelectableItem{
			Label:          name,
			PrefectureName: prefectureName,
			CityName:       cityName,
			Selected:       true,
		})
		existingSet[name] = struct{}{}
	}
}

// locationRequestsByName は LocationRequest 一覧を正規化名キーで引けるマップへ変換する。
// 指定した LocationType だけを対象にし、後続の追加処理で元の都道府県名・市区町村名を引き直せるようにする。
func locationRequestsByName(requested []*address.LocationRequest, locationType address.LocationType) map[string]*address.LocationRequest {
	results := make(map[string]*address.LocationRequest)
	for _, loc := range requested {
		if loc == nil || loc.LocationType != locationType {
			continue
		}
		name := locationRequestName(loc)
		if name == "" {
			continue
		}
		results[name] = loc
	}
	return results
}

// locationRequestName は 1 件の LocationRequest から比較用の正規化名を作る。
// nil は空文字を返し、それ以外は都道府県名と市区町村名を連結した値へ正規化する。
func locationRequestName(loc *address.LocationRequest) string {
	if loc == nil {
		return ""
	}
	return normalizeLocationName(loc.PrefectureName, loc.CityName)
}

// normalizeLocationName は都道府県名と市区町村名を連結して正規化する。
func normalizeLocationName(prefectureName, cityName string) string {
	return strings.TrimSpace(prefectureName + cityName)
}

// mergeRequestedJobTypeGroups は既存の職種グループ状態へ、今回リクエストされた選択内容をマージする。
// 選択対象グループは requested に合わせて選択状態を更新し、非選択グループは既存値保持または未登録職種の補完のみを行う。
func mergeRequestedJobTypeGroups(current map[string][]*jobfilter.JobtypeSelectableItem, selectedGroupKey string, groupedJobtypeNames map[string][]string) map[string][]*jobfilter.JobtypeSelectableItem {
	groups := cloneJobtypeGroupsWithoutDescriptions(current)
	if groups == nil {
		groups = map[string][]*jobfilter.JobtypeSelectableItem{}
	}
	// 今回ユーザーが操作した代表グループで、選択状態更新の対象判定に使う。
	selectedKey := strings.TrimSpace(selectedGroupKey)
	// もともと存在していたグループかどうかを保持し、新規グループ追加時の扱いを分ける。
	_, selectedGroupExisted := groups[selectedKey]

	// リクエスト入力を空白除去・重複排除したグループ別一覧へ正規化する。
	normalizedGroups := map[string][]string{}
	for key, names := range groupedJobtypeNames {
		normalizedKey := strings.TrimSpace(key)
		if normalizedKey == "" {
			continue
		}
		normalizedGroups[normalizedKey] = uniqueJobtypeNames(names)
	}

	if len(groups) == 0 && selectedKey == "" && len(normalizedGroups) == 0 {
		return nil
	}

	for key, items := range groups {
		requested := normalizedGroups[key]
		if key != selectedKey {
			requested = nil
		}
		groups[key] = mergeJobtypeGroup(items, requested)
	}

	for key, names := range normalizedGroups {
		if _, ok := groups[key]; !ok {
			groups[key] = nil
		}
		if key == selectedKey {
			if !selectedGroupExisted {
				groups[key] = mergeJobtypeGroup(groups[key], names)
			}
			continue
		}
		groups[key] = appendMissingJobtypes(groups[key], names, false)
	}

	return groups
}

// appendMissingJobtypes は指定グループに未登録の職種名だけを追加する。
// 既存項目は保持しつつ、足りない職種を Selected の既定値付きで末尾へ補完する。
func appendMissingJobtypes(current []*jobfilter.JobtypeSelectableItem, requested []string, selected bool) []*jobfilter.JobtypeSelectableItem {
	items := append([]*jobfilter.JobtypeSelectableItem{}, current...)
	for _, name := range requested {
		if jobtypeExistsInGroup(items, name) {
			continue
		}
		items = append(items, &jobfilter.JobtypeSelectableItem{
			JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{
				JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{
					Label: name,
					Value: name,
				},
				Selected: selected,
			},
		})
	}
	return items
}

// jobtypeExistsInGroup は指定職種名がグループ内にすでに存在するかを判定する。
// Value を比較対象にし、空白差異を除いたうえで重複追加防止に利用する。
func jobtypeExistsInGroup(items []*jobfilter.JobtypeSelectableItem, name string) bool {
	for _, item := range items {
		if item == nil {
			continue
		}
		if strings.TrimSpace(item.Value) == name {
			return true
		}
	}
	return false
}

// mergeJobtypeGroup は 1 つの職種グループ内で選択状態を requested に合わせて再構築する。
// 既存項目はラベルや説明を維持しつつ Selected を更新し、未登録の requested 項目は新規選択済みとして追加する。
func mergeJobtypeGroup(current []*jobfilter.JobtypeSelectableItem, requested []string) []*jobfilter.JobtypeSelectableItem {
	// 今回選択されている職種名を O(1) で判定するための集合。
	selected := map[string]struct{}{}
	for _, name := range requested {
		selected[name] = struct{}{}
	}

	// 既存項目と追加項目の双方で重複を防ぐための既出判定用セット。
	seen := make(map[string]struct{}, len(current)+len(selected))
	items := make([]*jobfilter.JobtypeSelectableItem, 0, len(current)+len(selected))
	for _, item := range current {
		if item == nil {
			continue
		}
		value := strings.TrimSpace(item.Value)
		if value == "" {
			continue
		}
		if _, ok := seen[value]; ok {
			continue
		}
		seen[value] = struct{}{}
		_, isSelected := selected[value]
		items = append(items, &jobfilter.JobtypeSelectableItem{
			JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{
				JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{
					Label: item.Label,
					Value: value,
				},
				Selected: isSelected,
			},
			Description: item.Description,
		})
	}

	for _, name := range requested {
		if _, ok := seen[name]; ok {
			continue
		}
		seen[name] = struct{}{}
		items = append(items, &jobfilter.JobtypeSelectableItem{
			JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{
				JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{
					Label: name,
					Value: name,
				},
				Selected: true,
			},
		})
	}

	return items
}

// uniqueJobtypeNames は職種名一覧から空文字と重複を除いた正規化済み一覧を返す。
// 前後空白を除去した値だけを保持し、最初の出現順を維持する。
func uniqueJobtypeNames(names []string) []string {
	seen := map[string]struct{}{}
	out := make([]string, 0, len(names))
	for _, name := range names {
		n := strings.TrimSpace(name)
		if n == "" {
			continue
		}
		if _, ok := seen[n]; ok {
			continue
		}
		seen[n] = struct{}{}
		out = append(out, n)
	}
	return out
}

// cloneForPersistence は保存用の JobSearchFilter を必要最小限の情報だけで複製する。
// 説明文など DB 保存に不要な情報を落としつつ、可変マップやスライスの参照共有を避ける。
func cloneForPersistence(src *jobfilter.JobSearchFilter) *jobfilter.JobSearchFilter {
	if src == nil {
		return nil
	}
	return &jobfilter.JobSearchFilter{
		Jobtypes:                   cloneJobtypeGroupsWithoutDescriptions(src.Jobtypes),
		Locations:                  src.Locations,
		Salary:                     src.Salary,
		PositionKeyword:            src.PositionKeyword,
		SelectedOtherFilterOptions: cloneSelectedOtherFilterOptions(src.SelectedOtherFilterOptions),
	}
}

// cloneJobtypeGroupsWithoutDescriptions は職種グループを説明文なしでディープコピーする。
// 保存対象に必要な label/value/selected だけを残し、元データを書き換えないよう新しい構造へ複製する。
func cloneJobtypeGroupsWithoutDescriptions(src map[string][]*jobfilter.JobtypeSelectableItem) map[string][]*jobfilter.JobtypeSelectableItem {
	if len(src) == 0 {
		return nil
	}
	cloned := make(map[string][]*jobfilter.JobtypeSelectableItem, len(src))
	for key, items := range src {
		group := make([]*jobfilter.JobtypeSelectableItem, 0, len(items))
		for _, item := range items {
			if item == nil {
				group = append(group, nil)
				continue
			}
			group = append(group, &jobfilter.JobtypeSelectableItem{
				JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{
					JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{
						Label: item.Label,
						Value: item.Value,
					},
					Selected: item.Selected,
				},
			})
		}
		cloned[key] = group
	}
	return cloned
}

// cloneSelectedOtherFilterOptions は SelectedOtherFilterOptions をマップ階層ごと複製する。
// ツールキーとフィルタ値配列を丸ごとコピーし、呼び出し元との参照共有を防ぐ。
func cloneSelectedOtherFilterOptions(src map[string]map[string][]string) map[string]map[string][]string {
	if len(src) == 0 {
		return nil
	}
	cloned := make(map[string]map[string][]string, len(src))
	for key, values := range src {
		inner := make(map[string][]string, len(values))
		for filterName, options := range values {
			inner[filterName] = append([]string(nil), options...)
		}
		cloned[key] = inner
	}
	return cloned
}

// mergeCommonPositionKeyword は共通フィルタ領域の PositionKeyword だけを更新するヘルパーである。
// 実処理は mergeSelectedOtherFilterOptions に委譲し、共通キーの扱いだけを簡潔に呼び出せるようにしている。
func mergeCommonPositionKeyword(current map[string]map[string][]string, positionKeyword string) map[string]map[string][]string {
	return mergeSelectedOtherFilterOptions(current, "", nil, positionKeyword)
}

// mergeSelectedOtherFilterOptions は職種別フィルタ選択と共通 PositionKeyword をまとめて更新する。
// toolKey 側は空配列なら削除、値ありなら置換し、共通キーワードは空なら削除・値ありなら共通キーへ保存する。
func mergeSelectedOtherFilterOptions(current map[string]map[string][]string, toolKey string, toolValues map[string][]string, positionKeyword string) map[string]map[string][]string {
	merged := cloneSelectedOtherFilterOptions(current)
	if merged == nil {
		merged = map[string]map[string][]string{}
	}
	if strings.TrimSpace(toolKey) != "" {
		if len(toolValues) == 0 {
			delete(merged, toolKey)
		} else {
			inner := make(map[string][]string, len(toolValues))
			for key, values := range toolValues {
				inner[key] = append([]string(nil), values...)
			}
			merged[toolKey] = inner
		}
	}
	if strings.TrimSpace(positionKeyword) == "" {
		delete(merged, commonSelectedFilterKey)
		return merged
	}
	common := map[string][]string{"PositionKeyword": {strings.TrimSpace(positionKeyword)}}
	merged[commonSelectedFilterKey] = common
	return merged
}

// selectedFilterOptionsByKey は保存済みフィルタから指定キーに対応するその他フィルタ選択だけを取り出す。
// フィルタ自体やキーが無効な場合は nil を返し、呼び出し側でそのままマージ可否を判定できるようにする。
func selectedFilterOptionsByKey(filter *jobfilter.JobSearchFilter, key string) map[string][]string {
	if filter == nil || key == "" || filter.SelectedOtherFilterOptions == nil {
		return nil
	}
	return filter.SelectedOtherFilterOptions[key]
}

// buildGenericLocations は汎用検索の LocationRequest 一覧を保存用 Locations 構造へ変換する。
// 居住地、通勤圏・勤務地、フルリモートを分類しつつ、重複を除いた Selected=true の selectable item 群を組み立てる。
func buildGenericLocations(locations []*address.LocationRequest) *jobfilter.JobSearchFilterLocations {
	if len(locations) == 0 {
		return nil
	}

	// 勤務地系の selectable item を蓄積する一覧。
	workLocations := make([]*jobfilter.JobSearchFilterLocationSelectableItem, 0, len(locations))
	// 勤務地系項目の重複追加を防ぐための既出判定セット。
	workSeen := map[string]struct{}{}
	var residence *jobfilter.JobSearchFilterResidence
	// 明示的に指定された通勤圏の重複追加を防ぐための既出判定セット。
	explicitCommutingSeen := map[string]struct{}{}
	var remoteWorkPossible *bool
	for _, loc := range locations {
		if loc == nil {
			continue
		}

		switch loc.LocationType {
		case address.LOCATION_TYPE_RESIDENCE:
			name := normalizeLocationName(loc.PrefectureName, loc.CityName)
			if name == "" {
				continue
			}
			if residence == nil {
				residence = &jobfilter.JobSearchFilterResidence{
					Address: &jobfilter.JobSearchFilterAddress{
						PrefectureName: loc.PrefectureName,
						CityName:       loc.CityName,
					},
				}
			}
		case address.LOCATION_TYPE_COMMUTING_AREAS:
			name := normalizeLocationName(loc.PrefectureName, loc.CityName)
			if name == "" {
				continue
			}
			if residence == nil {
				residence = &jobfilter.JobSearchFilterResidence{}
			}
			if _, exists := explicitCommutingSeen[name]; exists {
				continue
			}
			explicitCommutingSeen[name] = struct{}{}
			residence.CommutingAreas = append(residence.CommutingAreas, &jobfilter.JobSearchFilterLocationSelectableItem{
				Label:          name,
				PrefectureName: loc.PrefectureName,
				CityName:       loc.CityName,
				Selected:       true,
			})
		case address.LOCATION_TYPE_WORK_LOCATION:
			name := normalizeLocationName(loc.PrefectureName, loc.CityName)
			if name == "" {
				continue
			}
			if _, exists := workSeen[name]; exists {
				continue
			}
			workSeen[name] = struct{}{}
			workLocations = append(workLocations, &jobfilter.JobSearchFilterLocationSelectableItem{
				Label:          name,
				PrefectureName: loc.PrefectureName,
				CityName:       loc.CityName,
				Selected:       true,
			})
		case address.LOCATION_TYPE_FULL_REMOTE_WORK:
			v := true
			remoteWorkPossible = &v
		}
	}

	if residence == nil && len(workLocations) == 0 && remoteWorkPossible == nil {
		return nil
	}
	return &jobfilter.JobSearchFilterLocations{
		Residence:          residence,
		WorkLocations:      workLocations,
		RemoteWorkPossible: remoteWorkPossible,
	}
}

// mergeGenericLocations は汎用検索の LocationRequest 群を既存保存値へマージする。
// リクエストで指定された項目は Selected=true にし、DB にだけある既存項目は保持したまま Selected=false に落とす。
// ただしリクエストから有効な location が 1 件も作れなかった場合は、既存保存値をそのまま使う。(勤務地は必須条件なので、基本この場合がない)
func mergeGenericLocations(current *jobfilter.JobSearchFilterLocations, requested []*address.LocationRequest) *jobfilter.JobSearchFilterLocations {
	desired := buildGenericLocations(requested)
	if current == nil {
		return desired
	}
	if desired == nil {
		// buildGenericLocations で有効な location を 1 件も作れなかった場合は、
		// 既存保存値を維持するため current のクローンをそのまま返す。
		return cloneLocationState(current)
	}

	merged := cloneLocationState(current)

	if desired.Residence != nil {
		if merged.Residence == nil {
			merged.Residence = &jobfilter.JobSearchFilterResidence{}
		}
		merged.Residence.Address = cloneLocationAddress(desired.Residence.Address)
		setSelected(merged.Residence.CommutingAreas, locationItemNames(desired.Residence.CommutingAreas))
		addMissingLocationItems(&merged.Residence.CommutingAreas, desired.Residence.CommutingAreas)
	} else if merged.Residence != nil {
		merged.Residence.Address = nil
		setSelected(merged.Residence.CommutingAreas, nil)
	}

	setSelected(merged.WorkLocations, locationItemNames(desired.WorkLocations))
	addMissingLocationItems(&merged.WorkLocations, desired.WorkLocations)

	merged.RemoteWorkPossible = desired.RemoteWorkPossible

	return nilIfLocationsEmpty(merged)
}

// cloneLocationState は Locations 全体をディープコピーして返す。
// マージ時に元の current を直接書き換えないよう、Residence/WorkLocations まで新しいオブジェクトに複製する。
func cloneLocationState(src *jobfilter.JobSearchFilterLocations) *jobfilter.JobSearchFilterLocations {
	if src == nil {
		return nil
	}

	cloned := &jobfilter.JobSearchFilterLocations{
		WorkLocations:      cloneLocationItems(src.WorkLocations),
		RemoteWorkPossible: src.RemoteWorkPossible,
	}
	if src.Residence != nil {
		cloned.Residence = &jobfilter.JobSearchFilterResidence{
			Address:        cloneLocationAddress(src.Residence.Address),
			CommutingAreas: cloneLocationItems(src.Residence.CommutingAreas),
		}
	}
	return cloned
}

// cloneLocationAddress は Residence.Address をそのまま複製する。
// nil は nil のまま返し、呼び出し側で nil 判定ロジックを統一できるようにしている。
func cloneLocationAddress(src *jobfilter.JobSearchFilterAddress) *jobfilter.JobSearchFilterAddress {
	if src == nil {
		return nil
	}
	return &jobfilter.JobSearchFilterAddress{
		PrefectureName: src.PrefectureName,
		CityName:       src.CityName,
	}
}

// cloneLocationItems は selectable item 配列を要素単位で複製する。
// Label/PrefectureName/CityName/Selected をそのままコピーし、既存配列との参照共有を避ける。
func cloneLocationItems(src []*jobfilter.JobSearchFilterLocationSelectableItem) []*jobfilter.JobSearchFilterLocationSelectableItem {
	if len(src) == 0 {
		return nil
	}
	cloned := make([]*jobfilter.JobSearchFilterLocationSelectableItem, 0, len(src))
	for _, item := range src {
		if item == nil {
			continue
		}
		cloned = append(cloned, &jobfilter.JobSearchFilterLocationSelectableItem{
			Label:          item.Label,
			PrefectureName: item.PrefectureName,
			CityName:       item.CityName,
			Selected:       item.Selected,
		})
	}
	return cloned
}

// locationSelectableItemName は selectable item から比較用の正規化名を返す。
// PrefectureName+CityName を優先し、持っていない場合だけ Label にフォールバックする。
func locationSelectableItemName(item *jobfilter.JobSearchFilterLocationSelectableItem) string {
	if item == nil {
		return ""
	}
	name := normalizeLocationName(item.PrefectureName, item.CityName)
	if name != "" {
		return name
	}
	return strings.TrimSpace(item.Label)
}

// locationItemNames は selectable item 配列から比較用の正規化名一覧を取り出す。
// 基本は PrefectureName+CityName を使い、持っていない項目だけ Label にフォールバックして重複は除去する。
func locationItemNames(items []*jobfilter.JobSearchFilterLocationSelectableItem) []string {
	names := make([]string, 0, len(items))
	for _, item := range items {
		name := locationSelectableItemName(item)
		if name == "" {
			continue
		}
		names = append(names, name)
	}
	return lo.Uniq(names)
}

// addMissingLocationItems は desired にあるが既存 items に存在しない項目だけを追加する。
// 追加時は address.LocationRequest 形式へ詰め替えて addMissingSelectedItems に渡し、新規項目を Selected=true で挿入する。
func addMissingLocationItems(items *[]*jobfilter.JobSearchFilterLocationSelectableItem, desired []*jobfilter.JobSearchFilterLocationSelectableItem) {
	desiredByName := make(map[string]*address.LocationRequest, len(desired))
	desiredNames := make([]string, 0, len(desired))
	for _, item := range desired {
		name := locationSelectableItemName(item)
		if name == "" {
			continue
		}
		desiredNames = append(desiredNames, name)
		desiredByName[name] = &address.LocationRequest{
			PrefectureName: item.PrefectureName,
			CityName:       item.CityName,
		}
	}
	addMissingSelectedItems(items, lo.Uniq(desiredNames), desiredByName)
}

// nilIfLocationsEmpty は Locations が実質的に空かどうかを判定して nil に畳み込む。
// Residence.Address も Residence.CommutingAreas も WorkLocations も RemoteWorkPossible も無い場合だけ nil を返す。
func nilIfLocationsEmpty(locations *jobfilter.JobSearchFilterLocations) *jobfilter.JobSearchFilterLocations {
	if locations == nil {
		return nil
	}
	if locations.Residence != nil {
		if locations.Residence.Address != nil {
			return locations
		}
		if len(locations.Residence.CommutingAreas) > 0 {
			return locations
		}
	}
	if len(locations.WorkLocations) > 0 || locations.RemoteWorkPossible != nil {
		return locations
	}
	return nil
}

// selectedFilterOptionsKey は検索入力に対してその他フィルタ保存先のキーを決定する。
// 明示指定の SelectedFilterOptionsKey を優先し、未指定なら大分類 ID から標準 ToolName を導出する。
func selectedFilterOptionsKey(input *pcontracts.JobSpecificSearchInput) string {
	if input == nil {
		return ""
	}
	if strings.TrimSpace(input.SelectedFilterOptionsKey) != "" {
		return strings.TrimSpace(input.SelectedFilterOptionsKey)
	}
	return pcontracts.ToolNameByJobTypeLargeID(input.JobTypeLargeID)
}

// jobtypesGroupKeyForInput は職種選択を保存するグループキーを検索入力から決定する。
// selectedFilterOptionsKey の結果を優先し、何も導けない場合は汎用検索グループを既定値として返す。
func jobtypesGroupKeyForInput(input *pcontracts.JobSpecificSearchInput) string {
	if key := selectedFilterOptionsKey(input); key != "" {
		return key
	}
	return pcontracts.ToolNameSearchJobPostings
}
