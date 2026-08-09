import { Record, List, Map } from "immutable";
import OriginalDocumentRecord from "@/models/company/records/OriginalDocument";
import { type RecordConstructorParameter } from "@/types/utility-types";
import TraitRecord from "@/models/position/records/Trait";
import MasterV2Record from "@/models/records/MasterV2";

import TrainingSystemRecord from "./TrainingSystem";

import JobRotationRecord from "./JobRotation";
import ChangeDepartmentRecord from "./ChangeDepartment";
import CapitalTypeRecord from "./CapitalType";
import AppealPointRecord from "./AppealPoint";
import OtherRecord from "./Other";

type Props = {
  /** 企業ID */
  ID: number | null;
  /** 企業名 */
  Name: string;
  /** 所在地 */
  Address: string;
  /** オリジナル資料一覧 */
  OriginalDocuments: List<OriginalDocumentRecord>;
  /** 事業名一覧 */
  BusinessNames: List<string>;
  /** HP応募しているか */
  IsPartnerApplied: boolean;
  /** 企業概要-法人種別(旧 ctx_is_profit_company) */
  ProfitCompany: TraitRecord | null;
  /** 企業概要-従業員数(旧 ctx_employee_qty) */
  EmployeeQty: TraitRecord | null;
  /** 企業概要-設立(旧 ctx_years_of_establishment) */
  EstablishmentYear: TraitRecord | null;
  /** 企業概要-資本区分(旧 ctx_capital_type) */
  CapitalType: CapitalTypeRecord | null;
  /** 企業概要-売上規模(旧 ctx_sales_scale) */
  SalesScale: TraitRecord | null;
  /** 企業概要代表者名(旧 ctx_president_name) */
  PresidentName: string;
  /** 企業概要HP(旧 ctx_website) */
  Website: string;
  /** 企業概要簡易企業紹介文(旧 ctx_introduction) */
  Introduction: string;
  /** 企業概要-当社のアピールポイント(旧 ctx_appeal_point) */
  AppealPoint: AppealPointRecord | null;
  /** 事業概要-海外売上比率(旧 ctx_sales_overseas_rate) */
  SalesOverseasRate: TraitRecord | null;
  /** 待遇-福利厚生（待遇編）(旧 ctx_welfare__benefit) */
  WelfareBenefit: Map<string, List<TraitRecord> | List<MasterV2Record>>;
  /** 休日休暇-年間休日(旧 ctx_year_holidays) */
  YearHolidays: TraitRecord | null;
  /** 副業(旧 ctx_side_business) */
  SideBusiness: TraitRecord | null;
  /** 副業条件(旧 ctx_side_business_condition) */
  SideBusinessCondition: string;
  /** 休日休暇-福利厚生（休日休暇編）(旧 ctx_vacations) */
  Vacations: Map<string, List<TraitRecord> | List<MasterV2Record>>;
  /** 休日休暇-有給休暇取得率(旧 ctx_paid_holiday_use_rate) */
  PaidHolidayUseRate: TraitRecord | null;
  /** キャリア-研修制度 */
  TrainingSystem: TrainingSystemRecord | null;
  /** キャリア-ジョブローテーション(旧 ctx_job_rotation_exists) */
  JobRotationExists: JobRotationRecord | null;
  /** キャリア-異動希望申請制度(旧 ctx_change_department_request) */
  ChangeDepartmentRequest: ChangeDepartmentRecord | null;
  // Map<string,Map<string,string>|string>;
  /** 人事評価-人事評価実績_女性管理職比率(旧 ctx_hr_evaluation__woman_manager_rate) */
  HREvaluationWomanManagerRate: TraitRecord | null;
  /** 人事評価-人事評価実績_20代管理職(旧 ctx_hr_evaluation__20s_manager_rate) */
  HREvaluation20sManagerRate: TraitRecord | null;
  /** 福利厚生-社会保険 */
  WelfareInsurance: Map<string, List<TraitRecord> | List<MasterV2Record>>;
  /** 福利厚生-実績のある福利厚生(旧 ctx_welfare__achievement) */
  WelfareAchievement: Map<string, List<TraitRecord> | List<MasterV2Record>>;
  /** 福利厚生-人気の福利厚生(旧 ctx_welfare__popular) */
  WelfarePopular: Map<string, List<TraitRecord> | List<MasterV2Record>>;
  /** 福利厚生-その他福利厚生(旧 ctx_welfare__other) */
  WelfareOther: Map<string, List<TraitRecord> | List<MasterV2Record>>;
  /** その他企業特徴(旧 ctx_other) */
  Other: OtherRecord | null;
  /** 企業PRスペース(旧 ctx_pr) */
  PR: string;
  /** 健康経営宣言 */
  HPMCompanyDeclaration: string;
  /** 健康経営優良法人認定マークの表示年（※期限になった場合はnullになる） */
  HPMCertificationDisplayYear: number | null;
  /** はたらく人ファースト宣言をしているか否か */
  IsAgreedHatarakuhitoFirst: boolean;
};

/**
 * ApplyCompany
 * Apply仕様の企業のレコード
 */
export default class ApplyCompany extends Record<Props>({
  ID: null,
  Name: "",
  Address: "",
  OriginalDocuments: List([]),
  BusinessNames: List([]),
  IsPartnerApplied: false,
  ProfitCompany: null,
  EmployeeQty: null,
  EstablishmentYear: null,
  CapitalType: null,
  SalesScale: null,
  PresidentName: "",
  Website: "",
  Introduction: "",
  AppealPoint: null,
  SalesOverseasRate: null,
  WelfareBenefit: Map({
    ValueTexts: List([]),
    Options: List([]),
  }),
  YearHolidays: null,
  SideBusiness: null,
  SideBusinessCondition: "",
  Vacations: Map({
    ValueTexts: List([]),
    Options: List([]),
  }),
  PaidHolidayUseRate: null,
  TrainingSystem: null,
  JobRotationExists: null,
  ChangeDepartmentRequest: null,
  HREvaluationWomanManagerRate: null,
  HREvaluation20sManagerRate: null,
  WelfareInsurance: Map({
    ValueTexts: List([]),
    Options: List([]),
  }),
  WelfareAchievement: Map({
    ValueTexts: List([]),
    Options: List([]),
  }),
  WelfarePopular: Map({
    ValueTexts: List([]),
    Options: List([]),
  }),
  WelfareOther: Map({
    ValueTexts: List([]),
    Options: List([]),
  }),
  Other: null,
  PR: "",
  HPMCompanyDeclaration: "",
  HPMCertificationDisplayYear: null,
  IsAgreedHatarakuhitoFirst: false,
}) {
  constructor(
    company: RecordConstructorParameter<ApplyCompany> & {
      OriginalFiles?: RecordConstructorParameter<ApplyCompany>["OriginalDocuments"];
    },
  ) {
    const {
      OriginalFiles = [],
      BusinessNames = [],
      ProfitCompany,
      EmployeeQty,
      EstablishmentYear,
      SalesScale,
      SalesOverseasRate,
      YearHolidays,
      SideBusiness,
      PaidHolidayUseRate,
      HREvaluationWomanManagerRate,
      HREvaluation20sManagerRate,
      TrainingSystem,
      WelfareBenefit,
      JobRotationExists,
      ChangeDepartmentRequest,
      Vacations,
      WelfareInsurance,
      WelfarePopular,
      WelfareAchievement,
      WelfareOther,
      CapitalType,
      AppealPoint,
      Other,
    } = company;

    // @ts-expect-error: 型エラーが起きないよう後で修正する
    const originalDocuments = OriginalFiles.map(
      // @ts-expect-error: 型エラーが起きないよう後で修正する
      (originalDocument) => new OriginalDocumentRecord(originalDocument),
    );

    super({
      ...company,
      OriginalDocuments: List(originalDocuments),
      // @ts-expect-error: 型エラーが起きないよう後で修正する
      BusinessNames: List(BusinessNames),
      ProfitCompany: ProfitCompany ? new TraitRecord(ProfitCompany) : null,
      EmployeeQty: EmployeeQty ? new TraitRecord(EmployeeQty) : null,
      EstablishmentYear: EstablishmentYear
        ? new TraitRecord(EstablishmentYear)
        : null,
      SalesScale: SalesScale ? new TraitRecord(SalesScale) : null,
      SalesOverseasRate: SalesOverseasRate
        ? new TraitRecord(SalesOverseasRate)
        : null,
      YearHolidays: YearHolidays ? new TraitRecord(YearHolidays) : null,
      SideBusiness: SideBusiness ? new TraitRecord(SideBusiness) : null,
      PaidHolidayUseRate: PaidHolidayUseRate
        ? new TraitRecord(PaidHolidayUseRate)
        : null,
      HREvaluationWomanManagerRate: HREvaluationWomanManagerRate
        ? new TraitRecord(HREvaluationWomanManagerRate)
        : null,
      HREvaluation20sManagerRate: HREvaluation20sManagerRate
        ? new TraitRecord(HREvaluation20sManagerRate)
        : null,
      TrainingSystem: TrainingSystem
        ? new TrainingSystemRecord({
            // @ts-expect-error: 型エラーが起きないよう後で修正する
            Exists: TrainingSystem?.Exists,
            // @ts-expect-error: 型エラーが起きないよう後で修正する
            Text: TrainingSystem?.Text,
          })
        : null,
      // @ts-expect-error: 型エラーが起きないよう後で修正する
      WelfareBenefit: Map({
        ValueTexts: List(
          // @ts-expect-error: 型エラーが起きないよう後で修正する
          (WelfareBenefit?.ValueTexts || []).map(
            // @ts-expect-error: 型エラーが起きないよう後で修正する
            (value) => new TraitRecord(value),
          ),
        ),
        Options: List(
          // @ts-expect-error: 型エラーが起きないよう後で修正する
          (WelfareBenefit?.Options || []).map(
            // @ts-expect-error: 型エラーが起きないよう後で修正する
            (value) => new MasterV2Record(value),
          ),
        ),
      }),
      JobRotationExists: JobRotationExists
        ? new JobRotationRecord({
            // @ts-expect-error: 型エラーが起きないよう後で修正する
            Note: JobRotationExists.Note,
            // @ts-expect-error: 型エラーが起きないよう後で修正する
            Flg: JobRotationExists.Flg,
          })
        : null,
      ChangeDepartmentRequest: ChangeDepartmentRequest
        ? new ChangeDepartmentRecord({
            // @ts-expect-error: 型エラーが起きないよう後で修正する
            Note: ChangeDepartmentRequest.Note,
            // @ts-expect-error: 型エラーが起きないよう後で修正する
            Flg: ChangeDepartmentRequest.Flg,
          })
        : null,
      // @ts-expect-error: 型エラーが起きないよう後で修正する
      Vacations: Map({
        ValueTexts: List(
          // @ts-expect-error: 型エラーが起きないよう後で修正する
          (Vacations?.ValueTexts || []).map((value) => new TraitRecord(value)),
        ),
        Options: List(
          // @ts-expect-error: 型エラーが起きないよう後で修正する
          (Vacations?.Options || []).map((value) => new MasterV2Record(value)),
        ),
      }),
      // @ts-expect-error: 型エラーが起きないよう後で修正する
      WelfareInsurance: Map({
        ValueTexts: List(
          // @ts-expect-error: 型エラーが起きないよう後で修正する
          (WelfareInsurance?.ValueTexts || []).map(
            // @ts-expect-error: 型エラーが起きないよう後で修正する
            (value) => new TraitRecord(value),
          ),
        ),
        Options: List(
          // @ts-expect-error: 型エラーが起きないよう後で修正する
          (WelfareInsurance?.Options || []).map(
            // @ts-expect-error: 型エラーが起きないよう後で修正する
            (value) => new MasterV2Record(value),
          ),
        ),
      }),
      // @ts-expect-error: 型エラーが起きないよう後で修正する
      WelfarePopular: Map({
        ValueTexts: List(
          // @ts-expect-error: 型エラーが起きないよう後で修正する
          (WelfarePopular?.ValueTexts || []).map(
            // @ts-expect-error: 型エラーが起きないよう後で修正する
            (value) => new TraitRecord(value),
          ),
        ),
        Options: List(
          // @ts-expect-error: 型エラーが起きないよう後で修正する
          (WelfarePopular?.Options || []).map(
            // @ts-expect-error: 型エラーが起きないよう後で修正する
            (value) => new MasterV2Record(value),
          ),
        ),
      }),
      // @ts-expect-error: 型エラーが起きないよう後で修正する
      WelfareAchievement: Map({
        ValueTexts: List(
          // @ts-expect-error: 型エラーが起きないよう後で修正する
          (WelfareAchievement?.ValueTexts || []).map(
            // @ts-expect-error: 型エラーが起きないよう後で修正する
            (value) => new TraitRecord(value),
          ),
        ),
        Options: List(
          // @ts-expect-error: 型エラーが起きないよう後で修正する
          (WelfareAchievement?.Options || []).map(
            // @ts-expect-error: 型エラーが起きないよう後で修正する
            (value) => new MasterV2Record(value),
          ),
        ),
      }),
      // @ts-expect-error: 型エラーが起きないよう後で修正する
      WelfareOther: Map({
        ValueTexts: List(
          // @ts-expect-error: 型エラーが起きないよう後で修正する
          (WelfareOther?.ValueTexts || []).map(
            // @ts-expect-error: 型エラーが起きないよう後で修正する
            (value) => new TraitRecord(value),
          ),
        ),
        Options: List(
          // @ts-expect-error: 型エラーが起きないよう後で修正する
          (WelfareOther?.Options || []).map(
            // @ts-expect-error: 型エラーが起きないよう後で修正する
            (value) => new MasterV2Record(value),
          ),
        ),
      }),
      CapitalType: CapitalType
        ? new CapitalTypeRecord({
            // @ts-expect-error: 型エラーが起きないよう後で修正する
            Note: CapitalType.Note,
            // @ts-expect-error:  型エラーが起きないよう後で修正する
            IDs: List(CapitalType.IDs.map((ids) => new MasterV2Record(ids))),
            Options: List(
              // @ts-expect-error: 型エラーが起きないよう後で修正する
              CapitalType.Options.map((option) => new MasterV2Record(option)),
            ),
          })
        : null,
      AppealPoint: AppealPoint
        ? new AppealPointRecord({
            // @ts-expect-error: 型エラーが起きないよう後で修正する
            Note: AppealPoint.Note,
            // @ts-expect-error: 型エラーが起きないよう後で修正する
            IDs: List(AppealPoint.IDs.map((ids) => new MasterV2Record(ids))),
            Options: List(
              // @ts-expect-error: 型エラーが起きないよう後で修正する
              AppealPoint.Options.map((option) => new MasterV2Record(option)),
            ),
          })
        : null,
      Other: Other
        ? new OtherRecord({
            // @ts-expect-error: 型エラーが起きないよう後で修正する
            Note: Other.Note,
            // @ts-expect-error: 型エラーが起きないよう後で修正する
            IDs: List(Other.IDs.map((ids) => new MasterV2Record(ids))),
            Options: List(
              // @ts-expect-error: 型エラーが起きないよう後で修正する
              Other.Options.map((option) => new MasterV2Record(option)),
            ),
          })
        : null,
    });
  }

  /**
   * getAddressForDisplay
   * 表示用の住所を返す
   */
  getAddressForDisplay() {
    return `${this.Address || ""}`;
  }

  /**
   * getOriginalDocumentName
   * IDで元のドキュメント名を取得する
   */
  getOriginalDocumentName(originalDocumentId: number) {
    const originalDocument = this.OriginalDocuments.find((itemImtRecord) => {
      return itemImtRecord.ID === originalDocumentId;
    });
    return originalDocument ? originalDocument.Label : "";
  }
}
