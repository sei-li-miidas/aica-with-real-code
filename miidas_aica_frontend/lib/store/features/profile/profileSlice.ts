import { FieldError } from "@/components/Profile";
import { Address, MasterType } from "@/types/utility-types";
import { createSlice, PayloadAction } from "@reduxjs/toolkit";

export interface BasicInfo {
  // お名前（姓）
  lastName: string;
  // お名前（名）
  firstName: string;
  // オナマエ（セイ）
  lastNameKana: string;
  // オナマエ（メイ）
  firstNameKana: string;
  // メールアドレス
  email: string;
  // 電話番号/携帯（市外局番）
  phoneNo: string;
  // 性別
  gender: string;
  // パスワード
  password: string;
  // 生年月
  birthYear: string;
  birthMonth: string;
  // 都道府県（居住地）
  prefecture: MasterType;
  // 市区町村（居住地）
  city: MasterType;
  // 最も得意な言語
  firstLanguage: string;
  // 運転免許証
  driverLicence: string;
  // 面談応募・登録エラー
  applyErrors: FieldError[];
}

export interface Education {
  // 最終学歴 学校区分
  schoolType: string;
  // 学校名
  schoolName: string;
  // 学部・学科系統
  department: MasterType;
  // 専門学校区分
  professionalTrainingCollegeCategory: MasterType;
  // 卒業年
  graduationYear: string;
  // 英語スキル
  englishLevel: string;
  // 面談応募・登録エラー
  applyErrors: FieldError[];
}

export interface Career {
  // 経験社数
  expCompanyNum: string;
  // マネジメント経験年数
  managementExpTerm: string;
  // マネジメント経験人数
  managementPeopleNum: string;
  // 直近企業の勤務先企業名
  companyName: string;
  // 直近企業の経験業種
  industrySmallID: MasterType;
  // 直近企業の従業員数
  employeeNum: string;
  // 直近企業の雇用形態
  employmentType: string;
  // 直近企業の役職
  employmentPost: string;
  // 直近企業の経験職種
  jobTypeSmallID: MasterType;
  // 経験職種の経験年数（直近の企業のみ）
  jobTypeExpTerm: string;
  // 経験職種の経験年数（トータル）
  allCareerJobTypeExpTerm: string;
  // 直近企業の年収
  income: string;
  // 直近企業の入社年月
  joinYear: string;
  joinMonth: string;
  // 直近企業の退職年月
  retireYear: string;
  retireMonth: string;
  // 面談応募・登録エラー
  applyErrors: FieldError[];
}

export interface Will {
  // 希望年収
  willIncome: string;
  // 希望勤務地.市区町村
  willWorkAddresses: Address[];
  // フルリモートワーク
  willRemoteWork: boolean;
  // 転職希望時期
  willJobChangePeriod: string;
  // 希望職種.職種小
  willJobTypes: MasterType[];
  // TEL同意
  isRpoAgreement: boolean;
  // 面談応募・登録エラー
  applyErrors: FieldError[];
}

interface ProfileState {
  // 応募したポジション
  appliedPositions: string[];
  // 保持済みプロフィール取得済みフラグ
  savedProfileRetrieved: boolean;
  // 基本情報
  basicInfo: BasicInfo;
  // 学歴
  education: Education;
  // 職歴
  career: Career;
  // 希望条件
  will: Will;
}

const initialState: ProfileState = {
  appliedPositions: [],
  savedProfileRetrieved: false,
  basicInfo: {
    lastName: "",
    firstName: "",
    lastNameKana: "",
    firstNameKana: "",
    email: "",
    phoneNo: "",
    gender: "",
    password: "",
    birthYear: "",
    birthMonth: "",
    prefecture: {
      ID: 0,
      Name: "",
    },
    city: {
      ID: 0,
      Name: "",
    },
    firstLanguage: "",
    driverLicence: "",
    applyErrors: [],
  },
  education: {
    schoolType: "",
    schoolName: "",
    department: {
      ID: 0,
      Name: "",
    },
    professionalTrainingCollegeCategory: {
      ID: 0,
      Name: "",
    },
    graduationYear: "",
    englishLevel: "",
    applyErrors: [],
  },
  career: {
    expCompanyNum: "",
    managementExpTerm: "",
    managementPeopleNum: "",
    companyName: "",
    industrySmallID: {
      ID: 0,
      Name: "",
    },
    employeeNum: "",
    employmentType: "",
    employmentPost: "",
    jobTypeSmallID: {
      ID: 0,
      Name: "",
    },
    jobTypeExpTerm: "",
    allCareerJobTypeExpTerm: "",
    income: "",
    joinYear: "",
    joinMonth: "",
    retireYear: "",
    retireMonth: "",
    applyErrors: [],
  },
  will: {
    willIncome: "",
    willWorkAddresses: [],
    willRemoteWork: true,
    willJobChangePeriod: "",
    willJobTypes: [],
    isRpoAgreement: true,
    applyErrors: [],
  },
};

const profileSlice = createSlice({
  name: "profile",
  initialState,
  reducers: {
    addAppliedPosition: (state, action: PayloadAction<string>) => {
      state.appliedPositions.push(action.payload);
    },
    updateAppliedPositions: (state, action: PayloadAction<string[]>) => {
      state.appliedPositions = [...state.appliedPositions, ...action.payload];
    },
    markSavedProfileRetrieved: (state) => {
      state.savedProfileRetrieved = true;
    },
    updateBasicInfo: (state, action: PayloadAction<Partial<BasicInfo>>) => {
      state.basicInfo = {
        ...state.basicInfo,
        ...action.payload,
      };
    },
    updateBasicInfoAddress: (state, action: PayloadAction<Address>) => {
      state.basicInfo.prefecture = action.payload.prefecture;
      state.basicInfo.city = action.payload.city;
    },
    updateBasicInfoApplyErrors: (
      state,
      action: PayloadAction<FieldError[]>,
    ) => {
      state.basicInfo.applyErrors = action.payload;
    },
    updateEducation: (state, action: PayloadAction<Education>) => {
      state.education = {
        ...state.education,
        ...action.payload,
      };
    },
    updateEducationApplyErrors: (
      state,
      action: PayloadAction<FieldError[]>,
    ) => {
      state.education.applyErrors = action.payload;
    },
    updateCareer: (state, action: PayloadAction<Career>) => {
      state.career = {
        ...state.career,
        ...action.payload,
      };
    },
    updateCareerApplyErrors: (state, action: PayloadAction<FieldError[]>) => {
      state.career.applyErrors = action.payload;
    },
    updateWill: (state, action: PayloadAction<Will>) => {
      state.will = {
        ...state.will,
        ...action.payload,
      };
    },
    updateWillApplyErrors: (state, action: PayloadAction<FieldError[]>) => {
      state.will.applyErrors = action.payload;
    },
  },
});

export const {
  addAppliedPosition,
  updateAppliedPositions,
  markSavedProfileRetrieved,
  updateBasicInfo,
  updateBasicInfoAddress,
  updateBasicInfoApplyErrors,
  updateEducation,
  updateEducationApplyErrors,
  updateCareer,
  updateCareerApplyErrors,
  updateWill,
  updateWillApplyErrors,
} = profileSlice.actions;
export default profileSlice.reducer;
