"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  createPositionSearchResultItem,
  JobtypePositionSearchFilterOption,
  IPositionSearchResult,
  LocationPositionSearchFilterOption,
  PositionSearchFilter,
  PositionSearchOtherFilterOption,
  PositionSearchFilterType,
  PositionSearchFilterOption,
} from "@/lib/common";
import { useAppDispatch, useAppSelector } from "@/lib/store/hooks";
import { addMainChatPositionSearchResultItem } from "@/lib/store/features/websocket/websocketSlice";
import { LocationType } from "@/constants/profile";
import { Address } from "@/types/utility-types";
import {
  clearRemoteWorkPossible,
  clearPositionKeyword,
  clearResidence,
  setActiveToolName,
  setJobtypes,
  setOtherFilters,
  setReady,
  setRemoteWorkPossible,
  setPositionKeyword,
  setResidence,
  setSalary,
  setSelectedFilterOptions,
  setWorkLocations,
} from "@/lib/store/features/position_search/positionSearchSlice";
import {
  DetailSelections,
  FilterModalType,
  FilterOptionView,
  SubModalType,
} from "@/components/chat/jobSearchFilterDialog/types";
import { fetchApiData, searchCommutingAreas } from "@/utils/fetch";
import { sendWebSocketMessage } from "@/lib/socket";
import { ChatRequestType, PageName } from "@/constants/enum";

const MIN_SALARY = 100;
const MAX_SALARY = 9999;

const JOBTYPE_GROUP_LABELS: Record<string, string> = {
  search_job_postings_for_it_engineer: "IT開発系",
  search_job_postings_for_sales_financial_sales: "金融営業",
  search_job_postings: "その他",
};

const jobtypeGroupLabel = (toolName: string) =>
  JOBTYPE_GROUP_LABELS[toolName] ?? toolName;

type JobtypeSpecificSearchOverrides = {
  selectedJobtypeNames?: string[];
  salary?: number;
  positionKeyword?: string;
  residencePrefectureName?: string;
  residenceCityName?: string;
  commutingAreaOptions?: LocationPositionSearchFilterOption[];
  commutingAreas?: string[];
  workLocations?: string[];
  workLocationOptions?: LocationPositionSearchFilterOption[];
  remoteWorkPossible?: boolean;
  selectedFilterOptions?: Record<string, string[]>;
};

type JobtypeSpecificDetailParam = string | string[];

type AddressSelectionMode = "residence" | "other-location" | null;

type LocationRequestPayload = {
  LocationType: string;
  PrefectureName: string;
  CityName: string;
};

const residenceKey = (prefectureName?: string, cityName?: string) =>
  prefectureName && cityName ? `${prefectureName}\n${cityName}` : "";

const toSingleLocationRequest = (
  locationType: LocationType,
  prefectureName?: string,
  cityName?: string,
): LocationRequestPayload[] =>
  prefectureName && cityName
    ? [
        {
          LocationType: locationType,
          PrefectureName: prefectureName,
          CityName: cityName,
        },
      ]
    : [];

const toLocationRequests = (
  locationType: LocationType,
  options: LocationPositionSearchFilterOption[] | undefined,
  selectedValues: string[],
): LocationRequestPayload[] =>
  (options ?? [])
    .filter((option) => selectedValues.includes(option.Value))
    .map((option) => ({
      LocationType: locationType,
      PrefectureName: option.PrefectureName,
      CityName: option.CityName,
    }));

const toLocationOptionFromAddress = (
  address: Address,
): LocationPositionSearchFilterOption => {
  const value = `${address.prefecture.Name}${address.city.Name}`;
  return {
    Label: value,
    Value: value,
    Selected: false,
    PrefectureName: address.prefecture.Name,
    CityName: address.city.Name,
  };
};

const toCommutingAreaOptions = (
  addresses: Address[],
): LocationPositionSearchFilterOption[] =>
  addresses.map(toLocationOptionFromAddress);

type DetailGroupView = {
  // 詳細条件フィルターの識別子
  key: string;
  // API 送信用のキー
  requestKey: string;
  // 詳細条件フィルターの表示名
  label: string;
  // 単一選択 / 複数選択
  type: PositionSearchFilterType;
  // UI 表示用に正規化した選択肢
  options: FilterOptionView[];
};

// 通勤可能エリア/その他勤務地選択肢を UI 用の形式へ変換
const toViewOption = (
  option: PositionSearchFilterOption,
): FilterOptionView => ({
  label: option.Label,
  value: option.Value,
});

// 詳細条件選択肢を UI 用の形式へ変換
const toOtherFilterViewOption = (
  option: PositionSearchOtherFilterOption,
): FilterOptionView => ({
  label: option.Label,
  value: option.Value,
});

// 職種選択肢を UI 用の形式へ変換（説明文つき）
const toJobtypeViewOption = (
  option: JobtypePositionSearchFilterOption,
): FilterOptionView => ({
  label: option.Label,
  value: option.Value,
  description: option.Description,
});

// Selected=true の選択肢 Value 一覧を抽出
const toSelectedValues = (options: PositionSearchFilterOption[] | undefined) =>
  (options ?? [])
    .filter((option) => option.Selected)
    .map((option) => option.Value);

const toDetailSelections = (
  groups: DetailGroupView[],
  selectedMap: Record<string, string[]>,
): DetailSelections =>
  Object.fromEntries(
    groups.map((group) => [group.key, selectedMap[group.key] ?? []]),
  );

const toDetailGroupViews = (
  filters: PositionSearchFilter<PositionSearchOtherFilterOption>[],
): DetailGroupView[] =>
  filters.map((filter) => ({
    key: filter.Name,
    requestKey: filter.Key,
    label: filter.Name,
    type: filter.Type,
    options: filter.Options.map(toOtherFilterViewOption),
  }));

/**
 * 空行を除いたフリーワード行数を数える。
 *
 * 前後の空白を除去したうえで、入力済みの検索語数に合わせて
 * フリーワードタブのバッジ表示を更新するために使う。
 */
const normalizeKeywordLines = (keyword: string | undefined) =>
  (keyword ?? "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

const countKeywordLines = (keyword: string | undefined) =>
  normalizeKeywordLines(keyword).length;

const resolveActiveToolName = (
  activeToolName: string,
  jobtypeGroups: Record<string, JobtypePositionSearchFilterOption[]>,
) => {
  if (activeToolName && jobtypeGroups[activeToolName]) {
    return activeToolName;
  }
  const groupKeys = Object.keys(jobtypeGroups);
  return groupKeys.length === 1 ? groupKeys[0] : "";
};

const toggleJobtypeGroups = (
  groups: Record<string, JobtypePositionSearchFilterOption[]>,
  activeToolName: string,
  value: string,
) =>
  Object.fromEntries(
    Object.entries(groups).map(([toolName, options]) => {
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
          Selected: option.Value === value ? !option.Selected : option.Selected,
        })),
      ];
    }),
  );

export function useJobSearchFilterDialogState() {
  // Redux
  const dispatch = useAppDispatch();
  const positionSearch = useAppSelector((state) => state.positionSearch);

  // モーダル表示状態
  const [filterModalOpen, setFilterModalOpen] = useState(false);
  const [filterModalType, setFilterModalType] = useState<FilterModalType>(null);
  const [subModalType, setSubModalType] = useState<SubModalType>(null);

  const persistedPrimaryLocationOptions = useMemo(
    () => positionSearch.commutingAreas ?? [],
    [positionSearch.commutingAreas],
  );

  // 勤務地選択肢（通勤可能エリア/その他勤務地）
  const otherLocationOptions = useMemo(
    () => positionSearch.workLocations.map(toViewOption),
    [positionSearch.workLocations],
  );

  // 現在選択済みの勤務地 Value 一覧
  const selectedPrimaryLocationValues = useMemo(
    () => toSelectedValues(positionSearch.commutingAreas),
    [positionSearch.commutingAreas],
  );
  const selectedOtherLocationValues = useMemo(
    () => toSelectedValues(positionSearch.workLocations),
    [positionSearch.workLocations],
  );

  const activeToolName = positionSearch.activeToolName;

  // ダイアログ内ドラフト値（未確定）
  const [draftResidence, setDraftResidence] = useState<string | undefined>(
    positionSearch.residence,
  );
  const [draftResidencePrefectureName, setDraftResidencePrefectureName] =
    useState<string | undefined>(positionSearch.residencePrefectureName);
  const [draftResidenceCityName, setDraftResidenceCityName] = useState<
    string | undefined
  >(positionSearch.residenceCityName);
  const [draftPrimaryLocationOptions, setDraftPrimaryLocationOptions] =
    useState<LocationPositionSearchFilterOption[]>(
      persistedPrimaryLocationOptions,
    );
  const [draftPrimaryLocations, setDraftPrimaryLocations] = useState<string[]>(
    selectedPrimaryLocationValues,
  );
  const [draftOtherLocations, setDraftOtherLocations] = useState<string[]>(
    selectedOtherLocationValues,
  );
  const [draftOtherLocationOptions, setDraftOtherLocationOptions] = useState<
    LocationPositionSearchFilterOption[]
  >(positionSearch.workLocations);
  const [draftRemoteWorkPossible, setDraftRemoteWorkPossible] = useState<
    boolean | undefined
  >(positionSearch.remoteWorkPossible);
  const [draftActiveToolName, setDraftActiveToolName] = useState(
    positionSearch.activeToolName,
  );
  const [draftJobtypeGroups, setDraftJobtypeGroups] = useState(
    positionSearch.jobtypeGroups,
  );
  const [draftOtherFilters, setDraftOtherFilters] = useState(
    positionSearch.otherFilters,
  );
  const [draftSelectedFilterOptions, setDraftSelectedFilterOptions] = useState(
    positionSearch.selectedFilterOptions,
  );
  const [draftDetailGroups, setDraftDetailGroups] = useState<DetailSelections>(
    () => {
      const initialToolName = resolveActiveToolName(
        positionSearch.activeToolName,
        positionSearch.jobtypeGroups,
      );
      return toDetailSelections(
        toDetailGroupViews(positionSearch.otherFilters[initialToolName] ?? []),
        positionSearch.selectedFilterOptions[initialToolName] ?? {},
      );
    },
  );
  const [draftDetailToolName, setDraftDetailToolName] = useState(
    positionSearch.activeToolName,
  );
  // 年収ダイアログのドラフト値
  const [salaryDraft, setSalaryDraft] = useState<number>(
    positionSearch.salary > 0 ? positionSearch.salary : 300,
  );
  const [keywordDraft, setKeywordDraft] = useState<string>(
    positionSearch.positionKeyword ?? "",
  );

  // 職種ヘルプダイアログ状態
  const [jobtypeHelpOpen, setJobtypeHelpOpen] = useState(false);
  const [jobtypeHelpTarget, setJobtypeHelpTarget] = useState<string>("");
  const [jobtypeHelpDescription, setJobtypeHelpDescription] =
    useState<string>("");
  const [addressSelectionModalOpen, setAddressSelectionModalOpen] =
    useState(false);
  const [addressSelectionMode, setAddressSelectionMode] =
    useState<AddressSelectionMode>(null);

  // グループ切り替え確認ダイアログの状態
  const [groupSwitchConfirmPending, setGroupSwitchConfirmPending] = useState<{
    value: string;
    toolName: string;
  } | null>(null);

  // モーダル表示中の変更はタブを跨いで保持し、確定/キャンセル時だけ反映を切り替える
  const modalSessionSnapshotRef = useRef<{
    salary: typeof positionSearch.salary;
    positionKeyword: typeof positionSearch.positionKeyword;
    residence: typeof positionSearch.residence;
    residencePrefectureName: typeof positionSearch.residencePrefectureName;
    residenceCityName: typeof positionSearch.residenceCityName;
    commutingAreas: typeof positionSearch.commutingAreas;
    workLocations: typeof positionSearch.workLocations;
    remoteWorkPossible: typeof positionSearch.remoteWorkPossible;
    activeToolName: string;
    jobtypeGroups: typeof positionSearch.jobtypeGroups;
    otherFilters: typeof positionSearch.otherFilters;
    selectedFilterOptions: typeof positionSearch.selectedFilterOptions;
  } | null>(null);
  const hydratedResidenceKeyRef = useRef("");

  const snapshotModalSessionState = useCallback(() => {
    modalSessionSnapshotRef.current = {
      salary: positionSearch.salary,
      positionKeyword: positionSearch.positionKeyword,
      residence: positionSearch.residence,
      residencePrefectureName: positionSearch.residencePrefectureName,
      residenceCityName: positionSearch.residenceCityName,
      commutingAreas: positionSearch.commutingAreas,
      workLocations: positionSearch.workLocations,
      remoteWorkPossible: positionSearch.remoteWorkPossible,
      activeToolName: positionSearch.activeToolName,
      jobtypeGroups: positionSearch.jobtypeGroups,
      otherFilters: positionSearch.otherFilters,
      selectedFilterOptions: positionSearch.selectedFilterOptions,
    };
  }, [
    positionSearch.salary,
    positionSearch.positionKeyword,
    positionSearch.residence,
    positionSearch.residencePrefectureName,
    positionSearch.residenceCityName,
    positionSearch.commutingAreas,
    positionSearch.workLocations,
    positionSearch.remoteWorkPossible,
    positionSearch.activeToolName,
    positionSearch.jobtypeGroups,
    positionSearch.otherFilters,
    positionSearch.selectedFilterOptions,
  ]);

  const clearModalSessionSnapshot = useCallback(() => {
    modalSessionSnapshotRef.current = null;
  }, []);

  const restoreModalSessionSnapshot = useCallback(() => {
    const snapshot = modalSessionSnapshotRef.current;
    if (!snapshot) {
      return false;
    }

    dispatch(setSalary(snapshot.salary));
    if (snapshot.positionKeyword?.trim()) {
      dispatch(setPositionKeyword(snapshot.positionKeyword));
    } else {
      dispatch(clearPositionKeyword());
    }
    if (snapshot.residence) {
      dispatch(
        setResidence({
          residence: snapshot.residence,
          residencePrefectureName: snapshot.residencePrefectureName,
          residenceCityName: snapshot.residenceCityName,
          commutingAreas: snapshot.commutingAreas ?? [],
        }),
      );
    } else {
      dispatch(clearResidence());
    }
    dispatch(setWorkLocations(snapshot.workLocations ?? []));
    if (typeof snapshot.remoteWorkPossible === "boolean") {
      dispatch(setRemoteWorkPossible(snapshot.remoteWorkPossible));
    } else {
      dispatch(clearRemoteWorkPossible());
    }
    dispatch(setActiveToolName(snapshot.activeToolName));
    dispatch(setJobtypes(snapshot.jobtypeGroups));
    dispatch(setOtherFilters(snapshot.otherFilters));
    dispatch(setSelectedFilterOptions(snapshot.selectedFilterOptions));
    modalSessionSnapshotRef.current = null;
    return true;
  }, [dispatch]);

  const initializeModalDrafts = useCallback(() => {
    const nextDraftActiveToolName = resolveActiveToolName(
      positionSearch.activeToolName,
      positionSearch.jobtypeGroups,
    );
    const persistedDetailGroups = toDetailSelections(
      toDetailGroupViews(
        positionSearch.otherFilters[nextDraftActiveToolName] ?? [],
      ),
      positionSearch.selectedFilterOptions[nextDraftActiveToolName] ?? {},
    );
    setDraftResidence(positionSearch.residence);
    setDraftResidencePrefectureName(positionSearch.residencePrefectureName);
    setDraftResidenceCityName(positionSearch.residenceCityName);
    setDraftPrimaryLocationOptions(persistedPrimaryLocationOptions);
    setDraftPrimaryLocations(selectedPrimaryLocationValues);
    setDraftOtherLocations(selectedOtherLocationValues);
    setDraftOtherLocationOptions(positionSearch.workLocations);
    setDraftRemoteWorkPossible(positionSearch.remoteWorkPossible);
    setDraftActiveToolName(nextDraftActiveToolName);
    setDraftJobtypeGroups(positionSearch.jobtypeGroups);
    setDraftOtherFilters(positionSearch.otherFilters);
    setDraftSelectedFilterOptions(positionSearch.selectedFilterOptions);
    setDraftDetailToolName(nextDraftActiveToolName);
    setDraftDetailGroups(persistedDetailGroups);
    setSalaryDraft(positionSearch.salary > 0 ? positionSearch.salary : 300);
    setKeywordDraft(positionSearch.positionKeyword ?? "");
  }, [
    persistedPrimaryLocationOptions,
    positionSearch.positionKeyword,
    positionSearch.remoteWorkPossible,
    positionSearch.residence,
    positionSearch.residenceCityName,
    positionSearch.residencePrefectureName,
    positionSearch.salary,
    positionSearch.jobtypeGroups,
    positionSearch.otherFilters,
    positionSearch.selectedFilterOptions,
    positionSearch.activeToolName,
    positionSearch.workLocations,
    selectedOtherLocationValues,
    selectedPrimaryLocationValues,
  ]);

  const resolvedDraftActiveToolName = useMemo(
    () => resolveActiveToolName(draftActiveToolName, draftJobtypeGroups),
    [draftActiveToolName, draftJobtypeGroups],
  );
  const effectiveActiveToolName = useMemo(
    () => (filterModalOpen ? resolvedDraftActiveToolName : activeToolName),
    [activeToolName, filterModalOpen, resolvedDraftActiveToolName],
  );
  const effectiveJobtypeGroups = useMemo(
    () => (filterModalOpen ? draftJobtypeGroups : positionSearch.jobtypeGroups),
    [draftJobtypeGroups, filterModalOpen, positionSearch.jobtypeGroups],
  );
  const effectiveJobtypeOptions = useMemo(
    () =>
      effectiveActiveToolName
        ? (effectiveJobtypeGroups[effectiveActiveToolName] ?? [])
        : positionSearch.jobtypes.Options,
    [
      effectiveActiveToolName,
      effectiveJobtypeGroups,
      positionSearch.jobtypes.Options,
    ],
  );
  const effectiveOtherFilters = filterModalOpen
    ? draftOtherFilters
    : positionSearch.otherFilters;
  const effectiveSelectedFilterOptions = filterModalOpen
    ? draftSelectedFilterOptions
    : positionSearch.selectedFilterOptions;
  const selectedJobtypeOptions = useMemo(
    () => effectiveJobtypeOptions.filter((option) => option.Selected),
    [effectiveJobtypeOptions],
  );
  const selectedJobtype =
    selectedJobtypeOptions.length > 0
      ? selectedJobtypeOptions.map((option) => option.Label).join("、")
      : "職種";
  const selectedJobtypeValues = useMemo(
    () => selectedJobtypeOptions.map((option) => option.Value),
    [selectedJobtypeOptions],
  );
  const salaryLabel = (() => {
    const effectiveSalary = filterModalOpen
      ? salaryDraft
      : positionSearch.salary;
    return effectiveSalary > 0 ? `${effectiveSalary}` : "希望年収";
  })();
  const selectedDetailByJobtype = useMemo(
    () => effectiveSelectedFilterOptions[effectiveActiveToolName] ?? {},
    [effectiveActiveToolName, effectiveSelectedFilterOptions],
  );
  const committedDetailGroups = useMemo<DetailSelections>(
    () =>
      toDetailSelections(
        toDetailGroupViews(positionSearch.otherFilters[activeToolName] ?? []),
        positionSearch.selectedFilterOptions[activeToolName] ?? {},
      ),
    [
      activeToolName,
      positionSearch.otherFilters,
      positionSearch.selectedFilterOptions,
    ],
  );
  const detailGroups = useMemo<DetailGroupView[]>(
    () =>
      (effectiveOtherFilters[effectiveActiveToolName] ?? []).map((filter) => ({
        key: filter.Name,
        requestKey: filter.Key,
        label: filter.Name,
        type: filter.Type,
        options: filter.Options.map(toOtherFilterViewOption),
      })),
    [effectiveActiveToolName, effectiveOtherFilters],
  );
  const committedSelectedFilterOptions = useMemo(
    () => ({
      ...draftSelectedFilterOptions,
      ...(draftDetailToolName
        ? { [draftDetailToolName]: draftDetailGroups }
        : {}),
    }),
    [draftDetailGroups, draftDetailToolName, draftSelectedFilterOptions],
  );
  const committedJobtypeOptions = useMemo(
    () =>
      effectiveActiveToolName
        ? (draftJobtypeGroups[effectiveActiveToolName] ?? [])
        : [],
    [draftJobtypeGroups, effectiveActiveToolName],
  );
  const committedSelectedJobtypeNames = useMemo(
    () =>
      committedJobtypeOptions
        .filter((option) => option.Selected)
        .map((option) => option.Label),
    [committedJobtypeOptions],
  );

  // 通勤可能エリアの親見出し（ドラフト値）
  const primaryLocationTitle = draftResidence
    ? `${draftResidence}周辺`
    : "通勤可能エリア";
  const primaryLocationOptions = useMemo(
    () => draftPrimaryLocationOptions.map(toViewOption),
    [draftPrimaryLocationOptions],
  );

  // 条件変更後に職種別ポジション検索 API を実行し、結果をチャットへ追加
  const runJobtypeSpecificSearch = useCallback(
    async (overrides: JobtypeSpecificSearchOverrides = {}) => {
      const selectedJobtypeNames =
        overrides.selectedJobtypeNames ??
        selectedJobtypeOptions.map((option) => option.Label);
      if (selectedJobtypeNames.length === 0) {
        return;
      }

      const result = await fetchApiData(
        "positions/search/jobtype_specific",
        "ポジション検索に失敗しました",
        {
          method: "POST",
          data: (() => {
            const selectedDetail =
              overrides.selectedFilterOptions ?? selectedDetailByJobtype;
            const detailByKey = detailGroups.reduce<
              Record<string, JobtypeSpecificDetailParam>
            >((acc, group) => {
              const selectedValues = selectedDetail[group.key] ?? [];
              acc[group.requestKey] =
                group.type === PositionSearchFilterType.Single
                  ? (selectedValues[0] ?? "")
                  : selectedValues;
              return acc;
            }, {});

            const locations = [
              ...toSingleLocationRequest(
                LocationType.RESIDENCE,
                overrides.residencePrefectureName ??
                  positionSearch.residencePrefectureName,
                overrides.residenceCityName ?? positionSearch.residenceCityName,
              ),
              ...toLocationRequests(
                LocationType.COMMUTING_AREAS,
                overrides.commutingAreaOptions ?? positionSearch.commutingAreas,
                overrides.commutingAreas ?? selectedPrimaryLocationValues,
              ),
              ...toLocationRequests(
                LocationType.WORK_LOCATION,
                overrides.workLocationOptions ?? positionSearch.workLocations,
                overrides.workLocations ?? selectedOtherLocationValues,
              ),
            ];
            const remoteWorkPossible =
              overrides.remoteWorkPossible ?? positionSearch.remoteWorkPossible;
            const positionKeyword =
              overrides.positionKeyword ?? positionSearch.positionKeyword ?? "";
            const trimmedPositionKeyword = positionKeyword.trim();

            return {
              JobTypeNames: selectedJobtypeNames,
              Salary: overrides.salary ?? positionSearch.salary,
              Locations: locations,
              ...(trimmedPositionKeyword
                ? { PositionKeyword: trimmedPositionKeyword }
                : {}),
              ...(remoteWorkPossible !== undefined
                ? { RemoteWorkPossible: remoteWorkPossible }
                : {}),
              ...detailByKey,
            };
          })(),
        },
      );

      if (result.error || !result.data) {
        return;
      }

      const searchResult = (result.data.SearchResult ??
        result.data) as IPositionSearchResult;
      if (!Array.isArray(searchResult.Positions)) {
        return;
      }

      const itemId = `local_position_search_${crypto.randomUUID()}`;
      const newItem = createPositionSearchResultItem(
        itemId,
        JSON.stringify(searchResult),
      );
      dispatch(addMainChatPositionSearchResultItem(newItem));
    },
    [
      selectedJobtypeOptions,
      dispatch,
      selectedDetailByJobtype,
      detailGroups,
      positionSearch.commutingAreas,
      positionSearch.residencePrefectureName,
      positionSearch.residenceCityName,
      positionSearch.workLocations,
      positionSearch.salary,
      positionSearch.positionKeyword,
      selectedPrimaryLocationValues,
      selectedOtherLocationValues,
      positionSearch.remoteWorkPossible,
    ],
  );

  // すべてのモーダルを閉じる
  const closeAllModals = useCallback(() => {
    setSubModalType(null);
    setFilterModalType(null);
    setFilterModalOpen(false);
  }, []);

  useEffect(() => {
    if (filterModalType === "detail" && detailGroups.length === 0) {
      closeAllModals();
    }
  }, [closeAllModals, detailGroups.length, filterModalType]);

  useEffect(() => {
    const prefectureName = draftResidencePrefectureName;
    const cityName = draftResidenceCityName;
    const currentResidenceKey = residenceKey(prefectureName, cityName);
    if (!currentResidenceKey) {
      hydratedResidenceKeyRef.current = "";
      return;
    }
    if (!prefectureName || !cityName) {
      hydratedResidenceKeyRef.current = "";
      return;
    }
    if (!filterModalOpen) {
      hydratedResidenceKeyRef.current = "";
      return;
    }
    if (draftPrimaryLocationOptions.length > 0) {
      return;
    }
    if (hydratedResidenceKeyRef.current === currentResidenceKey) {
      return;
    }

    let active = true;

    void (async () => {
      const commutingAreaAddresses = await searchCommutingAreas(
        prefectureName,
        cityName,
      );
      if (!active) {
        return;
      }
      if (commutingAreaAddresses.length === 0) {
        hydratedResidenceKeyRef.current = "";
        return;
      }
      hydratedResidenceKeyRef.current = currentResidenceKey;
      setDraftPrimaryLocationOptions(
        toCommutingAreaOptions(commutingAreaAddresses),
      );
    })();

    return () => {
      active = false;
    };
  }, [
    draftPrimaryLocationOptions.length,
    draftResidenceCityName,
    draftResidencePrefectureName,
    filterModalOpen,
  ]);

  // 指定フィルターのモーダルを開く（必要に応じてドラフト初期化）
  const openFilter = useCallback(
    (type: Exclude<FilterModalType, null>) => {
      if (type === "detail" && detailGroups.length === 0) {
        return;
      }
      if (!filterModalOpen) {
        snapshotModalSessionState();
        initializeModalDrafts();
      } else if (
        type === "detail" &&
        draftDetailToolName !== effectiveActiveToolName
      ) {
        setDraftDetailToolName(effectiveActiveToolName);
        setDraftDetailGroups(
          toDetailSelections(
            detailGroups,
            effectiveSelectedFilterOptions[effectiveActiveToolName] ?? {},
          ),
        );
      }
      setFilterModalType(type);
      setSubModalType(null);
      setFilterModalOpen(true);
    },
    [
      filterModalOpen,
      draftDetailToolName,
      initializeModalDrafts,
      detailGroups,
      effectiveActiveToolName,
      effectiveSelectedFilterOptions,
      snapshotModalSessionState,
    ],
  );

  // 職種ヘルプを開く
  const openJobtypeHelp = useCallback((option: FilterOptionView) => {
    setJobtypeHelpTarget(option.label);
    setJobtypeHelpDescription(option.description ?? "");
    setJobtypeHelpOpen(true);
  }, []);

  // 「上記以外の職種を検討したい」を選択
  const selectOtherJobtype = useCallback(() => {
    // ポジション検索フッターバーを隠す
    dispatch(setReady(false));
    clearModalSessionSnapshot();
    closeAllModals();
    // 現在選択中の職種を外す
    sendWebSocketMessage(
      dispatch,
      ChatRequestType.JobTypesClear,
      PageName.Chat,
      PageName.Chat,
      null,
      null,
      null,
      false,
    );
  }, [clearModalSessionSnapshot, closeAllModals, dispatch]);

  // グループ切り替えを実際に実行する内部関数
  const executeGroupSwitch = useCallback(
    async (
      value: string,
      requestedToolName: string,
      isDifferentGroup: boolean,
    ) => {
      // The requested tool can be stale if the available draft groups changed,
      // so resolve it against the current draft state before using it.
      const normalizedToolName = resolveActiveToolName(
        requestedToolName,
        draftJobtypeGroups,
      );
      const groupOptions = normalizedToolName
        ? (draftJobtypeGroups[normalizedToolName] ?? [])
        : [];
      const selectedOption = groupOptions.find(
        (option) => option.Value === value,
      );
      const selectedJobtypeName = selectedOption?.Label ?? "";
      const willSelectJobtype = !Boolean(selectedOption?.Selected);

      const nextJobtypeGroups = normalizedToolName
        ? toggleJobtypeGroups(draftJobtypeGroups, normalizedToolName, value)
        : draftJobtypeGroups;
      setDraftActiveToolName(normalizedToolName);
      setDraftJobtypeGroups(nextJobtypeGroups);

      const hasLocalDetailFilters =
        !!normalizedToolName &&
        Object.prototype.hasOwnProperty.call(
          draftOtherFilters,
          normalizedToolName,
        );
      let nextGroupOtherFilters = normalizedToolName
        ? (draftOtherFilters[normalizedToolName] ?? [])
        : [];

      if (!hasLocalDetailFilters && willSelectJobtype && selectedJobtypeName) {
        const result = await fetchApiData(
          `positions/search_filter/jobtype?JobtypeName=${encodeURIComponent(selectedJobtypeName)}`,
          "ポジション検索条件取得に失敗しました",
          { method: "GET" },
        );

        if (!result.error && result.data) {
          const source = result.data.SearchFilters ?? result.data;
          nextGroupOtherFilters = Array.isArray(source.OtherFilters)
            ? source.OtherFilters
            : [];

          setDraftOtherFilters((prev) => ({
            ...prev,
            ...(normalizedToolName
              ? { [normalizedToolName]: nextGroupOtherFilters }
              : {}),
          }));
          const validNextToolName = normalizedToolName.trim();
          if (validNextToolName) {
            const nextSelectedFilterOptions =
              source.SelectedFilterOptions &&
              typeof source.SelectedFilterOptions === "object" &&
              !Array.isArray(source.SelectedFilterOptions)
                ? source.SelectedFilterOptions
                : {};
            setDraftSelectedFilterOptions((prev) => ({
              ...prev,
              [validNextToolName]: nextSelectedFilterOptions,
            }));
            if (isDifferentGroup) {
              setDraftDetailToolName(validNextToolName);
              setDraftDetailGroups(
                toDetailSelections(
                  toDetailGroupViews(nextGroupOtherFilters),
                  nextSelectedFilterOptions,
                ),
              );
            }
          }
        }
      }

      // グループ切り替え後、詳細条件があれば `その他` タブへ自動で切り替える。
      if (isDifferentGroup && nextGroupOtherFilters.length > 0) {
        if (draftDetailToolName !== normalizedToolName) {
          setDraftDetailToolName(normalizedToolName);
          setDraftDetailGroups(
            toDetailSelections(
              toDetailGroupViews(nextGroupOtherFilters),
              draftSelectedFilterOptions[normalizedToolName] ?? {},
            ),
          );
        }
        setFilterModalType("detail");
        setSubModalType(null);
      }
    },
    [
      draftDetailToolName,
      draftJobtypeGroups,
      draftOtherFilters,
      draftSelectedFilterOptions,
    ],
  );

  // 職種を更新（検索は実行しない）
  const selectJobtype = useCallback(
    async (value: string, toolName?: string) => {
      const nextToolName = toolName ?? effectiveActiveToolName;
      const isDifferentGroup = nextToolName !== effectiveActiveToolName;

      if (isDifferentGroup) {
        setGroupSwitchConfirmPending({ value, toolName: nextToolName });
        return;
      }

      await executeGroupSwitch(value, nextToolName, false);
    },
    [effectiveActiveToolName, executeGroupSwitch],
  );

  // グループ切り替え確認ダイアログで「続ける」を押した
  const confirmGroupSwitch = useCallback(async () => {
    if (!groupSwitchConfirmPending) return;
    const { value, toolName } = groupSwitchConfirmPending;
    setGroupSwitchConfirmPending(null);
    await executeGroupSwitch(value, toolName, true);
  }, [executeGroupSwitch, groupSwitchConfirmPending]);

  // グループ切り替え確認ダイアログで「キャンセル」を押した
  const cancelGroupSwitch = useCallback(() => {
    setGroupSwitchConfirmPending(null);
  }, []);

  const commitModalSessionDrafts = useCallback(() => {
    const nextCommutingAreas = draftPrimaryLocationOptions.map((option) => ({
      ...option,
      Selected: draftPrimaryLocations.includes(option.Value),
    }));
    const nextWorkLocations = draftOtherLocationOptions.map((option) => ({
      ...option,
      Selected: draftOtherLocations.includes(option.Value),
    }));
    const normalizedKeyword = normalizeKeywordLines(keywordDraft).join("\n");

    dispatch(setSalary(salaryDraft));
    if (normalizedKeyword) {
      dispatch(setPositionKeyword(normalizedKeyword));
    } else {
      dispatch(clearPositionKeyword());
    }
    if (draftResidence) {
      dispatch(
        setResidence({
          residence: draftResidence,
          residencePrefectureName: draftResidencePrefectureName,
          residenceCityName: draftResidenceCityName,
          commutingAreas: nextCommutingAreas,
        }),
      );
    } else {
      dispatch(clearResidence());
    }
    dispatch(setWorkLocations(nextWorkLocations));
    if (draftRemoteWorkPossible !== undefined) {
      dispatch(setRemoteWorkPossible(draftRemoteWorkPossible));
    } else {
      dispatch(clearRemoteWorkPossible());
    }
    dispatch(setActiveToolName(effectiveActiveToolName));
    dispatch(setJobtypes(draftJobtypeGroups));
    dispatch(setOtherFilters(draftOtherFilters));
    dispatch(setSelectedFilterOptions(committedSelectedFilterOptions));

    return {
      residencePrefectureName: draftResidencePrefectureName,
      residenceCityName: draftResidenceCityName,
      commutingAreaOptions: nextCommutingAreas,
      commutingAreas: draftPrimaryLocations,
      workLocationOptions: nextWorkLocations,
      workLocations: draftOtherLocations,
      remoteWorkPossible: draftRemoteWorkPossible,
      salary: salaryDraft,
      positionKeyword: normalizedKeyword,
      selectedJobtypeNames: committedSelectedJobtypeNames,
      selectedFilterOptions:
        committedSelectedFilterOptions[effectiveActiveToolName] ?? {},
    };
  }, [
    committedSelectedFilterOptions,
    committedSelectedJobtypeNames,
    dispatch,
    draftJobtypeGroups,
    draftOtherFilters,
    draftOtherLocationOptions,
    draftOtherLocations,
    draftPrimaryLocationOptions,
    draftPrimaryLocations,
    draftRemoteWorkPossible,
    draftResidence,
    draftResidenceCityName,
    draftResidencePrefectureName,
    effectiveActiveToolName,
    keywordDraft,
    salaryDraft,
  ]);

  const applyJobtype = useCallback(async () => {
    const searchOverrides = commitModalSessionDrafts();
    clearModalSessionSnapshot();
    await runJobtypeSpecificSearch(searchOverrides);
    closeAllModals();
  }, [
    clearModalSessionSnapshot,
    closeAllModals,
    commitModalSessionDrafts,
    runJobtypeSpecificSearch,
  ]);

  const cancelJobtype = useCallback(() => {
    restoreModalSessionSnapshot();
    closeAllModals();
  }, [closeAllModals, restoreModalSessionSnapshot]);

  const cancelJobtypeGroup = useCallback(() => {
    restoreModalSessionSnapshot();
    setSubModalType(null);
  }, [restoreModalSessionSnapshot]);

  // 年収入力欄の変更（数値のみ、上限まで）
  const setSalaryDraftValue = useCallback((value: string) => {
    const normalized = value.replace(/\D/g, "");
    const parsed = Number(normalized || "0");
    setSalaryDraft(Math.min(MAX_SALARY, parsed));
  }, []);

  // 年収ドラフトを増減
  const adjustSalaryDraft = useCallback((delta: number) => {
    setSalaryDraft((current) =>
      Math.max(MIN_SALARY, Math.min(MAX_SALARY, current + delta)),
    );
  }, []);

  // 年収が有効範囲内か
  const isSalaryValid = useMemo(
    () => salaryDraft >= MIN_SALARY && salaryDraft <= MAX_SALARY,
    [salaryDraft],
  );
  const canApplyLocation = useMemo(
    () =>
      Boolean(draftResidencePrefectureName && draftResidenceCityName) ||
      draftPrimaryLocations.length > 0 ||
      draftOtherLocations.length > 0,
    [
      draftOtherLocations.length,
      draftPrimaryLocations.length,
      draftResidenceCityName,
      draftResidencePrefectureName,
    ],
  );
  const canSearchWithCurrentFilters = useMemo(() => {
    const hasSelectedJobtype =
      (filterModalOpen
        ? committedJobtypeOptions
        : effectiveJobtypeOptions
      ).filter((option) => option.Selected).length > 0;
    const hasSalary = filterModalOpen
      ? isSalaryValid
      : positionSearch.salary >= MIN_SALARY &&
        positionSearch.salary <= MAX_SALARY;
    const effectiveSelectedLocationCount = filterModalOpen
      ? draftPrimaryLocations.length + draftOtherLocations.length
      : selectedPrimaryLocationValues.length +
        selectedOtherLocationValues.length;
    const hasResidenceLocation = filterModalOpen
      ? Boolean(draftResidencePrefectureName && draftResidenceCityName)
      : Boolean(
          positionSearch.residencePrefectureName &&
          positionSearch.residenceCityName,
        );
    const hasSelectedLocation =
      hasResidenceLocation || effectiveSelectedLocationCount > 0;

    return hasSelectedJobtype && hasSalary && hasSelectedLocation;
  }, [
    draftOtherLocations.length,
    draftPrimaryLocations.length,
    committedJobtypeOptions,
    effectiveJobtypeOptions,
    filterModalOpen,
    isSalaryValid,
    positionSearch.salary,
    positionSearch.residenceCityName,
    positionSearch.residencePrefectureName,
    selectedOtherLocationValues.length,
    selectedPrimaryLocationValues.length,
    draftResidenceCityName,
    draftResidencePrefectureName,
  ]);

  // 年収を確定更新
  const applySalary = useCallback(async () => {
    if (!isSalaryValid) {
      return;
    }
    const searchOverrides = commitModalSessionDrafts();
    clearModalSessionSnapshot();
    await runJobtypeSpecificSearch(searchOverrides);
    closeAllModals();
  }, [
    clearModalSessionSnapshot,
    commitModalSessionDrafts,
    isSalaryValid,
    closeAllModals,
    runJobtypeSpecificSearch,
  ]);

  // 年収変更をキャンセル
  const cancelSalary = useCallback(() => {
    restoreModalSessionSnapshot();
    closeAllModals();
  }, [closeAllModals, restoreModalSessionSnapshot]);

  const applyKeyword = useCallback(async () => {
    const searchOverrides = commitModalSessionDrafts();
    clearModalSessionSnapshot();
    await runJobtypeSpecificSearch(searchOverrides);
    closeAllModals();
  }, [
    clearModalSessionSnapshot,
    commitModalSessionDrafts,
    closeAllModals,
    runJobtypeSpecificSearch,
  ]);

  const cancelKeyword = useCallback(() => {
    restoreModalSessionSnapshot();
    closeAllModals();
  }, [closeAllModals, restoreModalSessionSnapshot]);

  // 通勤可能エリアのドラフト選択切り替え
  const toggleDraftPrimaryLocation = useCallback((value: string) => {
    setDraftPrimaryLocations((current) =>
      current.includes(value)
        ? current.filter((item) => item !== value)
        : [...current, value],
    );
  }, []);

  // その他勤務地のドラフト選択切り替え
  const toggleDraftOtherLocation = useCallback((value: string) => {
    setDraftOtherLocations((current) =>
      current.includes(value)
        ? current.filter((item) => item !== value)
        : [...current, value],
    );
  }, []);

  // その他勤務地の次候補をドラフトへ追加
  const addOtherLocation = useCallback(() => {
    setAddressSelectionMode("other-location");
    setAddressSelectionModalOpen(true);
  }, []);

  // リモート可能のドラフト選択切り替え
  const toggleDraftRemoteWorkPossible = useCallback(() => {
    setDraftRemoteWorkPossible((current) => !current);
  }, []);

  // 住所検索モーダルで選んだ勤務地をドラフトに追加
  const selectOtherLocationAddress = useCallback((address: Address) => {
    const newOption: LocationPositionSearchFilterOption = {
      ...toLocationOptionFromAddress(address),
      Selected: true,
    };

    setDraftOtherLocationOptions((current) => {
      if (current.some((option) => option.Value === newOption.Value)) {
        return current;
      }
      return [...current, newOption];
    });
    setDraftOtherLocations((current) =>
      current.includes(newOption.Value)
        ? current
        : [...current, newOption.Value],
    );
    setAddressSelectionMode(null);
    setAddressSelectionModalOpen(false);
  }, []);

  // 居住地検索モーダルを開く
  const openResidenceAddressSelection = useCallback(() => {
    setAddressSelectionMode("residence");
    setAddressSelectionModalOpen(true);
  }, []);

  // 住所検索モーダルで選んだ居住地から通勤可能エリアを取得して反映
  const selectResidenceAddress = useCallback(async (address: Address) => {
    const residence = `${address.prefecture.Name}${address.city.Name}`;
    const commutingAreaAddresses = await searchCommutingAreas(
      address.prefecture.Name,
      address.city.Name,
    );

    setDraftResidence(residence);
    setDraftResidencePrefectureName(address.prefecture.Name);
    setDraftResidenceCityName(address.city.Name);
    hydratedResidenceKeyRef.current = residenceKey(
      address.prefecture.Name,
      address.city.Name,
    );
    setDraftPrimaryLocationOptions(
      toCommutingAreaOptions(commutingAreaAddresses),
    );
    setDraftPrimaryLocations([]);
    setAddressSelectionMode(null);
    setAddressSelectionModalOpen(false);
  }, []);

  // 住所検索モーダルの選択イベントをモード別で振り分け
  const selectAddress = useCallback(
    async (address: Address) => {
      if (addressSelectionMode === "residence") {
        await selectResidenceAddress(address);
        return;
      }
      if (addressSelectionMode === "other-location") {
        selectOtherLocationAddress(address);
      }
    },
    [addressSelectionMode, selectOtherLocationAddress, selectResidenceAddress],
  );

  // 詳細条件ドラフトの選択切り替え
  const toggleDraftDetail = useCallback(
    (key: string, optionValue: string) => {
      const filterType =
        detailGroups.find((group) => group.key === key)?.type ??
        PositionSearchFilterType.Multiple;

      setDraftDetailGroups((current) => {
        const values = current[key] ?? [];
        if (filterType === PositionSearchFilterType.Single) {
          return {
            ...current,
            [key]: values.includes(optionValue) ? [] : [optionValue],
          };
        }
        return {
          ...current,
          [key]: values.includes(optionValue)
            ? values.filter((item) => item !== optionValue)
            : [...values, optionValue],
        };
      });
    },
    [detailGroups],
  );

  // 子画面（通勤可能エリア/その他勤務地）からの「設定する」は親の「勤務地」画面へ戻す。
  // 親画面の「この条件で検索する」は他タブと同様に検索まで実行する。
  const applyLocation = useCallback(async () => {
    if (
      subModalType?.type === "location-primary" ||
      subModalType?.type === "location-other"
    ) {
      setSubModalType(null);
      return;
    }

    const searchOverrides = commitModalSessionDrafts();
    clearModalSessionSnapshot();
    await runJobtypeSpecificSearch(searchOverrides);

    closeAllModals();
  }, [
    closeAllModals,
    clearModalSessionSnapshot,
    commitModalSessionDrafts,
    runJobtypeSpecificSearch,
    subModalType,
    setSubModalType,
  ]);

  // 通勤可能エリア子画面を閉じて勤務地画面へ戻る（ドラフトは保持）
  const cancelPrimaryLocationSubModal = useCallback(() => {
    setAddressSelectionMode(null);
    setAddressSelectionModalOpen(false);
    setSubModalType(null);
  }, [setSubModalType]);

  // その他勤務地子画面を閉じて勤務地画面へ戻る（ドラフトは保持）
  const cancelOtherLocationSubModal = useCallback(() => {
    setAddressSelectionMode(null);
    setAddressSelectionModalOpen(false);
    setSubModalType(null);
  }, [setSubModalType]);

  // 勤務地変更をキャンセル
  const cancelLocation = useCallback(() => {
    restoreModalSessionSnapshot();
    closeAllModals();
  }, [closeAllModals, restoreModalSessionSnapshot]);

  // 詳細条件ドラフトを Redux に反映
  const applyDetail = useCallback(async () => {
    const searchOverrides = commitModalSessionDrafts();
    clearModalSessionSnapshot();
    await runJobtypeSpecificSearch(searchOverrides);

    closeAllModals();
  }, [
    clearModalSessionSnapshot,
    closeAllModals,
    commitModalSessionDrafts,
    runJobtypeSpecificSearch,
  ]);

  // 詳細条件変更をキャンセル
  const cancelDetail = useCallback(() => {
    restoreModalSessionSnapshot();
    closeAllModals();
  }, [closeAllModals, restoreModalSessionSnapshot]);

  // チップ表示用の選択件数
  const selectedLocationCount = useMemo(
    () =>
      filterModalOpen
        ? draftPrimaryLocations.length + draftOtherLocations.length
        : selectedPrimaryLocationValues.length +
          selectedOtherLocationValues.length,
    [
      draftOtherLocations.length,
      draftPrimaryLocations.length,
      filterModalOpen,
      selectedOtherLocationValues.length,
      selectedPrimaryLocationValues.length,
    ],
  );

  // チップ表示用の詳細条件選択件数
  const selectedDetailCount = useMemo(() => {
    const detailSelections = filterModalOpen
      ? draftDetailGroups
      : committedDetailGroups;
    const detailSelectionValues: string[][] = Object.values(detailSelections);
    return detailSelectionValues.reduce(
      (count, options) => count + options.length,
      0,
    );
  }, [committedDetailGroups, draftDetailGroups, filterModalOpen]);

  const selectedKeywordCount = useMemo(
    () =>
      countKeywordLines(
        filterModalOpen ? keywordDraft : positionSearch.positionKeyword,
      ),
    [filterModalOpen, keywordDraft, positionSearch.positionKeyword],
  );
  const selectedSalaryCount = useMemo(
    () => ((filterModalOpen ? salaryDraft : positionSearch.salary) > 0 ? 1 : 0),
    [filterModalOpen, positionSearch.salary, salaryDraft],
  );

  const showDetailChip = useMemo(
    () => detailGroups.length > 0,
    [detailGroups.length],
  );

  const totalVisibleTabCount = useMemo(
    () =>
      selectedJobtypeValues.length +
      selectedSalaryCount +
      selectedKeywordCount +
      selectedLocationCount +
      (showDetailChip ? selectedDetailCount : 0),
    [
      selectedDetailCount,
      selectedJobtypeValues.length,
      selectedSalaryCount,
      selectedKeywordCount,
      selectedLocationCount,
      showDetailChip,
    ],
  );

  const jobtypeGroups = useMemo(
    () =>
      Object.entries(effectiveJobtypeGroups).map(([toolName, options]) => ({
        toolName,
        label: jobtypeGroupLabel(toolName),
        selected: toolName === effectiveActiveToolName,
        selectedCount: options.filter((option) => option.Selected).length,
        options: options.map(toJobtypeViewOption),
      })),
    [effectiveActiveToolName, effectiveJobtypeGroups],
  );

  const hasMultipleJobtypeGroups = jobtypeGroups.length > 1;

  // 職種選択肢を UI 用へ整形
  const jobtypeOptions = useMemo(
    () => effectiveJobtypeOptions.map(toJobtypeViewOption),
    [effectiveJobtypeOptions],
  );

  return {
    filterModalOpen,
    filterModalType,
    subModalType,
    selectedJobtype,
    selectedJobtypeValues,
    selectedSalary: salaryLabel,
    salaryValue: positionSearch.salary > 0 ? String(positionSearch.salary) : "",
    keywordDraft,
    salaryDraft,
    isSalaryValid,
    canApplyLocation,
    canSearchWithCurrentFilters,
    jobtypeOptions,
    jobtypeGroups,
    hasMultipleJobtypeGroups,
    primaryLocationTitle,
    primaryLocationOptions,
    otherLocationOptions,
    detailGroups,
    draftPrimaryLocations,
    draftOtherLocations,
    draftOtherLocationOptions,
    draftRemoteWorkPossible,
    draftDetailGroups,
    addressSelectionModalOpen,
    jobtypeHelpOpen,
    jobtypeHelpTarget,
    jobtypeHelpDescription,
    selectedLocationCount,
    selectedDetailCount,
    selectedKeywordCount,
    selectedSalaryCount,
    showDetailChip,
    totalVisibleTabCount,
    setSubModalType,
    setJobtypeHelpOpen,
    addressSelectionMode,
    openFilter,
    closeAllModals,
    openJobtypeHelp,
    selectOtherJobtype,
    selectJobtype,
    applyJobtype,
    cancelJobtype,
    cancelJobtypeGroup,
    confirmGroupSwitch,
    cancelGroupSwitch,
    groupSwitchConfirmPending,
    setKeywordDraft,
    setSalaryDraftValue,
    adjustSalaryDraft,
    applySalary,
    cancelSalary,
    applyKeyword,
    cancelKeyword,
    toggleDraftPrimaryLocation,
    toggleDraftOtherLocation,
    toggleDraftRemoteWorkPossible,
    addOtherLocation,
    openResidenceAddressSelection,
    setAddressSelectionModalOpen,
    selectAddress,
    toggleDraftDetail,
    applyLocation,
    cancelLocation,
    cancelPrimaryLocationSubModal,
    cancelOtherLocationSubModal,
    applyDetail,
    cancelDetail,
    remoteWorkPossible: positionSearch.remoteWorkPossible,
  };
}

export type UseJobSearchFilterDialogState = ReturnType<
  typeof useJobSearchFilterDialogState
>;
