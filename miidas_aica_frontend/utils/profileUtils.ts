import { FieldError } from "@/components/Profile";
import {
  BasicInfo,
  Career,
  Education,
  Will,
} from "@/lib/store/features/profile/profileSlice";
import { isNullOrEmpty } from "./stringUtils";
import { MasterType } from "@/types/utility-types";

export enum DateFieldName {
  JoinYear = "joinYear",
  JoinMonth = "joinMonth",
  RetireYear = "retireYear",
  RetireMonth = "retireMonth",
}

const JOIN_RETIRE_DATE_REVERSED_ERROR_MESSAGE =
  "入社年月と退社年月が逆転しています";
const FUTURE_DATE_ERROR_MESSAGE_TEMPLATE =
  "現在より未来のDATE年月の指定はできません";

export function requiresDepartment(schoolType: string) {
  return schoolType != "4" && schoolType != "6" && schoolType != "7";
}

export function hasApplyErrors(profile: any) {
  if ((profile.applyErrors?.length ?? 0) > 0) {
    return profile.applyErrors.some((error: FieldError) => {
      const fieldName = error.Field;
      const errorValue = error.Value;
      const currentValue = profile[fieldName];

      // Year/Monthフィールドの場合、年月を組み合わせて比較
      if (fieldName.endsWith("Year") || fieldName.endsWith("Month")) {
        const prefix = fieldName.replace(/(Year|Month)$/, "");
        const pairField = fieldName.endsWith("Year")
          ? `${prefix}Month`
          : `${prefix}Year`;
        const pairError = profile.applyErrors.find(
          (e: FieldError) => e.Field === pairField,
        );

        if (pairError) {
          return (
            errorValue == currentValue && pairError.Value == profile[pairField]
          );
        }
      }

      return errorValue == currentValue;
    });
  }

  return false;
}

// 値が有効かどうかをチェックする共通関数
function isValidValue(value: unknown): boolean {
  // 空文字、null、undefinedはNG
  if (value === "" || value == null) {
    return false;
  }

  // 配列の場合、空配列はNG
  if (Array.isArray(value)) {
    return value.length > 0;
  }

  // MasterTypeオブジェクトの場合、IDが有効かチェック
  if (typeof value === "object" && value !== null && "ID" in value) {
    return (value as MasterType).ID > 0;
  }

  return true;
}

export function basicInfoCompleted(basicInfo: BasicInfo) {
  if (hasApplyErrors(basicInfo)) {
    return false;
  }

  const { applyErrors, ...valuesWithoutApplyErrors } = basicInfo;

  const values = Object.values(valuesWithoutApplyErrors);
  return values.every((value) => isValidValue(value));
}

export function educationCompleted(education: Education) {
  if (hasApplyErrors(education)) {
    return false;
  }

  if (isNullOrEmpty(education.englishLevel)) {
    return false;
  }

  if (isNullOrEmpty(education.schoolType)) {
    return false;
  }

  if (isNullOrEmpty(education.graduationYear)) {
    return false;
  }

  // 学校区分が4、6、7以外の場合、学校名と学部・学科系統必須
  if (requiresDepartment(education.schoolType)) {
    if (isNullOrEmpty(education.schoolName)) {
      return false;
    }

    if (!education.department || education.department?.ID == 0) {
      return false;
    }
  }

  // 学校区分が4の場合、専門学校区分必須
  if (education.schoolType == "4") {
    if (
      !education.professionalTrainingCollegeCategory ||
      education.professionalTrainingCollegeCategory?.ID == 0
    ) {
      return false;
    }
  }

  return true;
}

export function careerCompleted(career: Career) {
  if (hasApplyErrors(career)) {
    return false;
  }

  if (career.expCompanyNum == "1") {
    return true;
  }

  // バリデーション対象外のフィールド
  // 退職年月は必須項目ではない
  const excludedFields = new Set<keyof Career>([
    "applyErrors",
    "retireYear",
    "retireMonth",
  ]);

  // Career型の全てのキーを取得
  const allKeys = Object.keys(career) as (keyof Career)[];

  return allKeys.every((key) => {
    // バリデーション対象外のフィールドはスキップ
    if (excludedFields.has(key)) {
      return true;
    }

    const value = career[key];

    // 値が空の場合
    if (value === "" || value === null || value === undefined) {
      if (key === "managementPeopleNum") {
        // マネジメント経験年数がナシの場合のみ、マネジメント経験人数は不要
        return career.managementExpTerm === "1";
      }
      return false;
    }

    return isValidValue(value);
  });
}

export function willCompleted(will: Will) {
  if (hasApplyErrors(will)) {
    return false;
  }

  const { applyErrors, ...valuesWithoutApplyErrors } = will;

  const values = Object.values(valuesWithoutApplyErrors);
  return values.every((value) => isValidValue(value));
}

// 入社年月と退社年月を比較して、
// 正常であればtrue、異常であればfalseを返す
// 退社年月が入社日より前であれば異常
// いずれか未来であれば異常
//
// 入社年または退社年が未来かどうかのチェックは既に
// TextFieldのMaxバリデーションで行われているため、ここでは行わない
export function checkJoinRetireDatesCorrect(
  joinYear: string, // 入社年
  joinMonth: string, // 入社月
  retireYear: string, // 退社年
  retireMonth: string, // 退社月
): { ok: boolean; error: string } {
  const okResult = { ok: true, error: "" };

  // 入社年と退社年の両方とも未入力であれば
  // 比較ができないので正常
  if (!joinYear && !retireYear) {
    return okResult;
  }

  let startYear = 0;
  let endYear = 0;

  if (joinYear) {
    startYear = parseInt(joinYear, 10);
  }

  if (retireYear) {
    endYear = parseInt(retireYear, 10);
  }

  // 片方がなければ比較ができないので正常
  if (!joinYear || !retireYear) {
    return okResult;
  }

  // 退社年が入社年より前であれば異常
  if (endYear < startYear) {
    return { ok: false, error: JOIN_RETIRE_DATE_REVERSED_ERROR_MESSAGE };
  }

  // いずれかの月が指定されていなければ
  // 比較ができないので正常
  if (!joinMonth || !retireMonth) {
    return okResult;
  }

  const startMonth = parseInt(joinMonth, 10);
  const endMonth = parseInt(retireMonth, 10);

  // 月のパラメーターはインデックスなので1月=ゼロ
  // 入力は1〜12なので、-1しないと正しいインデックスにならない
  const startDate = new Date(startYear, startMonth - 1, 1);
  const endDate = new Date(endYear, endMonth - 1, 1);

  // 同じ年に退職した場合でも入社月より前であれば異常
  // 同じ月に退職した場合でも正常するので > で比較
  if (startDate > endDate) {
    return { ok: false, error: JOIN_RETIRE_DATE_REVERSED_ERROR_MESSAGE };
  }

  const now = new Date();
  // 入社年月は未来であってはいけない
  if (startDate > now) {
    return {
      ok: false,
      error: FUTURE_DATE_ERROR_MESSAGE_TEMPLATE.replace("DATE", "入社"),
    };
  }

  // 退社年月は未来であってはいけない
  if (endDate > now) {
    return {
      ok: false,
      error: FUTURE_DATE_ERROR_MESSAGE_TEMPLATE.replace("DATE", "退社"),
    };
  }

  return okResult;
}

// 年月のバリデーションロジックを、コンポーネントごとに独立した状態で使えるようにする
export function createDateFieldValidator() {
  let lastChangedDateField: DateFieldName | null = null;

  const setLastChangedDateField = (fieldName: DateFieldName): void => {
    lastChangedDateField = fieldName;
  };

  const validateDateFieldWithFocus = (
    currentFieldName: DateFieldName,
    joinYear: string,
    joinMonth: string,
    retireYear: string,
    retireMonth: string,
  ): true | string => {
    const result = checkJoinRetireDatesCorrect(
      joinYear,
      joinMonth,
      retireYear,
      retireMonth,
    );

    // エラーがないならtrueを返す
    if (result.ok) {
      return true;
    }

    // 最後フォーカスされた項目にはエラーメッセージを表示する
    if (currentFieldName === lastChangedDateField) {
      return result.error;
    }

    // その他項目はエラーを表示しないが、赤くする
    return " ";
  };

  return { setLastChangedDateField, validateDateFieldWithFocus };
}

// 会員登録APIエラーがないかの確認
export function hasNoAPIValidationError(
  errors: FieldError[] | null | undefined,
  fieldName: string,
  value: string,
  fieldKanjiName: string,
  defaultMessage?: string,
) {
  const error = errors?.find(
    (err: FieldError) => err.Field === fieldName && err.Value == value,
  );

  if (error) {
    return (
      error.Message ??
      defaultMessage ??
      `${fieldKanjiName}を正しく入力してください。`
    );
  }

  return true;
}

// 会員登録APIエラーがないかの確認
export function hasAPIValidationErrorForDateFields(
  errors: FieldError[] | null | undefined,
  yearFieldName: string,
  currentYearValue: string,
  monthFieldName: string,
  currentMonthValue: string,
  fieldKanjiName: string,
  defaultMessage?: string,
) {
  if (errors) {
    const yearError = errors.find(
      (error: FieldError) =>
        error.Field === yearFieldName && error.Value == currentYearValue,
    );
    const monthError = errors.find(
      (error: FieldError) =>
        error.Field === monthFieldName && error.Value == currentMonthValue,
    );
    if (yearError && monthError) {
      return (
        yearError.Message ??
        monthError.Message ??
        defaultMessage ??
        `${fieldKanjiName}を正しく入力してください。`
      );
    }
  }

  return true;
}

/**
 * 職種経験年数が実際の在籍期間を超えていないかをバリデーション
 * @param jobTypeExpTerm - 選択された経験年数ID (例: "3" = 1年以上)
 * @param joinYear - 入社年
 * @param joinMonth - 入社月
 * @param retireYear - 退職年 (任意)
 * @param retireMonth - 退職月 (任意)
 * @returns 正常な場合true、エラーの場合エラーメッセージ
 */
export function validateJobTypeExpTermAgainstTenure(
  jobTypeExpTerm: string,
  joinYear: string,
  joinMonth: string,
  retireYear: string,
  retireMonth: string,
): true | string {
  // jobTypeExpTermが未選択、または"1"(経験なし)、"2"(1年未満)の場合はバリデーションスキップ
  if (!jobTypeExpTerm || jobTypeExpTerm === "1" || jobTypeExpTerm === "2") {
    return true;
  }

  // 入社年月が未入力の場合はバリデーションスキップ
  if (!joinYear || !joinMonth) {
    return true;
  }

  const joinYearNum = parseInt(joinYear, 10);
  const joinMonthNum = parseInt(joinMonth, 10);

  // 入社年月が正しい数値かチェック
  if (isNaN(joinYearNum) || isNaN(joinMonthNum)) {
    return true;
  }

  const joinDate = new Date(joinYearNum, joinMonthNum - 1, 1);

  // 終了日を決定
  let endDate: Date;
  if (retireYear && retireMonth) {
    // 退職済み: 退職月の翌月1日を使用
    const retireYearNum = parseInt(retireYear, 10);
    const retireMonthNum = parseInt(retireMonth, 10);

    if (isNaN(retireYearNum) || isNaN(retireMonthNum)) {
      return true;
    }

    if (retireMonthNum === 12) {
      endDate = new Date(retireYearNum + 1, 0, 1); // 翌年の1月1日
    } else {
      endDate = new Date(retireYearNum, retireMonthNum, 1); // 翌月1日
    }
  } else {
    // 在籍中: 現在月の翌月1日を使用
    const now = new Date();
    if (now.getMonth() === 11) {
      // 12月の場合
      endDate = new Date(now.getFullYear() + 1, 0, 1);
    } else {
      endDate = new Date(now.getFullYear(), now.getMonth() + 1, 1);
    }
  }

  // 在籍月数を計算
  const monthsEmployed =
    (endDate.getFullYear() - joinDate.getFullYear()) * 12 +
    (endDate.getMonth() - joinDate.getMonth());

  // 在籍年数を計算（整数除算）
  const yearsEmployed = Math.floor(monthsEmployed / 12);
  const remainingMonths = monthsEmployed % 12;

  // jobTypeExpTerm IDから必要な最低年数にマッピング
  // 1=経験なし, 2=1年未満, 3=1年以上, 4=2年以上, ..., 12=10年以上
  const minYearsRequired = parseInt(jobTypeExpTerm, 10) - 2;

  if (yearsEmployed < minYearsRequired) {
    return `直近企業での職種経験年数は在籍期間（${yearsEmployed}年${remainingMonths}ヶ月）を超えることはできません`;
  }

  return true;
}
