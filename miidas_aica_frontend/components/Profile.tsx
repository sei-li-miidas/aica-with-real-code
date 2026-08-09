"use client";

import "./Profile.scss";
import {
  Card,
  CardContent,
  Typography,
  Box,
  CardActions,
  Button,
  Chip,
} from "@mui/material";
import WarningIcon from "@mui/icons-material/Warning";
import CheckIcon from "@mui/icons-material/Check";
import { useRouter } from "next/navigation";
import {
  useAppDispatch,
  useAppSelector,
  selectPositionSearchReady,
} from "@/lib/store/hooks";
import { useCallback, useEffect, useMemo } from "react";
import { getJobSearchFilter, getSavedUserProfile } from "@/utils/fetch";
import {
  updateBasicInfo,
  updateCareer,
  updateEducation,
  markSavedProfileRetrieved,
  updateWill,
  updateAppliedPositions,
} from "@/lib/store/features/profile/profileSlice";
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
import { PagePath } from "@/constants/enum";
import {
  basicInfoCompleted,
  careerCompleted,
  educationCompleted,
  hasApplyErrors,
  willCompleted,
} from "@/utils/profileUtils";
import { formatResidenceAddress } from "@/lib/common";

export interface FieldError {
  Page: string;
  Field: string;
  Value: string;
  Message?: string;
}

export default function Profile() {
  const router = useRouter();

  const profileState = useAppSelector((state) => state.profile);
  const { savedProfileRetrieved, basicInfo, education, career, will } =
    profileState;
  const positionSearchReady = useAppSelector(selectPositionSearchReady);

  const profileCompletionStatus = useMemo(() => {
    return {
      basicInfoCompleted: basicInfoCompleted(basicInfo),
      educationCompleted: educationCompleted(education),
      careerCompleted: careerCompleted(career),
      willCompleted: willCompleted(will),
    };
  }, [basicInfo, education, career, will]);

  const profiles = useMemo(
    () => [
      {
        title: "基本情報",
        description: "氏名、メールアドレス、パスワードなど",
        completed: profileCompletionStatus.basicInfoCompleted,
        hasApplyErrors: hasApplyErrors(basicInfo),
        detailPath: PagePath.ProfileBasicInfo,
      },
      {
        title: "学歴・スキル",
        description: "最終学歴、英会話スキルなど",
        completed: profileCompletionStatus.educationCompleted,
        hasApplyErrors: hasApplyErrors(education),
        detailPath: PagePath.ProfileEducation,
      },
      {
        title: "職歴",
        description: "経験した企業、経験した仕事内容など",
        completed: profileCompletionStatus.careerCompleted,
        hasApplyErrors: hasApplyErrors(career),
        detailPath: PagePath.ProfileCarrer,
      },
      {
        title: "希望条件",
        description: "希望する年収、勤務地、仕事内容など",
        completed: profileCompletionStatus.willCompleted,
        hasApplyErrors: hasApplyErrors(will),
        detailPath: PagePath.ProfileWill,
      },
    ],
    [profileCompletionStatus, basicInfo, education, career, will],
  );

  const dispatch = useAppDispatch();

  // 後処理しやすいため、ここのリクエスト処理後、画面表示する。
  // じゃないと、ここでの処理はunmountなどのため中断されること考慮したら、いくつの画面では同じことやらないといけない
  useEffect(() => {
    const abortController = new AbortController();

    // 保存済みのプロフィール取得
    getSavedUserProfile({ signal: abortController.signal })
      .then((profile) => {
        profile = profile || {};

        if ("PositionIDs" in profile) {
          dispatch(updateAppliedPositions(profile.PositionIDs));
        }

        const basicInfoSaved = "basic_profile" in profile;
        const preferencesSaved = "preferences_profile" in profile;

        if (basicInfoSaved) {
          // 基本情報
          dispatch(updateBasicInfo(profile.basic_profile));
        }

        if ("education_profile" in profile) {
          // 学歴
          dispatch(updateEducation(profile.education_profile));
        }

        if ("experience_profile" in profile) {
          // 職歴
          dispatch(updateCareer(profile.experience_profile));
        }

        if (preferencesSaved) {
          // 希望条件
          dispatch(updateWill(profile.preferences_profile));
        }

        if ((!basicInfoSaved || !preferencesSaved) && !positionSearchReady) {
          // 基本情報と希望条件にポジション検索条件を初期値として利用するので、
          // 基本情報未保存 || 希望条件未保存の場合、取得
          getJobSearchFilter({ signal: abortController.signal })
            .then((data) => {
              if (!data?.SearchFilters) {
                dispatch(setReady(false));
                return;
              }

              const filters = data.SearchFilters;
              const sameFilterJobtypes = data.JobtypeNamesWithSameSearchFilters;
              dispatch(
                setActiveToolName(
                  typeof data.ToolName === "string" ? data.ToolName : "",
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
                    residenceCityName:
                      filters.Locations.Residence.Address?.CityName,
                    commutingAreas:
                      filters.Locations.Residence.CommutingAreas ?? [],
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

              if (
                filters.OtherFilters &&
                typeof filters.OtherFilters === "object"
              ) {
                dispatch(setOtherFilters(filters.OtherFilters));
              } else {
                dispatch(clearOtherFilters());
              }

              if (
                filters.SelectedFilterOptions &&
                typeof filters.SelectedFilterOptions === "object"
              ) {
                dispatch(
                  setSelectedFilterOptions(filters.SelectedFilterOptions),
                );
              } else {
                dispatch(clearSelectedFilterOptions());
              }

              if (
                sameFilterJobtypes &&
                typeof sameFilterJobtypes === "object"
              ) {
                dispatch(setSameOtherFilterJobtypes(sameFilterJobtypes));
              } else {
                dispatch(setSameOtherFilterJobtypes({}));
              }

              const hasJobtypes =
                !!filters.Jobtypes && Object.keys(filters.Jobtypes).length > 0;
              const hasLocation =
                !!filters.Locations?.Residence ||
                (Array.isArray(filters.Locations?.WorkLocations) &&
                  filters.Locations.WorkLocations.length > 0);
              const hasSalary = Number(filters.Salary) > 0;
              dispatch(setReady(hasJobtypes && hasLocation && hasSalary));
            })
            .catch((error) => {
              dispatch(setReady(false));
              console.error("ポジション検索条件の取得に失敗しました", error);
            });
        }

        dispatch(markSavedProfileRetrieved());
      })
      .catch((error) =>
        console.error("プロフィールの取得に失敗しました", error),
      );

    return () => {
      abortController.abort();
    };
  }, [dispatch, positionSearchReady]);

  const profileEditClicked = useCallback(
    (path: PagePath) => {
      router.push(path);
    },
    [router],
  );

  return savedProfileRetrieved ? (
    <Box className="profile-list">
      {profiles.map((profile, index) => (
        <Card key={index} className="profile-card">
          {profile.completed && (
            <Chip
              icon={<CheckIcon color="success" />}
              label="入力済み"
              size="small"
              variant="outlined"
              className="profile-chip is-complete"
            />
          )}
          {!profile.completed && (
            <Chip
              icon={<WarningIcon color="error" />}
              label={profile.hasApplyErrors ? "修正が必要です" : "未入力"}
              size="small"
              variant="outlined"
              className="profile-chip is-incomplete"
            />
          )}
          <CardContent>
            <Typography variant="h6" component="h2" gutterBottom>
              {profile.title}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {profile.description}
            </Typography>
          </CardContent>
          <CardActions className="profile-card-actions">
            <Button
              size="medium"
              onClick={() => profileEditClicked(profile.detailPath)}
            >
              詳細を見る
            </Button>
          </CardActions>
        </Card>
      ))}
    </Box>
  ) : (
    <Box className="profile-loading">
      <Typography variant="h6" color="text.secondary">
        プロフィール情報を読み込み中...
      </Typography>
    </Box>
  );
}
