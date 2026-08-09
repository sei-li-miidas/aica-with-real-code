package shared_dto

import (
	"aica/api/domain/user/apply/vo"
)

type ValueText struct {
	ID   int
	Name string
	Note string
}
type ValueTexts []ValueText

type ValuesText struct {
	IDs  []IDWithName
	Note string
}

// ValuesTextWithOptions 選択した値以外のラベル付き
type ValueTextWithOptions struct {
	ID      int
	Name    string
	Note    string
	Options []IDWithName
}

// ValuesTextWithOptions 選択した値以外のラベル付き
type ValuesTextWithOptions struct {
	IDs     []IDWithName
	Note    string
	Options []IDWithName
}

// ValueTextsWithOptions 選択した値以外のラベル付き
type ValueTextsWithOptions struct {
	ValueTexts ValueTexts
	Options    []IDWithName
}

// Deprecated: use sdk/vo/IntIDNamePair
type IDWithName struct {
	ID   int
	Name string
}

type FlagText struct {
	Flg  *Flag
	Note string
}

type Flag struct {
	On   bool
	Name string
}

type TraitOption interface {
	GetValue() int
	GetUserSideName() string
}

func ShowValueText(v *vo.ValueText, findMasterFunc func(id int) string) *ValueText {
	if v == nil {
		return nil
	}
	return &ValueText{
		ID:   v.ID,
		Name: findMasterFunc(v.ID),
		Note: v.Text,
	}
}

func ShowValueTexts(vs vo.ValueTexts, findMasterFunc func(id int) string) *ValueTexts {
	values := make(ValueTexts, 0, len(vs))
	for _, v := range vs {
		values = append(values, ValueText{
			ID:   v.ID,
			Name: findMasterFunc(v.ID),
			Note: v.Text,
		})
	}
	return &values
}

func ShowValuesText(vs *vo.ValuesText, findMasterFunc func(id int) string) *ValuesText {
	if vs == nil {
		return nil
	}
	ids := make([]IDWithName, 0, len(vs.IDs))
	for _, v := range vs.IDs {
		ids = append(ids, IDWithName{
			ID:   v.ID,
			Name: findMasterFunc(v.ID),
		})
	}
	return &ValuesText{
		IDs:  ids,
		Note: vs.Text,
	}
}

func ShowValueTextWithOptions[T TraitOption](v *vo.ValueText, options []T) *ValueTextWithOptions {
	if v == nil {
		return nil
	}

	name := ""
	allOpts := make([]IDWithName, 0, len(options))
	for _, opt := range options {
		if opt.GetValue() == v.ID {
			name = opt.GetUserSideName()
		}
		allOpts = append(allOpts, IDWithName{
			ID:   opt.GetValue(),
			Name: opt.GetUserSideName(),
		})
	}

	return &ValueTextWithOptions{
		ID:      v.ID,
		Name:    name,
		Note:    v.Text,
		Options: allOpts,
	}
}

func ShowValuesTextWithOptions[T TraitOption](v *vo.ValuesText, options []T) *ValuesTextWithOptions {
	if v == nil {
		return nil
	}

	optMap := make(map[int]T, len(options))
	allOpts := make([]IDWithName, 0, len(options))
	for _, opt := range options {
		optMap[opt.GetValue()] = opt
		allOpts = append(allOpts, IDWithName{
			ID:   opt.GetValue(),
			Name: opt.GetUserSideName(),
		})
	}

	values := make([]IDWithName, 0, len(v.IDs))
	for _, idWithName := range v.IDs {
		if idWithName != nil {
			if opt, ok := optMap[idWithName.ID]; ok {
				values = append(values, IDWithName{
					ID:   idWithName.ID,
					Name: opt.GetUserSideName(),
				})
			}
		}
	}

	return &ValuesTextWithOptions{
		IDs:     values,
		Note:    v.Text,
		Options: allOpts,
	}
}

func ShowValueTextsWithOptions[T TraitOption](v vo.ValueTexts, options []T) *ValueTextsWithOptions {

	optMap := make(map[int]T, len(options))
	allOpts := make([]IDWithName, 0, len(options))
	for _, opt := range options {
		optMap[opt.GetValue()] = opt
		allOpts = append(allOpts, IDWithName{
			ID:   opt.GetValue(),
			Name: opt.GetUserSideName(),
		})
	}

	if v == nil {
		return &ValueTextsWithOptions{
			ValueTexts: nil,
			Options:    allOpts,
		}
	}

	valueTexts := make([]ValueText, 0, len(v))
	for _, valueText := range v {
		if valueText != nil {
			if opt, ok := optMap[valueText.ID]; ok {
				valueTexts = append(valueTexts, ValueText{
					ID:   valueText.ID,
					Name: opt.GetUserSideName(),
					Note: valueText.Text,
				})
			}
		}
	}

	return &ValueTextsWithOptions{
		ValueTexts: valueTexts,
		Options:    allOpts,
	}
}

func ShowFlagText(v *vo.FlagText, findMasterFunc func(on bool) string) *FlagText {
	if v == nil {
		return nil
	}
	return &FlagText{
		Flg: &Flag{
			On:   v.Flg.On,
			Name: findMasterFunc(v.Flg.On),
		},
		Note: v.Text,
	}
}

func ShowFlagWithFlagName(v *vo.Flag, flagName string) *Flag {
	if v == nil {
		return nil
	}
	return &Flag{
		On:   v.On,
		Name: flagName,
	}
}
