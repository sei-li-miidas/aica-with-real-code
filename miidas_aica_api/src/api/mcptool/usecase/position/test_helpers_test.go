package position

import (
	"reflect"
	"unsafe"

	"aica/api/api/mcptool/service"
	tmock "aica/api/api/mcptool/testutil/mock"
	"aica/api/domain/public/master"
	mcompany "aica/api/domain/user/apply/company"
	mposition "aica/api/domain/user/apply/position"
)

type detailPositionRepoStub struct {
	get func(id mposition.ID) (*mposition.Position, error)
}

func (s *detailPositionRepoStub) Get(id mposition.ID) (*mposition.Position, error) {
	return s.get(id)
}

type detailCompanyRepoStub struct {
	get func(id mcompany.ID) (*mcompany.Company, error)
}

func (s *detailCompanyRepoStub) Get(id mcompany.ID) (*mcompany.Company, error) {
	return s.get(id)
}

func setMasterCacheProviderCache(cp *master.CacheProvider, cache *master.Cache) {
	field := reflect.ValueOf(cp).Elem().FieldByName("cache")
	reflect.NewAt(field.Type(), unsafe.Pointer(field.UnsafeAddr())).Elem().Set(reflect.ValueOf(cache))
}

func newCacheServiceWithCache(cache *master.Cache) *service.MiidasCacheService {
	cp := &master.CacheProvider{}
	setMasterCacheProviderCache(cp, cache)
	l := &tmock.MockLogger{}
	return service.NewMiidasCacheService(l, cp, service.NewProviderRepositoryRegistry(l))
}

type testCommutingAreaSearcher struct {
	resultsByOriginID map[int][]*master.PrefectureCity
	err               error
}

func newLocationLookupServiceWithCache(cache *master.Cache, resultsByOriginID map[int][]*master.PrefectureCity) *service.LocationLookupService {
	cp := &master.CacheProvider{}
	setMasterCacheProviderCache(cp, cache)
	return service.NewLocationLookupService(
		&tmock.MockLogger{},
		cp,
		&testCommutingAreaSearcher{
			resultsByOriginID: resultsByOriginID,
		},
	)
}

func (s *testCommutingAreaSearcher) SearchCommutingAreas(originCityID int) ([]*master.PrefectureCity, error) {
	if s.err != nil {
		return nil, s.err
	}
	return s.resultsByOriginID[originCityID], nil
}

func loPtr[T any](v T) *T {
	return &v
}
