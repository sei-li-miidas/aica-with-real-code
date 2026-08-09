package support

import (
	"testing"
)

/*
実行方法
$ cd api/mcptool/usecase/position
$ go test
*/
func Test_calculateHighSalary(t *testing.T) {
	tests := []struct {
		name          string // ケース名
		desiredSalary int    // 希望年収
		highSalary    int    // 高額年収テーマの年収
	}{
		{
			name:          "0",
			desiredSalary: 0,
			highSalary:    198,
		},
		{
			name:          "100",
			desiredSalary: 100,
			highSalary:    294,
		},
		{
			name:          "200",
			desiredSalary: 200,
			highSalary:    385,
		},
		{
			name:          "300",
			desiredSalary: 300,
			highSalary:    464,
		},
		{
			name:          "400",
			desiredSalary: 400,
			highSalary:    524,
		},
		{
			name:          "500",
			desiredSalary: 500,
			highSalary:    576,
		},
		{
			name:          "550",
			desiredSalary: 550,
			highSalary:    604,
		},
		{
			name:          "600",
			desiredSalary: 600,
			highSalary:    636,
		},
		{
			name:          "700",
			desiredSalary: 700,
			highSalary:    715,
		},
		{
			name:          "800",
			desiredSalary: 800,
			highSalary:    806,
		},
		{
			name:          "900",
			desiredSalary: 900,
			highSalary:    902,
		},
		{
			name:          "1000",
			desiredSalary: 1000,
			highSalary:    1001,
		},
		{
			name:          "1100",
			desiredSalary: 1100,
			highSalary:    1100,
		},
		{
			name:          "1200",
			desiredSalary: 1200,
			highSalary:    1200,
		},
		{
			name:          "1300",
			desiredSalary: 1300,
			highSalary:    1300,
		},
	}

	runCase := func(tt struct {
		name          string
		desiredSalary int
		highSalary    int
	}) {
		t.Run(tt.name, func(t *testing.T) {
			highSalary := CalculateHighSalary(tt.desiredSalary)
			if highSalary != tt.highSalary {
				t.Errorf("CalculateHighSalary() = %v, want %v", highSalary, tt.highSalary)
			}
		})
	}

	runCase(tests[0])
	runCase(tests[1])
	runCase(tests[2])
	runCase(tests[3])
	runCase(tests[4])
	runCase(tests[5])
	runCase(tests[6])
	runCase(tests[7])
	runCase(tests[8])
	runCase(tests[9])
	runCase(tests[10])
	runCase(tests[11])
	runCase(tests[12])
	runCase(tests[13])
	runCase(tests[14])
}
