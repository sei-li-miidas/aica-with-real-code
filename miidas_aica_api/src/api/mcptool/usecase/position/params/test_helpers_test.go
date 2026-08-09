package params

import (
	"reflect"
	"unsafe"

	"aica/api/api/mcptool/service"
	tmock "aica/api/api/mcptool/testutil/mock"
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	"aica/api/api/mcptool/usecase/shared"
	"aica/api/domain/public/master"
)

type stubResolver struct {
	resolveSkills         func([]string) (master.Skills, error)
	resolveSalesStyleDive func(*string) (int32, error)
}

func (s *stubResolver) ExistsPrefectureCity(_ string, _ string) bool {
	return true
}

func (s *stubResolver) ResolveJobTypeSmallIDs(_ []string) ([]int32, error) {
	return nil, nil
}
func (s *stubResolver) ResolveLocations(_ []*shared.LocationRequest, _ bool) ([]int32, *shared.LocationRequest, []*shared.LocationRequest, []*shared.LocationRequest, error) {
	return nil, nil, nil, nil, nil
}
func (s *stubResolver) ResolveLocationByName(_ string) (*shared.LocationRequest, error) {
	return nil, nil
}
func (s *stubResolver) ResolveSkills(skillNames []string) (master.Skills, error) {
	return s.resolveSkills(skillNames)
}
func (s *stubResolver) ResolveDayOffs(_ *[]string) ([]int32, error) {
	return nil, nil
}
func (s *stubResolver) ResolveAverageOvertime(_ *string) (int32, error) {
	return 0, nil
}
func (s *stubResolver) ResolveSalesStyleDive(v *string) (int32, error) {
	return s.resolveSalesStyleDive(v)
}

var _ pcontracts.JobSpecificSearchResolver = (*stubResolver)(nil)

func newCacheServiceForJobSpecific(cache *master.Cache) *service.MiidasCacheService {
	cp := &master.CacheProvider{}
	field := reflect.ValueOf(cp).Elem().FieldByName("cache")
	reflect.NewAt(field.Type(), unsafe.Pointer(field.UnsafeAddr())).Elem().Set(reflect.ValueOf(cache))
	l := &tmock.MockLogger{}
	return service.NewMiidasCacheService(l, cp, service.NewProviderRepositoryRegistry(l))
}
