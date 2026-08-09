"use client";

import "./page.scss";
import { useRouter } from "next/navigation";
import { useForm, Controller, useWatch } from "react-hook-form";
import TextField from "@mui/material/TextField";
import Grid from "@mui/material/Grid2";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import { Select, MenuItem, FormControl, InputAdornment } from "@mui/material";
import {
  Education,
  updateEducation,
} from "@/lib/store/features/profile/profileSlice";
import { useAppDispatch, useAppSelector } from "@/lib/store/hooks";
import { useEffect, useState } from "react";
import { fetchApiData } from "@/utils/fetch";
import SchoolSelectionModal from "@/components/SchoolSelectionModal";
import DepartmentSelectionModal from "@/components/MasterTypeSelectionModal";
import { MASTER_KEYS } from "@/constants/master";
import { MasterType } from "@/types/utility-types";
import { PagePath, ScrollEventType } from "@/constants/enum";
import {
  EDUCATION_MIN_GRADUATION_YEAR,
  LANG_LEVEL_OPTIONS,
  SCHOOL_TYPE_OPTIONS,
} from "@/constants/profile";
import {
  requiresDepartment,
  hasNoAPIValidationError,
} from "@/utils/profileUtils";
import { updateScrollEventType } from "@/lib/store/features/websocket/websocketSlice";

export default function EducationPage() {
  const router = useRouter();

  const dispatch = useAppDispatch();
  const basicInfo = useAppSelector((state) => state.profile.basicInfo);
  const education = useAppSelector((state) => state.profile.education);

  // React Hook Form の設定
  const {
    control,
    handleSubmit,
    setValue,
    getValues,
    trigger,
    formState: { errors },
  } = useForm<Education>({
    defaultValues: education,
    mode: "onBlur", // フォーカスが外れたときに検証
  });

  useEffect(() => {
    if (education.applyErrors?.length > 0) {
      trigger();
    }
  }, [education.applyErrors, trigger]);

  const [showSchoolModal, setShowSchoolModal] = useState(false);
  const [showMasterTypeModal, setShowMasterTypeModal] = useState({
    open: false,
    masterKey: "",
    searchQuery: "",
  });

  // 最終学歴が更新されたら、推測卒業年を更新します。
  const schoolType = useWatch({
    control,
    name: "schoolType",
  });

  const getGraduationHelperText = (schoolType: string) => {
    const existed = SCHOOL_TYPE_OPTIONS.find(
      (schoolTypeOptions) => schoolTypeOptions["ID"] == schoolType,
    );
    if (!existed) {
      // 最終学歴が入力されていない場合、非表示
      return "";
    }

    const ageAtGraduation = existed["AgeAtGraduation"];
    if (basicInfo.birthYear && basicInfo.birthMonth) {
      // 基本情報の生年月が入力されている場合のみ
      const birthYear = parseInt(basicInfo.birthYear);
      const birthMonth = parseInt(basicInfo.birthMonth);

      if (!isNaN(birthYear) && !isNaN(birthMonth)) {
        // 基本情報の生年月を元に、卒業年を計算します。
        let graduationYear = birthYear + ageAtGraduation;

        // 基本情報の生まれ年月は4-12ｎの場合、翌年とします。
        if (birthMonth > 3) {
          graduationYear += 1;
        }

        return `※ 参考：あなたが上記の学校を${ageAtGraduation}歳で卒業した場合→${graduationYear}年`;
      }
    }

    // 基本情報の生年月が入力されていない場合非表示
    return "";
  };

  // フォーム送信時の処理
  const onSubmit = async (data: Education) => {
    console.debug("保存されたデータ:", data);

    try {
      const result = await fetchApiData(
        "profile/education",
        "学歴の保存に失敗しました",
        {
          method: "POST",
          data: data,
        },
      );

      if (result.error) {
        console.error("学歴の保存に失敗しました:", result.error);
        // TODO: エラーハンドリング - ユーザーにエラーメッセージを表示
      } else {
        console.debug("学歴の保存に失敗しました:", result.data);

        dispatch(updateEducation(data));
        close();
      }
    } catch (error) {
      console.error("学歴の保存に失敗しました", error);
      // TODO: エラーハンドリング - ユーザーにエラーメッセージを表示
    }
  };

  const close = () => {
    router.push(PagePath.Chat);
    dispatch(updateScrollEventType(ScrollEventType.ProfileSaved));
  };

  const handleSchoolSelect = (schoolName: string) => {
    setValue("schoolName", schoolName);
    setShowSchoolModal(false);
  };

  const handleDepartmentSelect = (value?: MasterType) => {
    if (value) {
      if (schoolType === "4") {
        setValue("professionalTrainingCollegeCategory", value);
      } else {
        setValue("department", value);
      }
    }

    setShowMasterTypeModal({
      open: false,
      masterKey: "",
      searchQuery: "",
    });
  };

  return (
    <Box className="page-container">
      {/* ヘッダ固定 */}
      <Box className="page-header">
        <Typography variant="h6" className="page-header__title">
          学歴・スキル
        </Typography>
      </Box>

      {/* スクロール可能なエリア */}
      <Box className="page-scroll">
        <Box
          component="form"
          id="education-form"
          onSubmit={handleSubmit(onSubmit)}
          className="page-form"
        >
          <Grid container spacing={2}>
            <Grid size={12}>
              <Typography variant="body2" gutterBottom>
                英会話スキル
              </Typography>
              <Controller
                name="englishLevel"
                control={control}
                rules={{
                  required: "英会話スキルを選択してください",
                }}
                render={({ field }) => (
                  <FormControl
                    fullWidth
                    size="small"
                    error={!!errors.englishLevel}
                  >
                    <Select {...field} displayEmpty>
                      <MenuItem value="" disabled>
                        選択してください
                      </MenuItem>
                      {LANG_LEVEL_OPTIONS.map((option) => (
                        <MenuItem key={option.ID} value={option.ID}>
                          {option.Name}
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.englishLevel && (
                      <Typography variant="caption" className="error-text">
                        {errors.englishLevel.message}
                      </Typography>
                    )}
                  </FormControl>
                )}
              />
            </Grid>
            <Grid size={12}>
              <Typography variant="body2" gutterBottom>
                最終学歴
              </Typography>
              <Controller
                name="schoolType"
                control={control}
                rules={{
                  required: "学校区分を選択してください",
                }}
                render={({ field }) => (
                  <FormControl
                    fullWidth
                    size="small"
                    error={!!errors.schoolType}
                  >
                    <Select {...field} displayEmpty>
                      <MenuItem value="" disabled>
                        選択してください
                      </MenuItem>
                      {SCHOOL_TYPE_OPTIONS.map((option) => (
                        <MenuItem key={option.ID} value={option.ID}>
                          {option.Name}
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.schoolType && (
                      <Typography variant="caption" className="error-text">
                        {errors.schoolType.message}
                      </Typography>
                    )}
                  </FormControl>
                )}
              />
            </Grid>
            {schoolType && requiresDepartment(schoolType) && (
              <>
                <Grid size={12}>
                  <Typography variant="body2" gutterBottom>
                    学校名
                  </Typography>
                  <Controller
                    name="schoolName"
                    control={control}
                    rules={{
                      required: "学校名を入力してください",
                      maxLength: {
                        value: 200,
                        message: "200文字まで入力してください",
                      },
                      validate: (value) =>
                        hasNoAPIValidationError(
                          education.applyErrors,
                          "schoolName",
                          value,
                          "学校名",
                        ),
                    }}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        fullWidth
                        placeholder="学校名を入力"
                        variant="outlined"
                        size="small"
                        error={!!errors.schoolName}
                        helperText={errors.schoolName?.message}
                        onClick={() => setShowSchoolModal(true)}
                        className="clickable-input"
                        slotProps={{
                          formHelperText: { className: "error-text" },
                          input: {
                            readOnly: true,
                          },
                        }}
                      />
                    )}
                  />
                </Grid>
                <Grid size={12}>
                  <Typography variant="body2" gutterBottom>
                    学部・学科系統
                  </Typography>
                  <Controller
                    name="department"
                    control={control}
                    rules={{
                      required: "学部・学科系統を入力してください",
                    }}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        value={getValues("department").Name}
                        fullWidth
                        placeholder="学部・学科系統を選択"
                        variant="outlined"
                        size="small"
                        error={!!errors.department}
                        helperText={errors.department?.message}
                        onClick={() =>
                          setShowMasterTypeModal({
                            open: true,
                            masterKey: MASTER_KEYS.DEPARTMENT_TYPE,
                            searchQuery: getValues("department").Name,
                          })
                        }
                        className="clickable-input"
                        slotProps={{
                          formHelperText: { className: "error-text" },
                          input: {
                            readOnly: true,
                          },
                        }}
                      />
                    )}
                  />
                </Grid>
              </>
            )}
            {schoolType === "4" && (
              <Grid size={12}>
                <Typography variant="body2" gutterBottom>
                  学部・学科系統
                </Typography>
                <Controller
                  name="professionalTrainingCollegeCategory"
                  control={control}
                  rules={{
                    required: "学部・学科系統を入力してください",
                  }}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      value={
                        getValues("professionalTrainingCollegeCategory").Name
                      }
                      fullWidth
                      placeholder="学部・学科系統を選択"
                      variant="outlined"
                      size="small"
                      error={!!errors.professionalTrainingCollegeCategory}
                      helperText={
                        errors.professionalTrainingCollegeCategory?.message
                      }
                      onClick={() =>
                        setShowMasterTypeModal({
                          open: true,
                          masterKey:
                            MASTER_KEYS.PROFESSIONAL_TRAINING_COLLEGE_CATEGORY,
                          searchQuery: getValues(
                            "professionalTrainingCollegeCategory",
                          ).Name,
                        })
                      }
                      className="clickable-input"
                      slotProps={{
                        formHelperText: { className: "error-text" },
                        input: {
                          readOnly: true,
                        },
                      }}
                    />
                  )}
                />
              </Grid>
            )}
            <Grid size={6}>
              <Typography variant="body2" gutterBottom>
                卒業年
              </Typography>
              <Controller
                name="graduationYear"
                control={control}
                rules={{
                  required: "卒業年を入力してください",
                  pattern: {
                    value: /^\d{4}$/,
                    message: "4桁の年を入力してください",
                  },
                  validate: (value) => {
                    const year = parseInt(value);
                    const currentYear = new Date().getFullYear();
                    const minGraduationYear =
                      currentYear - EDUCATION_MIN_GRADUATION_YEAR;

                    if (year < minGraduationYear) {
                      return `${minGraduationYear}年以降の年を入力してください`;
                    }
                    if (year > currentYear) {
                      return `${currentYear}年以前の年を入力してください`;
                    }
                    return hasNoAPIValidationError(
                      education.applyErrors,
                      "graduationYear",
                      value,
                      "卒業年",
                    );
                  },
                }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    type="number"
                    placeholder="XXXX"
                    variant="outlined"
                    size="small"
                    error={!!errors.graduationYear}
                    helperText={errors.graduationYear?.message}
                    slotProps={{
                      formHelperText: { className: "error-text" },
                      input: {
                        endAdornment: (
                          <InputAdornment position="end">年</InputAdornment>
                        ),
                      },
                      htmlInput: {
                        className: "text-right",
                        inputMode: "numeric",
                        pattern: "[0-9]*",
                        maxLength: 4,
                      },
                    }}
                    onChange={(e) => {
                      const value = e.target.value
                        .replace(/[^0-9]/g, "")
                        .slice(0, 4);
                      field.onChange(value);
                    }}
                  />
                )}
              />
              {getGraduationHelperText(schoolType) && (
                <Typography variant="caption" color="text.secondary">
                  {getGraduationHelperText(schoolType)}
                </Typography>
              )}
            </Grid>
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
          form="education-form"
          variant="contained"
          color="primary"
          className="btn-submit"
        >
          保存する
        </Button>
      </Box>

      <SchoolSelectionModal
        open={showSchoolModal}
        onClose={() => setShowSchoolModal(false)}
        onSelect={handleSchoolSelect}
        selectedSchoolName={getValues("schoolName")}
        schoolType={parseInt(schoolType) || 0}
      />

      <DepartmentSelectionModal
        open={showMasterTypeModal.open}
        onClose={handleDepartmentSelect}
        onSelect={handleDepartmentSelect}
        selectedMasterKey={showMasterTypeModal.masterKey}
        selectedResultName={showMasterTypeModal.searchQuery}
      />
    </Box>
  );
}
