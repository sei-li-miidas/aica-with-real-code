import {
  GroupedJobtypeNamesWithSameSearchFilters,
  GroupedJobtypePositionSearchFilterOptions,
  GroupedOtherFilters,
  GroupedSelectedFilterOptions,
  JobtypePositionSearchFilter,
  LocationPositionSearchFilterOption,
  PositionSearchFilterType,
} from "@/lib/common";
import { createSlice, PayloadAction } from "@reduxjs/toolkit";

export type PositionSearchState = {
  // フィルター準備ができているか
  ready: boolean;
  // 現在アクティブな職種検索ツール
  activeToolName: string;
  // 職種
  jobtypes: JobtypePositionSearchFilter;
  jobtypeGroups: GroupedJobtypePositionSearchFilterOptions;
  // 希望年収
  salary: number;
  // フリーワード
  positionKeyword?: string;
  // 居住地（表示用テキスト）
  residence?: string;
  // 居住地の都道府県名
  residencePrefectureName?: string;
  // 居住地の市区町村名
  residenceCityName?: string;
  // 通勤可能エリア
  commutingAreas?: LocationPositionSearchFilterOption[];
  // 希望勤務地
  workLocations: LocationPositionSearchFilterOption[];
  // リモート可能
  remoteWorkPossible?: boolean;
  // 職種別ポジション検索詳細条件
  otherFilters: GroupedOtherFilters;
  // 職種別ポジション検索詳細条件の選択された値
  selectedFilterOptions: GroupedSelectedFilterOptions;
  // 同じポジション検索詳細条件を持ってる職種名（ツールごと）
  sameOtherFilterJobtypes: GroupedJobtypeNamesWithSameSearchFilters;
};

const normalizeJobtypeGroups = (
  groups: GroupedJobtypePositionSearchFilterOptions,
): GroupedJobtypePositionSearchFilterOptions => {
  const normalized: GroupedJobtypePositionSearchFilterOptions = {};

  for (const [toolName, options] of Object.entries(groups)) {
    normalized[toolName] = options.map((option) => ({
      ...option,
      Selected: Boolean(option.Selected),
    }));
  }

  return normalized;
};

const initialState: PositionSearchState = {
  ready: false,
  activeToolName: "",
  jobtypes: {
    Key: "",
    Name: "",
    Type: PositionSearchFilterType.Single,
    Options: [],
  },
  jobtypeGroups: {},
  salary: 0,
  workLocations: [],
  otherFilters: {},
  selectedFilterOptions: {},
  sameOtherFilterJobtypes: {},
};

const positionSearchSlice = createSlice({
  name: "position_search",
  initialState,
  reducers: {
    setReady(state, action: PayloadAction<boolean>) {
      state.ready = action.payload;
    },
    setActiveToolName(state, action: PayloadAction<string>) {
      state.activeToolName = action.payload;
    },
    setJobtypes(
      state,
      action: PayloadAction<GroupedJobtypePositionSearchFilterOptions>,
    ) {
      const incomingGroups = action.payload ?? {};
      const groupKeys = Object.keys(incomingGroups);
      const activeGroupKey =
        state.activeToolName && incomingGroups[state.activeToolName]
          ? state.activeToolName
          : groupKeys.length === 1
            ? groupKeys[0]
            : "";
      const groups = normalizeJobtypeGroups(incomingGroups);
      state.jobtypeGroups = groups;
      state.activeToolName = activeGroupKey;

      const options = activeGroupKey ? (groups[activeGroupKey] ?? []) : [];
      state.jobtypes.Options = options;
      const selectedOption = options.find((option) => option.Selected);
      state.jobtypes.Name = selectedOption?.Label ?? "";
    },
    setSalary(state, action: PayloadAction<number>) {
      state.salary = action.payload;
    },
    setPositionKeyword(state, action: PayloadAction<string>) {
      state.positionKeyword = action.payload;
    },
    clearPositionKeyword(state) {
      state.positionKeyword = undefined;
    },
    setResidence(
      state,
      action: PayloadAction<{
        residence: string;
        residencePrefectureName?: string;
        residenceCityName?: string;
        commutingAreas: LocationPositionSearchFilterOption[];
      }>,
    ) {
      state.residence = action.payload.residence;
      state.residencePrefectureName = action.payload.residencePrefectureName;
      state.residenceCityName = action.payload.residenceCityName;
      state.commutingAreas = (action.payload.commutingAreas ?? []).map((o) => ({
        ...o,
        Value: o.Value ?? `${o.PrefectureName ?? ""}${o.CityName ?? ""}`,
      }));
    },
    clearResidence(state) {
      state.residence = undefined;
      state.residencePrefectureName = undefined;
      state.residenceCityName = undefined;
      state.commutingAreas = undefined;
    },
    setRemoteWorkPossible(state, action: PayloadAction<boolean>) {
      state.remoteWorkPossible = action.payload;
    },
    clearRemoteWorkPossible(state) {
      state.remoteWorkPossible = undefined;
    },
    setWorkLocations(
      state,
      action: PayloadAction<LocationPositionSearchFilterOption[]>,
    ) {
      state.workLocations = (action.payload ?? []).map((o) => ({
        ...o,
        Value: o.Value ?? `${o.PrefectureName ?? ""}${o.CityName ?? ""}`,
      }));
    },
    clearWorkLocations(state) {
      state.workLocations = [];
    },
    setOtherFilters(state, action: PayloadAction<GroupedOtherFilters>) {
      state.otherFilters = action.payload ?? {};
    },
    clearOtherFilters(state) {
      state.otherFilters = {};
    },
    setSelectedFilterOptions(
      state,
      action: PayloadAction<GroupedSelectedFilterOptions>,
    ) {
      state.selectedFilterOptions = action.payload ?? {};
    },
    setSelectedFilterOptionsForTool(
      state,
      action: PayloadAction<{
        toolName: string;
        selectedFilterOptions: Record<string, string[]>;
      }>,
    ) {
      const { toolName, selectedFilterOptions } = action.payload;
      state.selectedFilterOptions = {
        ...(state.selectedFilterOptions ?? {}),
        [toolName]: selectedFilterOptions,
      };
    },
    clearSelectedFilterOptions(state) {
      state.selectedFilterOptions = {};
    },
    setSameOtherFilterJobtypes(
      state,
      action: PayloadAction<GroupedJobtypeNamesWithSameSearchFilters>,
    ) {
      state.sameOtherFilterJobtypes = action.payload;
    },
    clearSameOtherFilterJobtypes(state) {
      state.sameOtherFilterJobtypes = {};
    },
    toggleJobtypeOption(state, action: PayloadAction<string>) {
      const activeToolName = state.activeToolName;
      if (!activeToolName || !state.jobtypeGroups[activeToolName]) {
        return;
      }

      state.jobtypeGroups = Object.fromEntries(
        Object.entries(state.jobtypeGroups).map(([toolName, options]) => {
          if (toolName !== activeToolName) {
            return [
              toolName,
              options.map((option) => ({
                ...option,
                Selected: false,
              })),
            ];
          }

          return [
            toolName,
            options.map((option) => ({
              ...option,
              Selected:
                option.Value === action.payload
                  ? !option.Selected
                  : option.Selected,
            })),
          ];
        }),
      );

      state.jobtypes.Options = state.jobtypeGroups[activeToolName] ?? [];
      const selectedLabels = state.jobtypes.Options.filter(
        (option) => option.Selected,
      ).map((option) => option.Label);
      state.jobtypes.Name = selectedLabels.join("、");
    },
    toggleCommutingAreaOption(state, action: PayloadAction<string>) {
      const option = state.commutingAreas?.find(
        (o) => o.Value === action.payload,
      );
      if (option) option.Selected = !option.Selected;
    },
    toggleWorkLocationOption(state, action: PayloadAction<string>) {
      const option = state.workLocations.find(
        (o) => o.Value === action.payload,
      );
      if (option) option.Selected = !option.Selected;
    },
    toggleOtherFilterOption(
      state,
      action: PayloadAction<{
        toolName: string;
        filterName: string;
        optionName: string;
        filterType: PositionSearchFilterType;
      }>,
    ) {
      const { toolName, filterName, optionName, filterType } = action.payload;
      const selectedByTool = state.selectedFilterOptions[toolName] ?? {};
      const current = selectedByTool[filterName] ?? [];

      if (filterType === PositionSearchFilterType.Single) {
        const isAlreadySelected =
          current.length === 1 && current[0] === optionName;
        selectedByTool[filterName] = isAlreadySelected ? [] : [optionName];
      } else if (current.includes(optionName)) {
        selectedByTool[filterName] = current.filter(
          (value) => value !== optionName,
        );
      } else {
        selectedByTool[filterName] = [...current, optionName];
      }

      state.selectedFilterOptions[toolName] = selectedByTool;
    },
  },
});

export const {
  setReady,
  setActiveToolName,
  setJobtypes,
  setSalary,
  setPositionKeyword,
  clearPositionKeyword,
  setResidence,
  clearResidence,
  setRemoteWorkPossible,
  clearRemoteWorkPossible,
  setWorkLocations,
  clearWorkLocations,
  setOtherFilters,
  clearOtherFilters,
  setSelectedFilterOptions,
  setSelectedFilterOptionsForTool,
  clearSelectedFilterOptions,
  setSameOtherFilterJobtypes,
  clearSameOtherFilterJobtypes,
  toggleJobtypeOption,
  toggleCommutingAreaOption,
  toggleWorkLocationOption,
  toggleOtherFilterOption,
} = positionSearchSlice.actions;

export default positionSearchSlice.reducer;
