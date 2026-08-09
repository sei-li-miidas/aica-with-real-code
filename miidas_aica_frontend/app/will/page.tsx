"use client";

import "./page.scss";
import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useForm, Controller } from "react-hook-form";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import FormControl from "@mui/material/FormControl";
import Switch from "@mui/material/Switch";
import IconButton from "@mui/material/IconButton";

import Grid from "@mui/material/Grid2";
import { useAppDispatch, useAppSelector } from "@/lib/store/hooks";
import {
  updateWill,
  Will,
  updateBasicInfoAddress,
} from "@/lib/store/features/profile/profileSlice";

import {
  fetchApiData,
  searchByPrefectureCityNames,
  searchCommutingAreas,
  searchJobtypeByName,
} from "@/utils/fetch";
import { Address, MasterType } from "@/types/utility-types";
import AddressSelectionModal from "@/components/AddressSelectionModal";
import JobTypeSelectionModal from "@/components/JobTypeSelectionModal";
import {
  MAX_WILL_JOBTYPES_SMALLS_COUNT,
  MAX_WILL_WORK_ADDRESSES_CITIES_COUNT,
  MAX_WILL_WORK_ADDRESSES_PREFECTURES_COUNT,
  WILL_JOBTYPES_SMALLS_SCROLL_THRESHOLD,
  WILL_WORK_ADDRESSES_CITIES_SCROLL_THRESHOLD,
  JOB_CHANGE_PERIOD_OPTIONS,
} from "@/constants/profile";
import { PagePath, ScrollEventType } from "@/constants/enum";
import { hasNoAPIValidationError } from "@/utils/profileUtils";
import { updateScrollEventType } from "@/lib/store/features/websocket/websocketSlice";

enum AddressSearchTarget {
  Residence,
  CommutingArea,
}

export default function WillPage() {
  const router = useRouter();

  const dispatch = useAppDispatch();
  const positionSearch = useAppSelector((state) => state.positionSearch);
  const basicInfo = useAppSelector((state) => state.profile.basicInfo);
  const will = useAppSelector((state) => state.profile.will);

  const [residence, setResidence] = useState(
    `${basicInfo.prefecture.Name}${basicInfo.city.Name}`,
  );
  const [showAddressModal, setShowAddressModal] = useState(false);
  const [addressSearchTarget, setAddressSearchTarget] = useState(
    AddressSearchTarget.CommutingArea,
  );
  const [showJobTypeModal, setShowJobTypeModal] = useState(false);

  const abortController = useRef<AbortController | null>(null);

  // React Hook Form の設定
  const {
    control,
    handleSubmit,
    watch,
    getValues,
    setValue,
    trigger,
    formState: { errors },
  } = useForm<Will>({
    defaultValues: will,
    mode: "onBlur", // フォーカスが外れたときに検証
  });

  useEffect(() => {
    if (will.applyErrors?.length > 0) {
      trigger();
    }
  }, [will.applyErrors, trigger]);

  // フォーム送信時の処理
  const onSubmit = async (data: Will) => {
    console.debug("保存されたデータ:", data);

    try {
      const result = await fetchApiData(
        "profile/preferences",
        "希望条件の保存に失敗しました",
        {
          method: "POST",
          data: data,
        },
      );

      if (result.error) {
        console.error("希望条件の保存に失敗しました:", result.error);
        // TODO: エラーハンドリング - ユーザーにエラーメッセージを表示
      } else {
        console.debug("希望条件の保存に成功しました:", result.data);

        dispatch(updateWill(data));
        close();
      }
    } catch (error) {
      console.error("希望条件の保存に失敗しました", error);
      // TODO: エラーハンドリング - ユーザーにエラーメッセージを表示
    }
  };

  const addCommutingArea = useCallback(
    (addresses: Address | Address[]) => {
      const addressArray = Array.isArray(addresses) ? addresses : [addresses];
      const currentAddresses = getValues("willWorkAddresses") ?? [];

      // Unique都道府県抽出
      const validAddresses: Address[] = [];
      const currentCityIds = new Set(
        currentAddresses.map((addr) => addr.city.ID),
      );
      const currentUniquePrefectureIds = new Set(
        currentAddresses.map((area) => area.prefecture.ID),
      );

      for (const newAddr of addressArray) {
        // 重複スキップ
        if (currentCityIds.has(newAddr.city.ID)) continue;

        // 都道府県上限チェック
        const wouldExceedPrefectureLimit =
          !currentUniquePrefectureIds.has(newAddr.prefecture.ID) &&
          currentUniquePrefectureIds.size >=
            MAX_WILL_WORK_ADDRESSES_PREFECTURES_COUNT;

        if (wouldExceedPrefectureLimit) {
          continue;
        }

        validAddresses.push(newAddr);
        currentCityIds.add(newAddr.city.ID);
        currentUniquePrefectureIds.add(newAddr.prefecture.ID);
      }

      if (validAddresses.length > 0) {
        const updatedAddresses = [...validAddresses, ...currentAddresses].slice(
          0,
          MAX_WILL_WORK_ADDRESSES_CITIES_COUNT,
        );

        setValue("willWorkAddresses", updatedAddresses);
      }

      trigger("willWorkAddresses");
    },
    [setValue, getValues, trigger],
  );

  const searchPossibleCommutingAreas = useCallback(
    async (prefectureName: string, cityName: string) => {
      const result = await searchCommutingAreas(prefectureName, cityName, {
        signal: abortController.current?.signal,
      });

      if (result) {
        const uniqueResult = result.filter(
          (item, index, self) =>
            index === self.findIndex((t) => t.city.ID === item.city.ID),
        );

        if (uniqueResult.length > 0) {
          addCommutingArea(uniqueResult);
        }
      }
    },
    [addCommutingArea],
  );

  const removeCommutingAreas = (index: number) => {
    setValue(
      "willWorkAddresses",
      getValues("willWorkAddresses").filter((_, i) => i !== index),
    );
    trigger("willWorkAddresses");
  };

  const addJobTypesSmall = useCallback(
    (jobTypes: MasterType | MasterType[]) => {
      const jobTypeArray = Array.isArray(jobTypes) ? jobTypes : [jobTypes];
      const currentJobTypes = getValues("willJobTypes") ?? [];

      // Unique職種抽出（重複はスキップ）
      const validJobTypes: MasterType[] = [];
      const currentJobTypeIds = new Set(currentJobTypes.map((job) => job.ID));

      for (const newJob of jobTypeArray) {
        // 重複スキップ
        if (currentJobTypeIds.has(newJob.ID)) continue;
        validJobTypes.push(newJob);
        currentJobTypeIds.add(newJob.ID);
      }

      if (validJobTypes.length > 0) {
        const updatedJobTypes = [...validJobTypes, ...currentJobTypes].slice(
          0,
          MAX_WILL_JOBTYPES_SMALLS_COUNT,
        );
        setValue("willJobTypes", updatedJobTypes);
      }

      trigger("willJobTypes");
    },
    [setValue, getValues, trigger],
  );

  const removeJobType = (index: number) => {
    setValue(
      "willJobTypes",
      getValues("willJobTypes").filter((_, i) => i !== index),
    );
    trigger("willJobTypes");
  };

  const openAddressModal = (addressSearchTarget: AddressSearchTarget) => {
    setAddressSearchTarget(addressSearchTarget);
    setShowAddressModal(true);
  };

  const setResidenceAndSearchCommutingAreas = useCallback(
    (address: Address) => {
      setResidence(`${address.prefecture.Name}${address.city.Name}`);

      dispatch(
        updateBasicInfoAddress({
          prefecture: {
            ID: address.prefecture.ID,
            Name: address.prefecture.Name,
          },
          city: {
            ID: address.city.ID,
            Name: address.city.Name,
          },
        }),
      );

      searchPossibleCommutingAreas(address.prefecture.Name, address.city.Name);
    },
    [dispatch, searchPossibleCommutingAreas],
  );

  const addressSelected = useCallback(
    (address: Address) => {
      if (addressSearchTarget === AddressSearchTarget.Residence) {
        setResidenceAndSearchCommutingAreas(address);
      } else {
        addCommutingArea(address);
      }

      setShowAddressModal(false);
    },
    [
      setResidenceAndSearchCommutingAreas,
      addressSearchTarget,
      addCommutingArea,
    ],
  );

  const close = () => {
    router.push(PagePath.Chat);
    dispatch(updateScrollEventType(ScrollEventType.ProfileSaved));
  };

  const selectedCommutingAreas = useMemo(
    () =>
      positionSearch.commutingAreas?.filter((location) => location.Selected) ??
      [],
    [positionSearch.commutingAreas],
  );

  const selectedWorkLocations = useMemo(
    () => positionSearch.workLocations.filter((location) => location.Selected),
    [positionSearch.workLocations],
  );

  const selectedJobtypeNames = useMemo(
    () =>
      positionSearch.jobtypes.Options.filter(
        (jobtypeOption) => jobtypeOption.Selected,
      )
        .map((jobtypeOption) => jobtypeOption.Label)
        .filter((name) => name.length > 0),
    [positionSearch.jobtypes.Options],
  );

  useEffect(() => {
    // ユーザー会話から収集してきたデータを取得し、初期値として利用する。
    const willIncome = getValues("willIncome");
    if (!willIncome || parseInt(willIncome, 10) <= 0) {
      if (positionSearch.salary > 0) {
        setValue("willIncome", positionSearch.salary.toString());
      }
    }

    abortController.current = new AbortController();
    const signal = abortController.current.signal;

    // 通える場所willWorkAddressesCitiesに入力がある場合、
    // ユーザーが希望条件画面で手動で通える場所をいじらないと、変わらないです。
    // なので、仮にユーザー会話から取得できた居住地が間違ってユーザーが基本情報のお住まいを変更した場合、
    // ユーザー会話から取得できた居住地より検索できた通える場所はそのまま残る
    if ((getValues("willWorkAddresses")?.length ?? 0) === 0) {
      // 通える場所willWorkAddressesCitiesまだない場合のみ
      const selectedLocations = [
        ...selectedCommutingAreas,
        ...selectedWorkLocations,
      ];
      if (selectedLocations.length > 0) {
        searchByPrefectureCityNames(
          selectedLocations.map((location) => ({
            prefectureName: location.PrefectureName,
            cityName: location.CityName,
          })),
          {
            signal,
          },
        ).then((addresses) => {
          if (addresses.length > 0) {
            addCommutingArea(addresses);
          }
        });
      }
    }

    // 職種willJobTypesSmallsまだない場合のみ
    if ((getValues("willJobTypes")?.length ?? 0) === 0) {
      // ユーザーが会話中に選択した職種のみを抽出する。
      // Selected でフィルタしないと、バックエンドから返ってきた候補職種が
      // すべて希望条件に反映されてしまい、ユーザーの意図と異なる初期値になる。
      if (selectedJobtypeNames.length > 0) {
        searchJobtypeByName(selectedJobtypeNames, { signal }).then(
          (jobTypes) => {
            if (jobTypes.length > 0) {
              addJobTypesSmall(jobTypes);
            }
          },
        );
      }
    }

    return () => {
      // ページクローズ時にリクエストを廃止します。
      abortController.current?.abort();
    };
  }, [
    positionSearch.salary,
    selectedCommutingAreas,
    selectedWorkLocations,
    selectedJobtypeNames,
    getValues,
    setValue,
    addJobTypesSmall,
    addCommutingArea,
  ]);

  return (
    <Box className="page-container">
      {/* ヘッダ固定 */}
      <Box className="page-header">
        <Typography variant="h6" className="page-header__title">
          希望条件
        </Typography>
      </Box>

      {/* スクロール可能なエリア */}
      <Box className="page-scroll">
        <Box
          component="form"
          id="will-form"
          onSubmit={handleSubmit(onSubmit)}
          className="page-form"
        >
          <Grid container spacing={3}>
            {/* 希望年収 */}
            <Grid size={12}>
              <Typography variant="body2" gutterBottom>
                検討可能な年収
              </Typography>
              <Box className="inline-center">
                <Typography variant="body2" color="text.secondary">
                  おおよそ
                </Typography>
                <Controller
                  name="willIncome"
                  control={control}
                  rules={{
                    required: "検討可能な年収を入力してください",
                    pattern: {
                      value: /^[0-9]+$/,
                      message: "半角数字のみ入力可能です",
                    },
                    validate: (value) => {
                      const num = parseInt(value);
                      if (num < 100) {
                        return "100万円以上を入力してください";
                      }
                      if (num > 2000) {
                        return "2000万円以下を入力してください";
                      }
                      return hasNoAPIValidationError(
                        will.applyErrors,
                        "willIncome",
                        value,
                        "検討可能な年収",
                      );
                    },
                  }}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      type="number"
                      placeholder="300"
                      variant="outlined"
                      size="small"
                      error={!!errors.willIncome}
                      className="w-100"
                      slotProps={{
                        input: {
                          className: "input-soft",
                        },
                        htmlInput: {
                          className: "text-right",
                          inputMode: "numeric",
                          pattern: "[0-9]*",
                        },
                      }}
                    />
                  )}
                />
                <Typography variant="body2" color="text.secondary">
                  万円以上
                </Typography>
              </Box>
              {errors.willIncome && (
                <Typography
                  variant="caption"
                  className="error-text error-text--no-indent"
                >
                  {errors.willIncome.message}
                </Typography>
              )}
            </Grid>

            {/* 希望勤務地 */}
            <Grid size={12}>
              <Typography variant="body2" gutterBottom>
                検討可能な勤務地
              </Typography>

              <Box>
                {/* 通勤可能エリア入力フィールドとリスト */}
                <Box className="mt-16">
                  {!residence && (
                    <Button
                      onClick={() =>
                        openAddressModal(AddressSearchTarget.Residence)
                      }
                      variant="outlined"
                      className="btn-full"
                    >
                      お住まいの周辺地域を一括設定する
                    </Button>
                  )}
                </Box>
                <Box className="mt-16">
                  {/* 通勤可能エリアリスト */}
                  {residence ||
                  (getValues("willWorkAddresses")?.length ?? 0) > 0 ? (
                    <Controller
                      name="willWorkAddresses"
                      control={control}
                      rules={{
                        validate: (value) => {
                          if ((value?.length ?? 0) === 0) {
                            return "検討可能な勤務地を入力してください";
                          }
                          if (
                            value.length >= MAX_WILL_WORK_ADDRESSES_CITIES_COUNT
                          ) {
                            return `最大${MAX_WILL_WORK_ADDRESSES_CITIES_COUNT}件までしか登録できません。`;
                          }
                          return true;
                        },
                      }}
                      render={({ fieldState: { error } }) => (
                        <TextField
                          fullWidth
                          placeholder={
                            (getValues("willWorkAddresses")?.length ?? 0) >=
                            MAX_WILL_WORK_ADDRESSES_CITIES_COUNT
                              ? `最大${MAX_WILL_WORK_ADDRESSES_CITIES_COUNT}件まで登録可能です`
                              : "検討可能な勤務地を追加"
                          }
                          variant="outlined"
                          size="small"
                          className="mb-2 clickable-input"
                          onClick={() => {
                            if (
                              (getValues("willWorkAddresses")?.length ?? 0) <
                              MAX_WILL_WORK_ADDRESSES_CITIES_COUNT
                            ) {
                              openAddressModal(
                                AddressSearchTarget.CommutingArea,
                              );
                            }
                          }}
                          error={!!error}
                          helperText={error?.message}
                          disabled={
                            (getValues("willWorkAddresses")?.length ?? 0) >=
                            MAX_WILL_WORK_ADDRESSES_CITIES_COUNT
                          }
                          slotProps={{
                            formHelperText: { className: "error-text" },
                            input: {
                              readOnly: true,
                            },
                          }}
                        />
                      )}
                    />
                  ) : (
                    <Button
                      onClick={() =>
                        openAddressModal(AddressSearchTarget.CommutingArea)
                      }
                      variant="outlined"
                      className="btn-full"
                    >
                      検討可能な勤務地を1つずつ設定する
                    </Button>
                  )}

                  {/* 通勤可能エリアリスト */}
                  {watch("willWorkAddresses") &&
                    getValues("willWorkAddresses").length > 0 && (
                      <Box
                        className={`mb-2${getValues("willWorkAddresses").length > WILL_WORK_ADDRESSES_CITIES_SCROLL_THRESHOLD ? " chip-list-scrollable" : ""}`}
                      >
                        {getValues("willWorkAddresses").map((area, index) => (
                          <Box key={index} className="chip chip--lg">
                            <IconButton
                              size="small"
                              onClick={() => removeCommutingAreas(index)}
                              className="chip__remove"
                            >
                              ✕
                            </IconButton>
                            <Typography variant="body2">
                              {area.prefecture.Name}
                              {area.city.Name}
                            </Typography>
                          </Box>
                        ))}
                      </Box>
                    )}
                </Box>
              </Box>
            </Grid>

            {/* 在宅勤務 */}
            <Grid size={12}>
              <Typography variant="body2" gutterBottom>
                在宅勤務
              </Typography>

              <Box className="flex-between mb-2">
                <Typography variant="body2">在宅勤務を希望する</Typography>
                <Controller
                  name="willRemoteWork"
                  control={control}
                  render={({ field }) => (
                    <Switch
                      checked={field.value}
                      onChange={(e) => field.onChange(e.target.checked)}
                      color="primary"
                    />
                  )}
                />
              </Box>
            </Grid>

            {/* 希望職種 */}
            <Grid size={12}>
              <Typography variant="body2" gutterBottom>
                検討可能な仕事内容
              </Typography>

              <Box>
                {/* 職種選択フィールドとリスト */}
                <Box className="mt-16">
                  <Controller
                    name="willJobTypes"
                    control={control}
                    rules={{
                      validate: (value) => {
                        if ((value?.length ?? 0) === 0) {
                          return "検討可能な仕事内容を入力してください";
                        }

                        if (value.length >= MAX_WILL_JOBTYPES_SMALLS_COUNT) {
                          return `最大${MAX_WILL_JOBTYPES_SMALLS_COUNT}件までしか登録できません。`;
                        }

                        return true;
                      },
                    }}
                    render={({ fieldState: { error } }) => (
                      <TextField
                        fullWidth
                        placeholder={
                          (getValues("willJobTypes")?.length ?? 0) >=
                          MAX_WILL_JOBTYPES_SMALLS_COUNT
                            ? `最大${MAX_WILL_JOBTYPES_SMALLS_COUNT}件まで登録可能です`
                            : "検討可能な職種を追加"
                        }
                        variant="outlined"
                        size="small"
                        className="mb-2 clickable-input"
                        onClick={() => {
                          if (
                            (getValues("willJobTypes")?.length ?? 0) <
                            MAX_WILL_JOBTYPES_SMALLS_COUNT
                          ) {
                            setShowJobTypeModal(true);
                          }
                        }}
                        error={!!error}
                        helperText={error?.message}
                        disabled={
                          (getValues("willJobTypes")?.length ?? 0) >=
                          MAX_WILL_JOBTYPES_SMALLS_COUNT
                        }
                        slotProps={{
                          formHelperText: { className: "error-text" },
                          input: {
                            readOnly: true,
                          },
                        }}
                      />
                    )}
                  />

                  {/* 選択された職種リスト */}
                  {(watch("willJobTypes")?.length ?? 0) > 0 && (
                    <Box
                      className={`mb-2${(getValues("willJobTypes")?.length ?? 0) > WILL_JOBTYPES_SMALLS_SCROLL_THRESHOLD ? " chip-list-scrollable" : ""}`}
                    >
                      {getValues("willJobTypes").map((jobType, index) => (
                        <Box key={index} className="chip">
                          <IconButton
                            size="small"
                            onClick={() => removeJobType(index)}
                            className="chip__remove"
                          >
                            ✕
                          </IconButton>
                          <Typography variant="body2">
                            {jobType.Name}
                          </Typography>
                        </Box>
                      ))}
                    </Box>
                  )}
                </Box>
              </Box>
            </Grid>

            {/* 転職を希望する時期 */}
            <Grid size={12}>
              <Typography variant="body2" gutterBottom>
                転職を希望する時期
              </Typography>
              <Controller
                name="willJobChangePeriod"
                control={control}
                rules={{
                  required: "転職希望時期を選択してください",
                }}
                render={({ field }) => (
                  <FormControl
                    fullWidth
                    size="small"
                    error={!!errors.willJobChangePeriod}
                  >
                    <Select {...field} displayEmpty>
                      <MenuItem value="" disabled>
                        選択してください
                      </MenuItem>
                      {JOB_CHANGE_PERIOD_OPTIONS.map((option) => (
                        <MenuItem key={option.ID} value={option.ID}>
                          {option.Name}
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.willJobChangePeriod && (
                      <Typography variant="caption" className="error-text">
                        {errors.willJobChangePeriod.message}
                      </Typography>
                    )}
                  </FormControl>
                )}
              />
            </Grid>

            {/* 求人紹介サービス */}
            <Grid size={12}>
              <Typography variant="body2" gutterBottom>
                求人案内サービス
              </Typography>

              <Box className="flex-between mb-2">
                <Typography variant="body2">
                  あなたにおすすめの求人の案内電話を希望する
                </Typography>
                <Controller
                  name="isRpoAgreement"
                  control={control}
                  render={({ field }) => (
                    <Switch
                      checked={field.value}
                      onChange={(e) => field.onChange(e.target.checked)}
                      color="primary"
                    />
                  )}
                />
              </Box>
            </Grid>
          </Grid>
        </Box>
      </Box>

      {/* フッター */}
      <Box className="page-footer">
        <Button onClick={close} variant="outlined" className="btn-cancel">
          キャンセル
        </Button>
        <Button
          type="submit"
          form="will-form"
          variant="contained"
          color="primary"
          className="btn-submit"
        >
          保存する
        </Button>
      </Box>

      <AddressSelectionModal
        hint={
          addressSearchTarget == AddressSearchTarget.Residence
            ? "※住んでいる市区町村を教えてください"
            : "※希望する勤務地の市区町村名を入力してください。"
        }
        open={showAddressModal}
        onClose={() => {
          setShowAddressModal(false);
          trigger("willWorkAddresses");
        }}
        onSelect={addressSelected}
      />

      {/* 職種選択モーダル */}
      <JobTypeSelectionModal
        open={showJobTypeModal}
        onClose={() => {
          setShowJobTypeModal(false);
          trigger("willJobTypes");
        }}
        onSelect={(jobTypeId, jobTypeName) => {
          addJobTypesSmall({
            ID: jobTypeId,
            Name: jobTypeName,
          });
        }}
      />
    </Box>
  );
}
