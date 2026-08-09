"use client";

import { useEffect, useRef } from "react";
import { PageName } from "@/constants/enum";
import { getJobSearchFilter } from "@/utils/fetch";
import { useAppDispatch, useAppSelector } from "@/lib/store/hooks";
import { formatResidenceAddress } from "@/lib/common";
import {
  clearOtherFilters,
  clearPositionKeyword,
  clearRemoteWorkPossible,
  clearResidence,
  clearSelectedFilterOptions,
  clearWorkLocations,
  setActiveToolName,
  setJobtypes,
  setOtherFilters,
  setPositionKeyword,
  setReady,
  setRemoteWorkPossible,
  setResidence,
  setSalary,
  setSameOtherFilterJobtypes,
  setSelectedFilterOptions,
  setWorkLocations,
} from "@/lib/store/features/position_search/positionSearchSlice";

type Params = {
  currentPage: string;
  isConnected: boolean;
};

export function usePositionSearchFilterInitialization({
  currentPage,
  isConnected,
}: Params) {
  const dispatch = useAppDispatch();
  const sessionID = useAppSelector((state) => state.websocket.sessionID);
  const initializedRef = useRef(false);

  useEffect(() => {
    if (
      currentPage !== PageName.Chat ||
      !isConnected ||
      !sessionID.trim() ||
      initializedRef.current
    ) {
      return;
    }

    // コンポーネントのアンマウントやエフェクトの再実行時に、
    // 進行中の非同期処理の結果を破棄するためのフラグ。
    // クリーンアップ関数で false にセットされる。
    let active = true;

    const initializePositionSearchFilters = async () => {
      const result = await getJobSearchFilter();

      // active が false の場合、エフェクトがクリーンアップ済み（アンマウントまたは再実行）のため、
      // 古いレスポンスによる状態更新を防ぐ。
      if (!active) {
        return;
      }

      if (!result) {
        dispatch(setReady(false));
        return;
      }

      const source = result;
      const filters = source.SearchFilters;
      const sameFilterJobtypes =
        source.JobtypeNamesWithSameSearchFilters &&
        typeof source.JobtypeNamesWithSameSearchFilters === "object"
          ? source.JobtypeNamesWithSameSearchFilters
          : {};

      if (!filters) {
        dispatch(setReady(false));
        return;
      }

      initializedRef.current = true;
      dispatch(
        setActiveToolName(
          typeof source.ToolName === "string" ? source.ToolName : "",
        ),
      );
      dispatch(setJobtypes(filters.Jobtypes ?? {}));
      dispatch(setSalary(Number(filters.Salary) || 0));
      if (
        typeof filters.PositionKeyword === "string" &&
        filters.PositionKeyword.trim()
      ) {
        dispatch(setPositionKeyword(filters.PositionKeyword));
      } else {
        dispatch(clearPositionKeyword());
      }

      if (filters.Locations?.Residence) {
        dispatch(
          setResidence({
            residence: formatResidenceAddress(
              filters.Locations.Residence.Address,
            ),
            residencePrefectureName:
              filters.Locations.Residence.Address?.PrefectureName,
            residenceCityName: filters.Locations.Residence.Address?.CityName,
            commutingAreas: filters.Locations.Residence.CommutingAreas ?? [],
          }),
        );
      } else {
        dispatch(clearResidence());
      }

      if (Array.isArray(filters.Locations?.WorkLocations)) {
        dispatch(setWorkLocations(filters.Locations.WorkLocations));
      } else {
        dispatch(clearWorkLocations());
      }

      const remoteWorkPossible = filters.Locations?.RemoteWorkPossible;
      if (typeof remoteWorkPossible === "boolean") {
        dispatch(setRemoteWorkPossible(remoteWorkPossible));
      } else {
        dispatch(clearRemoteWorkPossible());
      }

      if (filters.OtherFilters && typeof filters.OtherFilters === "object") {
        dispatch(setOtherFilters(filters.OtherFilters));
      } else {
        dispatch(clearOtherFilters());
      }

      if (
        filters.SelectedFilterOptions &&
        typeof filters.SelectedFilterOptions === "object"
      ) {
        dispatch(setSelectedFilterOptions(filters.SelectedFilterOptions));
      } else {
        dispatch(clearSelectedFilterOptions());
      }

      dispatch(setSameOtherFilterJobtypes(sameFilterJobtypes));

      // 職種・勤務地・希望年収のすべてに値がある場合、一度検索が実行されたので
      const hasJobtypes =
        !!filters.Jobtypes && Object.keys(filters.Jobtypes).length > 0;
      const hasLocation =
        !!filters.Locations?.Residence ||
        (Array.isArray(filters.Locations?.WorkLocations) &&
          filters.Locations.WorkLocations.length > 0);
      const hasSalary = Number(filters.Salary) > 0;

      dispatch(setReady(hasJobtypes && hasLocation && hasSalary));
    };

    initializePositionSearchFilters();

    return () => {
      // エフェクトのクリーンアップ時にフラグを無効化し、
      // 非同期処理が完了しても状態を更新しないようにする。
      active = false;
    };
  }, [currentPage, dispatch, isConnected, sessionID]);
}
