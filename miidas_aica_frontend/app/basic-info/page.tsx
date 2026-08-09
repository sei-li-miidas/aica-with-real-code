"use client";

import "./page.scss";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm, Controller } from "react-hook-form";
import TextField from "@mui/material/TextField";
import Grid from "@mui/material/Grid2";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import LockIcon from "@mui/icons-material/Lock";
import {
  FormControlLabel,
  Radio,
  RadioGroup,
  Select,
  MenuItem,
  FormControl,
} from "@mui/material";
import {
  BasicInfo,
  updateBasicInfo,
} from "@/lib/store/features/profile/profileSlice";
import AddressSelectionModal from "@/components/AddressSelectionModal";
import { useAppDispatch, useAppSelector } from "@/lib/store/hooks";
import { fetchApiData, searchByPrefectureCityName } from "@/utils/fetch";
import { Address } from "@/types/utility-types";
import {
  LANGUAGES,
  DRIVER_LICENCE_OPTIONS,
  GENDER_OPTIONS,
} from "@/constants/profile";
import { PagePath, ScrollEventType } from "@/constants/enum";
import {
  hasNoAPIValidationError,
  hasAPIValidationErrorForDateFields,
} from "@/utils/profileUtils";
import { updateScrollEventType } from "@/lib/store/features/websocket/websocketSlice";

export default function BasicInfoPage() {
  const router = useRouter();

  const dispatch = useAppDispatch();
  const positionSearch = useAppSelector((state) => state.positionSearch);
  const basicInfo = useAppSelector((state) => state.profile.basicInfo);

  const [showAddressModal, setShowAddressModal] = useState(false);

  // React Hook Form の設定
  const {
    control,
    handleSubmit,
    getValues,
    setValue,
    trigger,
    formState: { errors },
  } = useForm<BasicInfo>({
    defaultValues: basicInfo,
    mode: "onBlur", // フォーカスが外れたときに検証
  });

  const currentYear = new Date().getFullYear();

  useEffect(() => {
    if (basicInfo.applyErrors?.length > 0) {
      trigger();
    }
  }, [basicInfo.applyErrors, trigger]);

  // フォーム送信時の処理
  const onSubmit = async (data: BasicInfo) => {
    console.debug("保存されたデータ:", data);

    try {
      const result = await fetchApiData(
        "profile/basic",
        "基本情報の保存に失敗しました",
        {
          method: "POST",
          data: data,
        },
      );

      if (result.error) {
        console.error("基本情報の保存に失敗しました:", result.error);
        // TODO: エラーハンドリング - ユーザーにエラーメッセージを表示
      } else {
        console.debug("基本情報が正常に保存されました:", result.data);

        dispatch(updateBasicInfo(data));
        close();
      }
    } catch (error) {
      console.error("基本情報の保存に失敗しました", error);
      // TODO: エラーハンドリング - ユーザーにエラーメッセージを表示
    }
  };

  const addressSelected = (address: Address) => {
    setValue("prefecture", {
      ID: address.prefecture.ID,
      Name: address.prefecture.Name,
    });
    setValue("city", {
      ID: address.city.ID,
      Name: address.city.Name,
    });
    setShowAddressModal(false);
  };

  const close = () => {
    router.push(PagePath.Chat);
    dispatch(updateScrollEventType(ScrollEventType.ProfileSaved));
  };

  // 初期値設定
  useEffect(() => {
    if (getValues("prefecture.ID") > 0) {
      // 基本情報が保存済みの場合、スキップ
      // お住まいを設定するので、お住まいの入力より判断
      return;
    }

    const abortController = new AbortController();

    // ユーザー会話から収集してきた居住地データ（Residence.Address）を取得し、初期値として利用する。
    const prefectureName = positionSearch.residencePrefectureName;
    const cityName = positionSearch.residenceCityName;

    if (prefectureName && cityName) {
      searchByPrefectureCityName(prefectureName, cityName, {
        signal: abortController.signal,
      }).then((data) => {
        if (data.length > 0) {
          setValue("prefecture", data[0].prefecture);
          setValue("city", data[0].city);
        }
      });
    }

    return () => {
      // ページクローズ時にリクエストを廃止します。
      abortController.abort();
    };
  }, [positionSearch.residencePrefectureName, positionSearch.residenceCityName, getValues, setValue]);

  return (
    <Box className="page-container">
      {/* ヘッダ固定 */}
      <Box className="page-header">
        <Typography variant="h6" className="page-header__title">
          基本情報
        </Typography>
      </Box>

      {/* スクロール可能なエリア */}
      <Box className="page-scroll">
        <Box
          component="form"
          id="basic-info-form"
          onSubmit={handleSubmit(onSubmit)}
          className="page-form"
        >
          <Box className="privacy-note">
            <LockIcon fontSize="small" color="primary" className="note-icon" />
            <Typography variant="body2" color="textSecondary">
              は自分が応募した企業にのみ表示されます
            </Typography>
          </Box>

          <Grid container spacing={2}>
            <Grid size={6}>
              <Typography variant="body2" className="bold-text" gutterBottom>
                姓
                <LockIcon
                  fontSize="small"
                  color="primary"
                  className="inline-icon"
                />
              </Typography>
              <Controller
                name="lastName"
                control={control}
                rules={{
                  required: "姓を入力してください",
                  maxLength: {
                    value: 50,
                    message: "50文字まで入力してください",
                  },
                  validate: (value) =>
                    hasNoAPIValidationError(
                      basicInfo.applyErrors,
                      "lastName",
                      value,
                      "姓",
                    ),
                }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    placeholder="山田"
                    variant="outlined"
                    size="small"
                    error={!!errors.lastName}
                    helperText={errors.lastName?.message}
                    slotProps={{
                      formHelperText: {
                        className: "error-text error-text--no-indent",
                      },
                    }}
                  />
                )}
              />
            </Grid>
            <Grid size={6}>
              <Typography variant="body2" className="bold-text" gutterBottom>
                名
                <LockIcon
                  fontSize="small"
                  color="primary"
                  className="inline-icon"
                />
              </Typography>
              <Controller
                name="firstName"
                control={control}
                rules={{
                  required: "名を入力してください",
                  maxLength: {
                    value: 50,
                    message: "50文字まで入力してください",
                  },
                  validate: (value) =>
                    hasNoAPIValidationError(
                      basicInfo.applyErrors,
                      "firstName",
                      value,
                      "名",
                    ),
                }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    placeholder="太郎"
                    variant="outlined"
                    size="small"
                    error={!!errors.firstName}
                    helperText={errors.firstName?.message}
                    slotProps={{
                      formHelperText: {
                        className: "error-text error-text--no-indent",
                      },
                    }}
                  />
                )}
              />
            </Grid>
            <Grid size={6}>
              <Typography variant="body2" className="bold-text" gutterBottom>
                姓（カナ）
                <LockIcon
                  fontSize="small"
                  color="primary"
                  className="inline-icon"
                />
              </Typography>
              <Controller
                name="lastNameKana"
                control={control}
                rules={{
                  required: "姓（カナ）を入力してください",
                  maxLength: {
                    value: 50,
                    message: "50文字まで入力してください",
                  },
                  validate: (value) =>
                    hasNoAPIValidationError(
                      basicInfo.applyErrors,
                      "lastNameKana",
                      value,
                      "姓（カナ）",
                    ),
                }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    placeholder="ヤマダ"
                    variant="outlined"
                    size="small"
                    error={!!errors.lastNameKana}
                    helperText={errors.lastNameKana?.message}
                    slotProps={{
                      formHelperText: {
                        className: "error-text error-text--no-indent",
                      },
                    }}
                  />
                )}
              />
            </Grid>
            <Grid size={6}>
              <Typography variant="body2" className="bold-text" gutterBottom>
                名（カナ）
                <LockIcon
                  fontSize="small"
                  color="primary"
                  className="inline-icon"
                />
              </Typography>
              <Controller
                name="firstNameKana"
                control={control}
                rules={{
                  required: "名（カナ）を入力してください",
                  maxLength: {
                    value: 50,
                    message: "50文字まで入力してください",
                  },
                  validate: (value) =>
                    hasNoAPIValidationError(
                      basicInfo.applyErrors,
                      "firstNameKana",
                      value,
                      "名（カナ）",
                    ),
                }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    placeholder="タロウ"
                    variant="outlined"
                    size="small"
                    error={!!errors.firstNameKana}
                    helperText={errors.firstNameKana?.message}
                    slotProps={{
                      formHelperText: {
                        className: "error-text error-text--no-indent",
                      },
                    }}
                  />
                )}
              />
            </Grid>
            <Grid size={12}>
              <Typography variant="body2" className="bold-text" gutterBottom>
                メールアドレス
                <LockIcon
                  fontSize="small"
                  color="primary"
                  className="inline-icon"
                />
              </Typography>
              <Controller
                name="email"
                control={control}
                rules={{
                  required: "メールアドレスを入力してください",
                  pattern: {
                    // RFC5322対応の正規表現 https://regex101.com/r/3uvtNl/1 からコピー
                    value:
                      /^((?:[A-Za-z0-9!#$%&'*+\-\/=?^_`{|}~]|(?<=^|\.)"|"(?=$|\.|@)|(?<=".*)[ .](?=.*")|(?<!\.)\.){1,64})(@)((?:[A-Za-z0-9.\-])*(?:[A-Za-z0-9])\.(?:[A-Za-z0-9]){2,})$/,
                    message: "有効なメールアドレスを入力してください",
                  },
                  maxLength: {
                    value: 100,
                    message: "100文字まで入力してください",
                  },
                  validate: (value) =>
                    hasNoAPIValidationError(
                      basicInfo.applyErrors,
                      "email",
                      value,
                      "メールアドレス",
                    ),
                }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    placeholder="sample@sample.com"
                    variant="outlined"
                    size="small"
                    error={!!errors.email}
                    type="email"
                    helperText={errors.email?.message}
                    slotProps={{
                      formHelperText: {
                        className: "error-text error-text--no-indent",
                      },
                    }}
                  />
                )}
              />
            </Grid>
            <Grid size={12}>
              <Typography variant="body2" className="bold-text" gutterBottom>
                電話番号
                <LockIcon
                  fontSize="small"
                  color="primary"
                  className="inline-icon"
                />
              </Typography>
              <Controller
                name="phoneNo"
                control={control}
                rules={{
                  required: "電話番号を入力してください",
                  pattern: {
                    value: /^0[0-9]{9,10}$/,
                    message: "有効な電話番号を入力してください（ハイフンなし）",
                  },
                  validate: (value) =>
                    hasNoAPIValidationError(
                      basicInfo.applyErrors,
                      "phoneNo",
                      value,
                      "電話番号",
                    ),
                }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    placeholder="09012345678"
                    variant="outlined"
                    size="small"
                    type="tel"
                    error={!!errors.phoneNo}
                    helperText={errors.phoneNo?.message}
                    slotProps={{
                      formHelperText: {
                        className: "error-text error-text--no-indent",
                      },
                    }}
                  />
                )}
              />
              <Typography variant="caption" color="textSecondary">
                ※ハイフンなし
              </Typography>
            </Grid>
            <Grid size={12}>
              <Typography variant="body2" className="bold-text" gutterBottom>
                性別
              </Typography>
              <Controller
                name="gender"
                control={control}
                rules={{
                  required: "性別を選択してください。",
                }}
                render={({ field }) => (
                  <Box>
                    <RadioGroup {...field} row className="gender-group">
                      {GENDER_OPTIONS.map((option) => (
                        <FormControlLabel
                          key={option.ID}
                          value={option.ID}
                          control={<Radio />}
                          label={option.Name}
                          className="gender-option"
                        />
                      ))}
                    </RadioGroup>
                    {errors.gender && (
                      <Typography variant="caption" className="error-text">
                        {errors.gender.message}
                      </Typography>
                    )}
                  </Box>
                )}
              />
            </Grid>
            <Grid size={12}>
              <Typography variant="body2" className="bold-text" gutterBottom>
                新しいパスワード
              </Typography>
              <Controller
                name="password"
                control={control}
                rules={{
                  required: "パスワードを入力してください",
                  pattern: {
                    value: /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,16}$/,
                    message:
                      "半角英数字を組み合わせ、8文字以上、16文字以内で入力してください",
                  },
                  validate: (value) =>
                    hasNoAPIValidationError(
                      basicInfo.applyErrors,
                      "password",
                      value,
                      "パスワード",
                    ),
                }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    type="password"
                    placeholder="パスワードを入力"
                    variant="outlined"
                    size="small"
                    error={!!errors.password}
                    helperText={errors.password?.message}
                    slotProps={{
                      formHelperText: {
                        className: "error-text error-text--no-indent",
                      },
                      input: {
                        inputMode: "text",
                        autoComplete: "new-password",
                      },
                    }}
                  />
                )}
              />
              <Typography variant="caption" color="textSecondary">
                ※アルファベットと数字の組み合わせ8文字以上
              </Typography>
            </Grid>
            <Grid size={6}>
              <Typography variant="body2" className="bold-text" gutterBottom>
                生まれた年
              </Typography>
              <Controller
                name="birthYear"
                control={control}
                rules={{
                  required: "生まれた年を入力してください",
                  pattern: {
                    value: /^\d{4}$/,
                    message: "4桁の年を入力してください",
                  },
                  min: {
                    value: currentYear - 100,
                    message: `${currentYear - 100}以降の年を入力してください`,
                  },
                  max: {
                    value: currentYear - 15,
                    message: `${currentYear - 15}までの年を入力してください`,
                  },
                  validate: (value) =>
                    hasAPIValidationErrorForDateFields(
                      basicInfo.applyErrors,
                      "birthYear",
                      value,
                      "birthMonth",
                      getValues("birthMonth"),
                      "生まれた年月",
                    ),
                }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    type="number"
                    placeholder="XXXX"
                    variant="outlined"
                    size="small"
                    error={!!errors.birthYear}
                    helperText={errors.birthYear?.message}
                    slotProps={{
                      formHelperText: {
                        className: "error-text error-text--no-indent",
                      },
                      input: {
                        endAdornment: (
                          <Typography variant="body2" color="textDisabled">
                            年
                          </Typography>
                        ),
                      },
                      htmlInput: {
                        className: "text-right",
                        inputMode: "numeric",
                        maxLength: 4,
                      },
                    }}
                    onChange={(e) => {
                      const value = e.target.value
                        .replace(/[^0-9]/g, "")
                        .slice(0, 4);
                      field.onChange(Number(value) || ""); // Convert to number

                      trigger(["birthYear", "birthMonth"]);
                    }}
                  />
                )}
              />
            </Grid>
            <Grid size={6}>
              <Typography variant="body2" className="bold-text" gutterBottom>
                生まれた月
              </Typography>
              <Controller
                name="birthMonth"
                control={control}
                rules={{
                  required: "生まれた月を入力してください",
                  pattern: {
                    value: /^(0?[1-9]|1[0-2])$/,
                    message: "1〜12の数字で入力してください",
                  },
                  onChange: () => {
                    trigger(["birthYear", "birthMonth"]);
                  },
                  validate: (value) =>
                    hasAPIValidationErrorForDateFields(
                      basicInfo.applyErrors,
                      "birthYear",
                      getValues("birthYear"),
                      "birthMonth",
                      value,
                      "生まれた年月",
                    ),
                }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    type="number"
                    placeholder="XX"
                    variant="outlined"
                    size="small"
                    error={!!errors.birthMonth}
                    helperText={errors.birthMonth?.message}
                    slotProps={{
                      formHelperText: {
                        className: "error-text error-text--no-indent",
                      },
                      input: {
                        endAdornment: (
                          <Typography variant="body2" color="textDisabled">
                            月
                          </Typography>
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
                      const value = e.target.value.replace(/[^0-9]/g, "");
                      const num = parseInt(value);

                      if (value === "" || (num >= 1 && num <= 12)) {
                        field.onChange(value);
                      }

                      trigger(["birthYear", "birthMonth"]);
                    }}
                  />
                )}
              />
            </Grid>
            <Grid size={12}>
              <Typography variant="body2" className="bold-text" gutterBottom>
                お住まいの市区町村名
              </Typography>
              <Controller
                name="prefecture"
                control={control}
                rules={{
                  required: "都道府県と市区町村を入力してください",
                  validate: () => {
                    const prefectureName = getValues("prefecture").Name || "";
                    const cityName = getValues("city").Name || "";

                    if (!prefectureName || !cityName) {
                      return "都道府県と市区町村を入力してください";
                    }

                    return true;
                  },
                }}
                render={({ field }) => {
                  // 都道府県と市区町村を結合して表示する
                  const prefectureName = getValues("prefecture").Name || "";
                  const cityName = getValues("city").Name || "";
                  const combinedValue = `${prefectureName}${cityName}`;

                  return (
                    <TextField
                      {...field}
                      value={combinedValue}
                      fullWidth
                      placeholder="◯◯県◯◯市"
                      variant="outlined"
                      size="small"
                      error={!!errors.prefecture}
                      helperText={errors.prefecture?.message}
                      className="clickable-input"
                      slotProps={{
                        formHelperText: {
                          className: "error-text error-text--no-indent",
                        },
                        input: {
                          readOnly: true,
                        },
                      }}
                      onClick={() => setShowAddressModal(true)}
                    />
                  );
                }}
              />
            </Grid>
            <Grid size={12}>
              <Typography variant="body2" className="bold-text" gutterBottom>
                最も得意な言語
              </Typography>
              <Controller
                name="firstLanguage"
                control={control}
                rules={{
                  required: "選択してください",
                }}
                render={({ field }) => (
                  <FormControl
                    fullWidth
                    size="small"
                    error={!!errors.firstLanguage}
                  >
                    <Select {...field} displayEmpty>
                      <MenuItem value="" disabled>
                        選択してください
                      </MenuItem>
                      {LANGUAGES.map((language) => (
                        <MenuItem key={language.ID} value={language.ID}>
                          {language.Name}
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.firstLanguage && (
                      <Typography variant="caption" className="error-text">
                        {errors.firstLanguage.message}
                      </Typography>
                    )}
                  </FormControl>
                )}
              />
            </Grid>
            <Grid size={12}>
              <Typography variant="body2" className="bold-text" gutterBottom>
                運転免許証
              </Typography>
              <Controller
                name="driverLicence"
                control={control}
                rules={{
                  required: "選択してください",
                }}
                render={({ field }) => (
                  <FormControl
                    fullWidth
                    size="small"
                    error={!!errors.driverLicence}
                  >
                    <Select {...field} displayEmpty>
                      <MenuItem value="" disabled>
                        選択してください
                      </MenuItem>
                      {DRIVER_LICENCE_OPTIONS.map((option) => (
                        <MenuItem key={option.ID} value={option.ID}>
                          {option.Name}
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.driverLicence && (
                      <Typography variant="caption" className="error-text">
                        {errors.driverLicence.message}
                      </Typography>
                    )}
                  </FormControl>
                )}
              />
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
          form="basic-info-form"
          variant="contained"
          color="primary"
          className="btn-submit"
        >
          保存する
        </Button>
      </Box>

      <AddressSelectionModal
        hint="※ 住んでいる市区町村を入力してください"
        open={showAddressModal}
        onClose={() => setShowAddressModal(false)}
        selectedPrefectureName={getValues("prefecture").Name}
        selectedCityName={getValues("city").Name}
        onSelect={addressSelected}
      />
    </Box>
  );
}
