"use client";

import "./page.scss";
import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useForm, Controller } from "react-hook-form";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import FormControl from "@mui/material/FormControl";
import InputAdornment from "@mui/material/InputAdornment";
import Grid from "@mui/material/Grid2";
import { useAppDispatch, useAppSelector } from "@/lib/store/hooks";
import {
  Career,
  updateCareer,
} from "@/lib/store/features/profile/profileSlice";
import IndustrySelectionModal from "@/components/IndustrySelectionModal";
import JobTypeSelectionModal from "@/components/JobTypeSelectionModal";
import { fetchApiData } from "@/utils/fetch";
import { PagePath, ScrollEventType } from "@/constants/enum";
import {
  CAREER_MIN_JOIN_RETIRE_YEARS,
  CAREER_MAX_INCOME,
} from "@/constants/profile";
import {
  EXPERIENCE_COMPANY_OPTIONS,
  MANAGEMENT_EXPERIENCE_OPTIONS,
  MANAGEMENT_PEOPLE_OPTIONS,
  EMPLOYEE_NUMBER_OPTIONS,
  EMPLOYMENT_TYPE_OPTIONS,
  EMPLOYMENT_POST_OPTIONS,
  JOBTYPE_EXPERIENCE_OPTIONS,
} from "@/constants/profile";
import {
  DateFieldName,
  createDateFieldValidator,
  hasAPIValidationErrorForDateFields,
  validateJobTypeExpTermAgainstTenure,
  hasNoAPIValidationError,
} from "@/utils/profileUtils";
import { updateScrollEventType } from "@/lib/store/features/websocket/websocketSlice";

// 一度のバリデーションする項目
const DATE_VALIDATION_FIELDS: Array<keyof Career> = [
  "joinYear",
  "joinMonth",
  "retireYear",
  "retireMonth",
  "jobTypeExpTerm",
];

export default function CareerPage() {
  const router = useRouter();

  const dispatch = useAppDispatch();
  const career = useAppSelector((state) => state.profile.career);

  const [showIndustryModal, setShowIndustryModal] = useState(false);
  const [showJobTypeModal, setShowJobTypeModal] = useState(false);
  const dateFieldValidatorRef = useRef(createDateFieldValidator());
  const { setLastChangedDateField, validateDateFieldWithFocus } =
    dateFieldValidatorRef.current;

  // React Hook Form の設定
  const {
    control,
    handleSubmit,
    watch,
    setValue,
    getValues,
    trigger,
    formState: { errors },
  } = useForm<Career>({
    defaultValues: career,
    mode: "onBlur", // フォーカスが外れたときに検証
  });

  useEffect(() => {
    if (career.applyErrors?.length > 0) {
      trigger();
    }
  }, [career.applyErrors, trigger]);

  // jobTypeExpTermが選択されたときに、allCareerJobTypeExpTermが未選択なら同じ値を設定
  useEffect(() => {
    const subscription = watch((value, { name }) => {
      if (name === "jobTypeExpTerm" && value.jobTypeExpTerm) {
        // allCareerJobTypeExpTermが未選択の場合のみ自動設定
        if (
          !value.allCareerJobTypeExpTerm ||
          value.allCareerJobTypeExpTerm === ""
        ) {
          setValue("allCareerJobTypeExpTerm", value.jobTypeExpTerm);
        }
      }
    });
    return () => subscription.unsubscribe();
  }, [watch, setValue]);

  // フォーム送信時の処理
  const onSubmit = async (data: Career) => {
    console.debug("保存されたデータ:", data);

    try {
      const result = await fetchApiData(
        "profile/experience",
        "職歴の保存に失敗しました",
        {
          method: "POST",
          data: data,
        },
      );

      if (result.error) {
        console.error("職歴の保存に失敗しました:", result.error);
        // TODO: エラーハンドリング - ユーザーにエラーメッセージを表示
      } else {
        console.debug("職歴の保存に失敗しました:", result.data);

        dispatch(updateCareer(data));
        close();
      }
    } catch (error) {
      console.error("職歴の保存に失敗しました", error);
      // TODO: エラーハンドリング - ユーザーにエラーメッセージを表示
    }
  };

  const close = () => {
    router.push(PagePath.Chat);
    dispatch(updateScrollEventType(ScrollEventType.ProfileSaved));
  };

  // 業種選択時の処理
  const handleIndustrySelect = (industryId: number, industryName: string) => {
    setValue("industrySmallID", {
      ID: industryId,
      Name: industryName,
    });
    setShowIndustryModal(false);
  };

  // 職種選択時の処理
  const handleJobTypeSelect = (jobTypeId: number, jobTypeName: string) => {
    setValue("jobTypeSmallID", {
      ID: jobTypeId,
      Name: jobTypeName,
    });
    setShowJobTypeModal(false);
  };

  const currentYear = new Date().getFullYear();

  return (
    <Box className="page-container">
      {/* ヘッダ固定 */}
      <Box className="page-header">
        <Typography variant="h6" className="page-header__title">
          職歴
        </Typography>
      </Box>

      {/* スクロール可能なエリア */}
      <Box className="page-scroll">
        <Box
          component="form"
          id="career-form"
          onSubmit={handleSubmit(onSubmit)}
          className="page-form"
        >
          <Grid container spacing={2}>
            {/* 今までの経験について */}
            <Grid size={12}>
              <Box className="section-head">
                <Typography variant="subtitle1">
                  今までの経験について
                </Typography>
              </Box>
              <Typography variant="body2" gutterBottom>
                これまでの経験について教えてください。
              </Typography>
            </Grid>

            {/* 経験社数 */}
            <Grid size={12}>
              <Typography variant="body2" gutterBottom>
                いままでの経験社数
              </Typography>
              <Controller
                name="expCompanyNum"
                control={control}
                rules={{
                  required: "経験社数を選択してください",
                }}
                render={({ field }) => (
                  <FormControl
                    fullWidth
                    size="small"
                    error={!!errors.expCompanyNum}
                  >
                    <Select {...field} displayEmpty>
                      <MenuItem value="" disabled>
                        選択してください
                      </MenuItem>
                      {EXPERIENCE_COMPANY_OPTIONS.map((option) => (
                        <MenuItem key={option.ID} value={option.ID}>
                          {option.Name}
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.expCompanyNum && (
                      <Typography variant="caption" className="error-text">
                        {errors.expCompanyNum.message}
                      </Typography>
                    )}
                  </FormControl>
                )}
              />
              <Typography variant="caption" color="text.secondary">
                ※アルバイト以外
              </Typography>
            </Grid>

            {/* 今までのマネジメント経験年数 */}
            <Grid size={12}>
              <Typography variant="body2" gutterBottom>
                今までのマネジメント経験年数
              </Typography>
              <Controller
                name="managementExpTerm"
                control={control}
                rules={{
                  required: "マネジメント経験年数を選択してください",
                }}
                render={({ field }) => (
                  <FormControl
                    fullWidth
                    size="small"
                    error={!!errors.managementExpTerm}
                  >
                    <Select {...field} displayEmpty>
                      <MenuItem value="" disabled>
                        選択してください
                      </MenuItem>
                      {MANAGEMENT_EXPERIENCE_OPTIONS.map((option) => (
                        <MenuItem key={option.ID} value={option.ID}>
                          {option.Name}
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.managementExpTerm && (
                      <Typography variant="caption" className="error-text">
                        {errors.managementExpTerm.message}
                      </Typography>
                    )}
                  </FormControl>
                )}
              />
            </Grid>

            {watch("managementExpTerm") &&
              parseInt(getValues("managementExpTerm")) > 1 && (
                <>
                  {/* 今までのマネジメント人数 */}
                  <Grid size={12}>
                    <Typography variant="body2" gutterBottom>
                      今までのマネジメント人数
                    </Typography>
                    <Controller
                      name="managementPeopleNum"
                      control={control}
                      rules={{
                        required: "マネジメント人数を選択してください",
                      }}
                      render={({ field }) => (
                        <FormControl
                          fullWidth
                          size="small"
                          error={!!errors.managementPeopleNum}
                        >
                          <Select {...field} displayEmpty>
                            <MenuItem value="" disabled>
                              選択してください
                            </MenuItem>
                            {MANAGEMENT_PEOPLE_OPTIONS.map((option) => (
                              <MenuItem key={option.ID} value={option.ID}>
                                {option.Name}
                              </MenuItem>
                            ))}
                          </Select>
                          {errors.managementPeopleNum && (
                            <Typography
                              variant="caption"
                              className="error-text"
                            >
                              {errors.managementPeopleNum.message}
                            </Typography>
                          )}
                        </FormControl>
                      )}
                    />
                  </Grid>
                </>
              )}

            {watch("expCompanyNum") &&
              parseInt(getValues("expCompanyNum")) > 1 && (
                <>
                  {/* 直近の経験企業について */}
                  <Grid size={12}>
                    <Box className="section-head section-head--light">
                      <Typography variant="subtitle1">
                        直近の経験企業について
                      </Typography>
                    </Box>
                    <Typography variant="body2" gutterBottom>
                      在籍中（または退職済みの直近）の企業について教えてください。
                    </Typography>
                  </Grid>

                  {/* 企業名 */}
                  <Grid size={12}>
                    <Typography variant="body2" gutterBottom>
                      企業名
                    </Typography>
                    <Controller
                      name="companyName"
                      control={control}
                      rules={{
                        required: "企業名を入力してください",
                        maxLength: {
                          value: 255,
                          message: "255文字まで入力してください",
                        },
                        validate: (value) =>
                          hasNoAPIValidationError(
                            career.applyErrors,
                            "companyName",
                            value,
                            "企業名",
                          ),
                      }}
                      render={({ field }) => (
                        <TextField
                          {...field}
                          fullWidth
                          placeholder="株式会社〇〇"
                          variant="outlined"
                          size="small"
                          error={!!errors.companyName}
                          helperText={errors.companyName?.message}
                          slotProps={{
                            formHelperText: {
                              className: "error-text error-text--no-indent",
                            },
                          }}
                        />
                      )}
                    />
                    <Typography variant="caption" color="text.secondary">
                      ※この企業にはあなたの情報は表示されません
                    </Typography>
                  </Grid>

                  {/* 事業内容 */}
                  <Grid size={12}>
                    <Typography variant="body2" gutterBottom>
                      事業内容
                    </Typography>
                    <Controller
                      name="industrySmallID"
                      control={control}
                      rules={{
                        validate: (value) => {
                          if (!value || !value.ID || value.ID <= 0) {
                            return "事業内容を選択してください";
                          }
                          return true;
                        },
                      }}
                      render={({ field }) => (
                        <TextField
                          {...field}
                          value={getValues("industrySmallID")?.Name}
                          fullWidth
                          placeholder="事業内容を選択"
                          variant="outlined"
                          size="small"
                          error={!!errors.industrySmallID}
                          helperText={errors.industrySmallID?.message}
                          onClick={() => setShowIndustryModal(true)}
                          className="clickable-input"
                          slotProps={{
                            formHelperText: {
                              className: "error-text error-text--no-indent",
                            },
                            input: {
                              readOnly: true,
                            },
                          }}
                        />
                      )}
                    />
                  </Grid>

                  {/* 従業員数 */}
                  <Grid size={12}>
                    <Typography variant="body2" gutterBottom>
                      従業員数
                    </Typography>
                    <Controller
                      name="employeeNum"
                      control={control}
                      rules={{
                        required: "従業員数を選択してください",
                      }}
                      render={({ field }) => (
                        <FormControl
                          fullWidth
                          size="small"
                          error={!!errors.employeeNum}
                        >
                          <Select {...field} displayEmpty>
                            <MenuItem value="" disabled>
                              選択してください
                            </MenuItem>
                            {EMPLOYEE_NUMBER_OPTIONS.map((option) => (
                              <MenuItem key={option.ID} value={option.ID}>
                                {option.Name}
                              </MenuItem>
                            ))}
                          </Select>
                          {errors.employeeNum && (
                            <Typography
                              variant="caption"
                              className="error-text"
                            >
                              {errors.employeeNum.message}
                            </Typography>
                          )}
                        </FormControl>
                      )}
                    />
                  </Grid>

                  {/* 入社年月 */}
                  <Grid size={12}>
                    <Typography variant="body2" gutterBottom>
                      入社年月
                    </Typography>
                    <Box className="inline-fields">
                      <Controller
                        name="joinYear"
                        control={control}
                        rules={{
                          required: "入社年を入力してください",
                          pattern: {
                            value: /^\d{4}$/,
                            message: "4桁の年を入力してください",
                          },
                          min: {
                            value: currentYear - CAREER_MIN_JOIN_RETIRE_YEARS,
                            message: `${currentYear - CAREER_MIN_JOIN_RETIRE_YEARS}以降の年を入力してください`,
                          },
                          max: {
                            value: currentYear,
                            message: `${currentYear}までの年を入力してください`,
                          },
                          onChange: () => {
                            setLastChangedDateField(DateFieldName.JoinYear);
                            // 全ての関連項目を同時にバリデーションする
                            trigger(DATE_VALIDATION_FIELDS);
                          },
                          validate: (value) => {
                            const result = validateDateFieldWithFocus(
                              DateFieldName.JoinYear,
                              value,
                              getValues("joinMonth"),
                              getValues("retireYear"),
                              getValues("retireMonth"),
                            );

                            if (result !== true) {
                              return result;
                            }

                            return hasAPIValidationErrorForDateFields(
                              career.applyErrors,
                              "joinYear",
                              value,
                              "joinMonth",
                              getValues("joinMonth"),
                              "入社年月",
                            );
                          },
                        }}
                        render={({ field }) => (
                          <TextField
                            {...field}
                            type="number"
                            className="flex-1"
                            placeholder="XXXX"
                            variant="outlined"
                            size="small"
                            error={!!errors.joinYear}
                            helperText={errors.joinYear?.message}
                            slotProps={{
                              formHelperText: {
                                className: "error-text error-text--no-indent",
                              },
                              input: {
                                endAdornment: (
                                  <Typography variant="body2">年</Typography>
                                ),
                              },
                              htmlInput: {
                                className: "text-right",
                                inputMode: "numeric",
                                pattern: "[0-9]*",
                                maxLength: 4,
                              },
                            }}
                          />
                        )}
                      />
                      <Controller
                        name="joinMonth"
                        control={control}
                        rules={{
                          required: "入社月を入力してください",
                          pattern: {
                            value: /^(0?[1-9]|1[0-2])$/,
                            message: "1〜12の数字で入力してください",
                          },
                          onChange: () => {
                            setLastChangedDateField(DateFieldName.JoinMonth);
                            // 全ての関連項目を同時にバリデーションする
                            trigger(DATE_VALIDATION_FIELDS);
                          },
                          validate: (value) => {
                            const result = validateDateFieldWithFocus(
                              DateFieldName.JoinMonth,
                              getValues("joinYear"),
                              value,
                              getValues("retireYear"),
                              getValues("retireMonth"),
                            );

                            if (result !== true) {
                              return result;
                            }

                            return hasAPIValidationErrorForDateFields(
                              career.applyErrors,
                              "joinYear",
                              getValues("joinYear"),
                              "joinMonth",
                              value,
                              "入社年月",
                            );
                          },
                        }}
                        render={({ field }) => (
                          <TextField
                            {...field}
                            type="number"
                            className="flex-1"
                            placeholder="XX"
                            variant="outlined"
                            size="small"
                            error={!!errors.joinMonth}
                            helperText={errors.joinMonth?.message}
                            slotProps={{
                              formHelperText: {
                                className: "error-text error-text--no-indent",
                              },
                              input: {
                                endAdornment: (
                                  <Typography variant="body2">月</Typography>
                                ),
                              },
                              htmlInput: {
                                className: "text-right",
                                inputMode: "numeric",
                                pattern: "[0-9]*",
                                maxLength: 2,
                              },
                            }}
                            onChange={(e) => {
                              const value = e.target.value.replace(
                                /[^0-9]/g,
                                "",
                              );
                              const num = parseInt(value);

                              if (value === "" || (num >= 1 && num <= 12)) {
                                field.onChange(value);
                              }
                            }}
                          />
                        )}
                      />
                    </Box>
                  </Grid>

                  {/* 退職年月 */}
                  <Grid size={12}>
                    <Typography variant="body2" gutterBottom>
                      退職年月
                      <Typography variant="caption" color="text.secondary">
                        　※在職中の場合は入力不要
                      </Typography>
                    </Typography>
                    <Box className="inline-fields">
                      <Controller
                        name="retireYear"
                        control={control}
                        rules={{
                          pattern: {
                            value: /^\d{4}$/,
                            message: "4桁の年を入力してください",
                          },
                          min: {
                            value: currentYear - CAREER_MIN_JOIN_RETIRE_YEARS,
                            message: `${currentYear - CAREER_MIN_JOIN_RETIRE_YEARS}以降の年を入力してください`,
                          },
                          max: {
                            value: currentYear,
                            message: `${currentYear}までの年を入力してください`,
                          },
                          onChange: () => {
                            setLastChangedDateField(DateFieldName.RetireYear);
                            // 全ての関連項目を同時にバリデーションする
                            trigger(DATE_VALIDATION_FIELDS);
                          },
                          validate: (value) => {
                            const result = validateDateFieldWithFocus(
                              DateFieldName.RetireYear,
                              getValues("joinYear"),
                              getValues("joinMonth"),
                              value,
                              getValues("retireMonth"),
                            );

                            if (result !== true) {
                              return result;
                            }

                            return hasAPIValidationErrorForDateFields(
                              career.applyErrors,
                              "retireYear",
                              value,
                              "retireMonth",
                              getValues("retireMonth"),
                              "退職年月",
                            );
                          },
                        }}
                        render={({ field }) => (
                          <TextField
                            {...field}
                            type="number"
                            className="flex-1"
                            placeholder="XXXX"
                            variant="outlined"
                            size="small"
                            error={!!errors.retireYear}
                            helperText={errors.retireYear?.message}
                            slotProps={{
                              formHelperText: {
                                className: "error-text error-text--no-indent",
                              },
                              input: {
                                endAdornment: (
                                  <Typography variant="body2">年</Typography>
                                ),
                              },
                              htmlInput: {
                                className: "text-right",
                                inputMode: "numeric",
                                pattern: "[0-9]*",
                                maxLength: 4,
                              },
                            }}
                          />
                        )}
                      />
                      <Controller
                        name="retireMonth"
                        control={control}
                        rules={{
                          pattern: {
                            value: /^(0?[1-9]|1[0-2])$/,
                            message: "1〜12の数字で入力してください",
                          },
                          onChange: () => {
                            setLastChangedDateField(DateFieldName.RetireMonth);
                            // 全ての関連項目を同時にバリデーションする
                            trigger(DATE_VALIDATION_FIELDS);
                          },
                          validate: (value) => {
                            const result = validateDateFieldWithFocus(
                              DateFieldName.RetireMonth,
                              getValues("joinYear"),
                              getValues("joinMonth"),
                              getValues("retireYear"),
                              value,
                            );

                            if (result !== true) {
                              return result;
                            }

                            return hasAPIValidationErrorForDateFields(
                              career.applyErrors,
                              "retireYear",
                              getValues("retireYear"),
                              "retireMonth",
                              value,
                              "退職年月",
                            );
                          },
                        }}
                        render={({ field }) => (
                          <TextField
                            {...field}
                            type="number"
                            className="flex-1"
                            placeholder="XX"
                            variant="outlined"
                            size="small"
                            error={!!errors.retireMonth}
                            helperText={errors.retireMonth?.message}
                            slotProps={{
                              formHelperText: {
                                className: "error-text error-text--no-indent",
                              },
                              input: {
                                endAdornment: (
                                  <Typography variant="body2">月</Typography>
                                ),
                              },
                              htmlInput: {
                                className: "text-right",
                                inputMode: "numeric",
                                pattern: "[0-9]*",
                                maxLength: 2,
                              },
                            }}
                            onChange={(e) => {
                              const value = e.target.value.replace(
                                /[^0-9]/g,
                                "",
                              );
                              const num = parseInt(value);

                              if (value === "" || (num >= 1 && num <= 12)) {
                                field.onChange(value);
                              }
                            }}
                          />
                        )}
                      />
                    </Box>
                  </Grid>

                  {/* 雇用形態 */}
                  <Grid size={12}>
                    <Typography variant="body2" gutterBottom>
                      雇用形態
                    </Typography>
                    <Controller
                      name="employmentType"
                      control={control}
                      rules={{
                        required: "雇用形態を選択してください",
                      }}
                      render={({ field }) => (
                        <FormControl
                          fullWidth
                          size="small"
                          error={!!errors.employmentType}
                        >
                          <Select {...field} displayEmpty>
                            <MenuItem value="" disabled>
                              選択してください
                            </MenuItem>
                            {EMPLOYMENT_TYPE_OPTIONS.map((option) => (
                              <MenuItem key={option.ID} value={option.ID}>
                                {option.Name}
                              </MenuItem>
                            ))}
                          </Select>
                          {errors.employmentType && (
                            <Typography
                              variant="caption"
                              className="error-text"
                            >
                              {errors.employmentType.message}
                            </Typography>
                          )}
                        </FormControl>
                      )}
                    />
                  </Grid>

                  {/* 年収 */}
                  <Grid size={12}>
                    <Typography variant="body2" gutterBottom>
                      年収
                    </Typography>
                    <Controller
                      name="income"
                      control={control}
                      rules={{
                        required: "年収を入力してください",
                        pattern: {
                          value: /^[0-9]+$/,
                          message: "半角数字のみ入力可能です",
                        },
                        validate: (value) => {
                          const num = parseInt(value);
                          if (num < 1) {
                            return "1万円以上を入力してください";
                          }
                          if (num > CAREER_MAX_INCOME) {
                            return `${CAREER_MAX_INCOME}万円以下を入力してください`;
                          }
                          return hasNoAPIValidationError(
                            career.applyErrors,
                            "income",
                            value,
                            "年収",
                          );
                        },
                      }}
                      render={({ field }) => (
                        <TextField
                          {...field}
                          fullWidth
                          placeholder="XXXX"
                          variant="outlined"
                          size="small"
                          error={!!errors.income}
                          helperText={errors.income?.message}
                          slotProps={{
                            formHelperText: {
                              className: "error-text error-text--no-indent",
                            },
                            input: {
                              endAdornment: (
                                <InputAdornment position="end">
                                  万円
                                </InputAdornment>
                              ),
                            },
                            htmlInput: {
                              className: "text-right",
                              inputMode: "numeric",
                              pattern: "[0-9]*",
                            },
                          }}
                          onChange={(e) => {
                            const value = e.target.value.replace(/[^0-9]/g, "");
                            field.onChange(value);
                          }}
                        />
                      )}
                    />
                  </Grid>

                  {/* 役職 */}
                  <Grid size={12}>
                    <Typography
                      variant="body2"
                      className="bold-text"
                      gutterBottom
                    >
                      役職
                    </Typography>
                    <Controller
                      name="employmentPost"
                      control={control}
                      rules={{
                        required: "選択してください",
                      }}
                      render={({ field }) => (
                        <FormControl
                          fullWidth
                          size="small"
                          error={!!errors.employmentPost}
                        >
                          <Select {...field} displayEmpty>
                            <MenuItem value="" disabled>
                              選択してください
                            </MenuItem>
                            {EMPLOYMENT_POST_OPTIONS.map((option) => (
                              <MenuItem key={option.ID} value={option.ID}>
                                {option.Name}
                              </MenuItem>
                            ))}
                          </Select>
                          {errors.employmentPost && (
                            <Typography
                              variant="caption"
                              className="error-text"
                            >
                              {errors.employmentPost.message}
                            </Typography>
                          )}
                        </FormControl>
                      )}
                    />
                  </Grid>

                  {/* この企業で経験した主な職種 */}
                  <Grid size={12}>
                    <Typography variant="body2" gutterBottom>
                      この企業で経験した主な職種
                    </Typography>
                    <Controller
                      name="jobTypeSmallID"
                      control={control}
                      rules={{
                        validate: (value) => {
                          if (!value || !value.ID || value.ID <= 0) {
                            return "職種を選択してください";
                          }
                          return true;
                        },
                      }}
                      render={({ field }) => (
                        <TextField
                          {...field}
                          value={getValues("jobTypeSmallID")?.Name}
                          fullWidth
                          placeholder="例：営業、販売、事務、ドライバー、介護など"
                          variant="outlined"
                          size="small"
                          error={!!errors.jobTypeSmallID}
                          helperText={errors.jobTypeSmallID?.message}
                          onClick={() => setShowJobTypeModal(true)}
                          className="clickable-input"
                          slotProps={{
                            formHelperText: {
                              className: "error-text error-text--no-indent",
                            },
                            input: {
                              readOnly: true,
                            },
                          }}
                        />
                      )}
                    />
                  </Grid>

                  {(watch("jobTypeSmallID")?.ID ?? 0) > 0 && (
                    <>
                      {/* 直近の経験企業について */}
                      <Grid size={12}>
                        <Box className="section-head section-head--light">
                          <Typography variant="subtitle1">
                            「{getValues("jobTypeSmallID").Name}
                            」の経験について
                          </Typography>
                        </Box>
                        <Typography variant="body2" gutterBottom>
                          この企業で経験した年数と今までのキャリアの合計の経験年数を教えてください。
                        </Typography>
                      </Grid>

                      {/* この企業での経験年数 */}
                      <Grid size={12}>
                        <Typography variant="body2" gutterBottom>
                          この企業での経験年数
                        </Typography>
                        <Controller
                          name="jobTypeExpTerm"
                          control={control}
                          rules={{
                            required: "この企業での経験年数を選択してください",
                            validate: (value) => {
                              const allCareerExpTerm = getValues(
                                "allCareerJobTypeExpTerm",
                              );
                              if (
                                value &&
                                allCareerExpTerm &&
                                parseInt(value) > parseInt(allCareerExpTerm)
                              ) {
                                return "この企業での経験年数は、今までのキャリアの合計の経験年数以下である必要があります";
                              }

                              // 実際の在籍期間に対するバリデーション
                              const tenureValidation =
                                validateJobTypeExpTermAgainstTenure(
                                  value,
                                  getValues("joinYear"),
                                  getValues("joinMonth"),
                                  getValues("retireYear"),
                                  getValues("retireMonth"),
                                );

                              return tenureValidation;
                            },
                          }}
                          render={({ field }) => (
                            <FormControl
                              fullWidth
                              size="small"
                              error={!!errors.jobTypeExpTerm}
                            >
                              <Select {...field} displayEmpty>
                                <MenuItem value="" disabled>
                                  選択してください
                                </MenuItem>
                                {JOBTYPE_EXPERIENCE_OPTIONS.map((option) => (
                                  <MenuItem key={option.ID} value={option.ID}>
                                    {option.Name}
                                  </MenuItem>
                                ))}
                              </Select>
                              {errors.jobTypeExpTerm && (
                                <Typography
                                  variant="caption"
                                  className="error-text"
                                >
                                  {errors.jobTypeExpTerm.message}
                                </Typography>
                              )}
                            </FormControl>
                          )}
                        />
                      </Grid>

                      {/* 今までのキャリアの合計の経験年数 */}
                      <Grid size={12}>
                        <Typography variant="body2" gutterBottom>
                          今までのキャリアの合計の経験年数
                        </Typography>
                        <Controller
                          name="allCareerJobTypeExpTerm"
                          control={control}
                          rules={{
                            required: "この企業での経験年数を選択してください",
                            validate: (value) => {
                              const jobTypeExpTerm =
                                getValues("jobTypeExpTerm");
                              if (
                                value &&
                                jobTypeExpTerm &&
                                parseInt(value) < parseInt(jobTypeExpTerm)
                              ) {
                                return "今までのキャリアの合計の経験年数は、この企業での経験年数以上である必要があります";
                              }
                              return true;
                            },
                          }}
                          render={({ field }) => (
                            <FormControl
                              fullWidth
                              size="small"
                              error={!!errors.allCareerJobTypeExpTerm}
                            >
                              <Select {...field} displayEmpty>
                                <MenuItem value="" disabled>
                                  選択してください
                                </MenuItem>
                                {JOBTYPE_EXPERIENCE_OPTIONS.map((option) => (
                                  <MenuItem key={option.ID} value={option.ID}>
                                    {option.Name}
                                  </MenuItem>
                                ))}
                              </Select>
                              {errors.allCareerJobTypeExpTerm && (
                                <Typography
                                  variant="caption"
                                  className="error-text"
                                >
                                  {errors.allCareerJobTypeExpTerm.message}
                                </Typography>
                              )}
                            </FormControl>
                          )}
                        />
                      </Grid>
                    </>
                  )}
                </>
              )}
          </Grid>
        </Box>
      </Box>

      {/* フッター固定 */}
      <Box className="page-footer">
        <Button onClick={close} variant="outlined" className="btn-cancel">
          キャンセル
        </Button>
        <Button
          type="submit"
          form="career-form"
          variant="contained"
          color="primary"
          className="btn-submit"
        >
          保存する
        </Button>
      </Box>

      {/* 業種選択モーダル */}
      {showIndustryModal && (
        <IndustrySelectionModal
          open={showIndustryModal}
          onClose={() => setShowIndustryModal(false)}
          onSelect={handleIndustrySelect}
          selectedIndustryName={getValues("industrySmallID")?.Name}
        />
      )}

      {/* 職種選択モーダル */}
      <JobTypeSelectionModal
        open={showJobTypeModal}
        onClose={() => setShowJobTypeModal(false)}
        onSelect={handleJobTypeSelect}
        selectedJobTypeName={getValues("jobTypeSmallID")?.Name}
      />
    </Box>
  );
}
