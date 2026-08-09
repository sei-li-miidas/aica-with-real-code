package validation

import (
	"strings"
	"testing"

	address "aica/api/api/mcptool/usecase/shared"
)

func stubExists(prefectureName, cityName string) bool {
	prefectureName, cityName = NormalizePrefectureCity(prefectureName, cityName)
	return prefectureName == "東京都" && cityName == "23区"
}

func TestValidateLocationRequests_Basic(t *testing.T) {
	err := ValidateLocationRequests(
		[]*address.LocationRequest{
			{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "東京都", CityName: "新宿区"},
		},
		stubExists,
		LocationValidationOptions{},
	)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestValidateLocationRequests_Branches(t *testing.T) {
	if err := ValidateLocationRequests(nil, stubExists, LocationValidationOptions{
		AllowEmptyIfRemotePossible: true,
		RemoteWork:                 true,
	}); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if err := ValidateLocationRequests([]*address.LocationRequest{
		{LocationType: address.LOCATION_TYPE_FULL_REMOTE_WORK},
	}, stubExists, LocationValidationOptions{}); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if err := ValidateLocationRequests([]*address.LocationRequest{
		{LocationType: address.LocationType("invalid")},
	}, stubExists, LocationValidationOptions{}); err == nil {
		t.Fatalf("expected invalid type error")
	}
	if err := ValidateLocationRequests([]*address.LocationRequest{
		nil,
	}, stubExists, LocationValidationOptions{}); err == nil {
		t.Fatalf("expected nil location error")
	}
	if err := ValidateLocationRequests([]*address.LocationRequest{
		{LocationType: address.LOCATION_TYPE_RESIDENCE},
	}, stubExists, LocationValidationOptions{}); err == nil {
		t.Fatalf("expected missing residence fields")
	}
	if err := ValidateLocationRequests([]*address.LocationRequest{
		{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "大阪府", CityName: "大阪市"},
	}, stubExists, LocationValidationOptions{}); err == nil {
		t.Fatalf("expected residence not found")
	}

	if err := ValidateLocationRequests([]*address.LocationRequest{
		{LocationType: address.LOCATION_TYPE_WORK_LOCATION},
	}, stubExists, LocationValidationOptions{}); err == nil {
		t.Fatalf("expected missing work fields")
	}
	if err := ValidateLocationRequests([]*address.LocationRequest{
		{LocationType: address.LOCATION_TYPE_WORK_LOCATION, PrefectureName: "東京都"},
	}, stubExists, LocationValidationOptions{}); err == nil {
		t.Fatalf("expected missing city name")
	}
	if err := ValidateLocationRequests([]*address.LocationRequest{
		{LocationType: address.LOCATION_TYPE_WORK_LOCATION, CityName: "新宿区"},
	}, stubExists, LocationValidationOptions{}); err == nil {
		t.Fatalf("expected missing prefecture name")
	}
	if err := ValidateLocationRequests([]*address.LocationRequest{
		{LocationType: address.LOCATION_TYPE_WORK_LOCATION, PrefectureName: "大阪府", CityName: "大阪市"},
	}, stubExists, LocationValidationOptions{}); err == nil {
		t.Fatalf("expected work location not found")
	}
}

func TestNormalizePrefectureCity(t *testing.T) {
	pref, city := NormalizePrefectureCity("東京都", "新宿区")
	if pref != "東京都" || city != "23区" {
		t.Fatalf("unexpected normalized city: %s%s", pref, city)
	}
}

func TestValidateLocationRequests_UsesCommutingAreaLabelInErrors(t *testing.T) {
	err := ValidateLocationRequests([]*address.LocationRequest{
		{LocationType: address.LOCATION_TYPE_COMMUTING_AREAS},
	}, stubExists, LocationValidationOptions{})
	if err == nil {
		t.Fatalf("expected commuting area validation error")
	}
	if !strings.Contains(err.Error(), "通勤圏") {
		t.Fatalf("expected commuting area label in error, got: %v", err)
	}
	if strings.Contains(err.Error(), "希望勤務地") {
		t.Fatalf("expected error not to mention work location label, got: %v", err)
	}
}
