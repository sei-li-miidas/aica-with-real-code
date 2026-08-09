import { Record, List } from "immutable";
import { TRAIT_EMPLOYMENT_TYPE } from "@/constants/position";
import HrEvaluationTypeRecord from "@/models/position/records/HrEvaluationType";
import HrEvaluationCompetencyRecord from "@/models/position/records/HrEvaluationCompetency";
import JobRecord from "@/models/position/records/Job";
import ModelAnnualIncomeRecord from "@/models/position/records/ModelAnnualIncome";
import WorkAddressRecord from "@/models/position/records/WorkAddress";
import RegularOutsourcingRecord from "@/models/position/records/RegularOutsourcing";
import SpotOutsourcingRecord from "@/models/position/records/SpotOutsourcing";
import OvertimeSalaryRecord from "@/models/position/records/OvertimeSalary";
import ITEngineerWorkEnvironmentRecord from "@/models/position/records/ITEngineerWorkEnvironment";
import JobChangeRecord from "@/models/position/records/JobChange";
import OutsourcingAppealRecord from "@/models/position/records/OutsourcingAppeal";
import PositionImageRecord from "@/models/position/records/PositionImage";
import InterviewRecord from "@/models/records/Interview";
import { INCOME_FROM_TYPE } from "@/constants/offers/offerIncome";
import CommissionOutsourcingRecord from "@/models/offers/outsourcing/commission/records/CommissionOutsourcing";
import AppealPointTagRecord from "@/models/offers/records/AppealPointTag";
import BossTypeRecord from "@/models/records/BossType";
import TraitRecord from "@/models/position/records/Trait";
import TraitWithOptionsRecord from "@/models/records/TraitWithOptions";
import SpotExpLevelRecord from "@/models/records/SpotExpLevel";
import SpotJobRequestRecord from "@/models/records/SpotJobRequest";
import TraitEmploymentTypeRecord from "@/models/position/records/TraitEmploymentType";

import { type RecordConstructorParameter } from "@/types/utility-types";

type Props = {
  /** 求人ID */
  ID: number | null;
  /** 求人と紐づく企業ID */
  CompanyID: number | null;
  /** 部門ID */
  CompanySectionID: number | null;
  /** 事業ID */
  BusinessID: number | null;
  /** 詳細表示可否 */
  IsDetailShowable: boolean;
  /** 認定情報 */
  CertificationRank: number | null;
  /** 上司との相性一覧 */
  BossTypeScores: List<BossTypeRecord>;
  /** プレビュー用求人詳細 */
  PreviewCompanyName: string;
  /** 求人名（公開用） (旧 ptx_title) */
  Title: string | null;
  /** 役職 (旧 ptx_post) */
  Post: TraitRecord | null;
  /** 契約形態種別 (旧 ptx_employment_type) */
  EmploymentType: TraitEmploymentTypeRecord | null;
  /** 仕事内容 (旧 ptx_job) */
  Jobs: List<JobRecord>;
  /** 仕事内容(メイン) (旧 ptx_job_text) */
  MainJobText: string | null;
  /** 確約年収 (旧 ptx_guaranteed_income) 求人受信時は求人年収、未受信の場合はnull */
  JobChange: JobChangeRecord | null;
  /** モデル年収 (旧 ptx_model_annual_income) */
  ModelAnnualIncome: ModelAnnualIncomeRecord | null;
  /** 基本月給 (旧 pte_base_monthly_salary) */
  BaseMonthlySalary: TraitRecord | null;
  /** 固定残業代 */
  OvertimeSalary: OvertimeSalaryRecord | null;
  /** 賞与 (旧 ptx_bonus_count) */
  BonusCount: TraitRecord | null;
  /** 昇給・昇格 (旧 ptx_promotion_count) */
  PromotionCount: TraitRecord | null;
  /** ストックオプション (旧 ptx_stock_option) */
  StockOption: TraitRecord | null;
  /** 勤務地都道府県 (旧 ptx_work_address) */
  WorkAddress: WorkAddressRecord | null;
  /** リモート勤務 (旧 ptx_remote_work) */
  RemoteWork: TraitRecord | null;
  /** リモート勤務条件 (旧 ptx_remote_work_condition) */
  RemoteWorkCondition: string | null;
  /** リモート勤務出社頻度 (旧 ptx_remote_work_office_frequency) */
  RemoteWorkOfficeFrequency: TraitRecord | null;
  /** 休日 (旧 ptx_holiday) */
  Holiday: TraitRecord | null;
  /** 勤務時間テキスト (旧 ptx_worktime_text) */
  WorkTime: string | null;
  /** 勤務時間 (旧 ptx_worktime) */
  WorkTimeSystem: TraitRecord | null;
  /** 勤務時間夜勤の有無 (旧 ptx_worktime_night_shift) */
  WorkTimeNightsShift: TraitRecord | null;
  /** 労働環境平均残業時間 (旧 ptx_overtime_avg) */
  OvertimeAvg: TraitRecord | null;
  /** 労働環境出張頻度 (旧 ptx_official_trip_frequency) */
  OfficialTripFrequency: TraitRecord | null;
  /** 労働環境労働環境の特徴 (旧 ptx_working_environment) */
  WorkEnvironment: List<TraitRecord>;
  /** キャリア国内転勤の有無 (旧 ptx_transference_exists) */
  TransferenceExists: TraitRecord | null;
  /** キャリア国内転勤の有無国内転勤の頻度 (旧 ptx_transference_frequency) */
  TransferenceFrequency: TraitRecord | null;
  /** キャリア海外転勤 (旧 ptx_transference_abroad_exists) */
  TransferenceAbroadExists: TraitRecord | null;
  /** キャリア海外転勤英語力不問 (旧 ptx_transference_abroad_english_is_unused) */
  TransferenceAbroadEnglishIsUnused: TraitRecord | null;
  /** 人事評価評価基準の特徴 (旧 ptx_hr_evaluation_type) */
  HREvaluationType: HrEvaluationTypeRecord | null;
  /** 人事評価特に評価されるコンピテンシー (旧 ptx_hr_evaluation__competency) */
  HREvaluationCompetency: HrEvaluationCompetencyRecord | null;
  /** その他求人PR (旧 ptx_pr) */
  PR: string;
  /** 受動喫煙対策 */
  SmokeFree: TraitRecord | null;
  /** 受動喫煙対策（具体的な対策） */
  SmokeFreeEnvironment: TraitRecord | null;
  /** 求人特徴業績目標達成者率 (旧 ptj_accomplishment_rate) */
  AccomplishmentRate: TraitRecord | null;
  /** 求人特徴営業スタイル新規飛び込み (旧 ptj_sales_style__dive) */
  SalesStyleDive: TraitRecord | null;
  /** 求人特徴営業スタイル新規テレアポ (旧 ptj_sales_style__tel_appointment) */
  SalesStyleTelAppointment: TraitRecord | null;
  /** 求人特徴営業スタイル接待 (旧 ptj_sales_style__host) */
  SalesStyleHost: TraitRecord | null;
  /** 求人特徴キャリアパス1 (旧 ptj_career_path__out_of_site_exists) */
  CareerPathOutOfSiteExists: TraitRecord | null;
  /** 求人特徴キャリアパス2 (旧 ptj_career_path__work_head_office_exists) */
  CareerPathWorkHeadOfficeExists: TraitRecord | null;
  /** 求人特徴組織1 (旧 ptj_org_trend__engineer_manager_exists) */
  OrgTrendEngineerManagerExists: TraitRecord | null;
  /** 求人特徴組織2 (旧 ptj_org_trend__section_member_qty) */
  OrgTrendSectionMemberQty: TraitRecord | null;
  /** 求人特徴組織3 (旧 ptj_org_trend__accounting_licence_exists) */
  OrgTrendAccountingLicenceExists: TraitRecord | null;
  /** 求人特徴組織4 (旧 ptj_org_trend__legal_licence_exists) */
  OrgTrendLegalLicenceExists: TraitRecord | null;
  /** 求人特徴組織5 (旧 ptj_org_trend__related_with_engineer) */
  OrgTrendRelatedWithEngineer: TraitRecord | null;
  /** 求人特徴労働環境 (旧 ptj_work_environment) */
  ITEngineerWorkEnvironment: ITEngineerWorkEnvironmentRecord | null;
  /** 求人特徴開発スパン (旧 ptj_development_term) */
  DevelopmentTerm: TraitRecord | null;
  /** 求人特徴開発手法 (旧 ptj_development_process) */
  DevelopmentProcess: TraitWithOptionsRecord | null;
  /** 求人特徴緊急対応 (旧 ptj_emergency_support) */
  EmergencySupport: TraitRecord | null;
  /** 入社支度金 (旧 pte_joined_reserve) */
  JoinedReserve: number | null;
  /** 契約形態契約社員 (旧 pte_employment_to_regular_employee) */
  EmploymentToRegularEmployee: TraitRecord | null;
  /** 求人特徴試用期間 (旧 pte_probation) */
  Probation: TraitRecord | null;
  /** 求人特徴契約期間 (旧 pte_contract_period) */
  ContractPeriod: TraitRecord | null;
  /** 契約社員求人: 契約更新 */
  ContractRenewal: TraitRecord | null;
  /** 契約社員求人: 契約更新の詳細 */
  ContractRenewalText: string | null;
  /** レギュラー求人: 契約延長 (旧 pte_contract_extension) */
  ContractExtension: TraitRecord | null;
  /** 業務委託（レギュラー） (旧 pte_regular_outsourcing) */
  RegularOutsourcing: RegularOutsourcingRecord | null;
  /** 業務委託（スポット） (旧 pte_spot_outsourcing) */
  SpotOutsourcing: SpotOutsourcingRecord | null;
  /** 業務委託（スポット）依頼内容詳細 (旧 pte_spot_job_description) */
  SpotJobDescription: string | null;
  /** 業務委託求人・完全歩合制の求人情報 */
  CommissionOutsourcing: CommissionOutsourcingRecord | null;
  /** 業務委託求人のアピールポイント */
  OutsourcingAppeal: OutsourcingAppealRecord | null;
  /** 求人画像 */
  Images: List<PositionImageRecord>;
  /** 求人の最終更新日時 */
  Modified: string | null;
  /** 面接情報 */
  Interview: InterviewRecord;
  /** スポット依頼内容 */
  SpotJobRequest: SpotJobRequestRecord | null;
  /** スポット応募時の熟練度回答の複数選択肢 */
  SpotExpLevels: List<SpotExpLevelRecord>;
  /** 企業が求人をゴミ箱に入れた日時 */
  CompanyTrashedAt: string | null;
  /** 下限年収の提示方法タイプ */
  IncomeFromType: number | null;
  /** 公開ステータス。0:非公開, 1: 公開 */
  PublishStatus: number;
  /** アピールポイントタグ */
  Tags: List<AppealPointTagRecord>;
};

/**
 * Position
 * 求人のレコード
 */
export default class Position extends Record<Props>({
  ID: null,
  CompanyID: null,
  CompanySectionID: null,
  BusinessID: null,
  IsDetailShowable: false,
  CertificationRank: null,
  BossTypeScores: List([]),
  PreviewCompanyName: "",
  Title: null,
  Post: null,
  EmploymentType: null,
  Jobs: List([]),
  MainJobText: null,
  JobChange: null,
  ModelAnnualIncome: null,
  BaseMonthlySalary: null,
  OvertimeSalary: null,
  BonusCount: null,
  PromotionCount: null,
  StockOption: null,
  WorkAddress: null,
  RemoteWork: null,
  RemoteWorkCondition: null,
  RemoteWorkOfficeFrequency: null,
  Holiday: null,
  WorkTime: null,
  WorkTimeSystem: null,
  WorkTimeNightsShift: null,
  OvertimeAvg: null,
  OfficialTripFrequency: null,
  WorkEnvironment: List([]),
  TransferenceExists: null,
  TransferenceFrequency: null,
  TransferenceAbroadExists: null,
  TransferenceAbroadEnglishIsUnused: null,
  HREvaluationType: null,
  HREvaluationCompetency: null,
  PR: "",
  SmokeFree: null,
  SmokeFreeEnvironment: null,
  AccomplishmentRate: null,
  SalesStyleDive: null,
  SalesStyleTelAppointment: null,
  SalesStyleHost: null,
  CareerPathOutOfSiteExists: null,
  CareerPathWorkHeadOfficeExists: null,
  OrgTrendEngineerManagerExists: null,
  OrgTrendSectionMemberQty: null,
  OrgTrendAccountingLicenceExists: null,
  OrgTrendLegalLicenceExists: null,
  OrgTrendRelatedWithEngineer: null,
  ITEngineerWorkEnvironment: null,
  DevelopmentTerm: null,
  DevelopmentProcess: null,
  EmergencySupport: null,
  JoinedReserve: null,
  EmploymentToRegularEmployee: null,
  Probation: null,
  ContractPeriod: null,
  ContractRenewal: null,
  ContractRenewalText: null,
  ContractExtension: null,
  RegularOutsourcing: null,
  SpotOutsourcing: null,
  SpotJobDescription: null,
  CommissionOutsourcing: null,
  OutsourcingAppeal: null,
  Images: List([]),
  Modified: null,
  Interview: new InterviewRecord({}),
  SpotJobRequest: null,
  SpotExpLevels: List([]),
  CompanyTrashedAt: null,
  IncomeFromType: null,
  PublishStatus: 0,
  Tags: List([]),
}) {
  constructor(position: RecordConstructorParameter<Position>) {
    const {
      BossTypeScores,
      Post,
      EmploymentType,
      Jobs,
      JobChange,
      ModelAnnualIncome,
      StockOption,
      BonusCount,
      PromotionCount,
      WorkAddress,
      RemoteWork,
      RemoteWorkOfficeFrequency,
      Holiday,
      WorkTimeSystem,
      WorkTimeNightsShift,
      OvertimeAvg,
      OfficialTripFrequency,
      WorkEnvironment,
      TransferenceExists,
      TransferenceFrequency,
      TransferenceAbroadExists,
      TransferenceAbroadEnglishIsUnused,
      HREvaluationType,
      HREvaluationCompetency,
      SmokeFree,
      SmokeFreeEnvironment,
      AccomplishmentRate,
      SalesStyleDive,
      SalesStyleTelAppointment,
      SalesStyleHost,
      BaseMonthlySalary,
      OvertimeSalary,
      CareerPathOutOfSiteExists,
      CareerPathWorkHeadOfficeExists,
      OrgTrendEngineerManagerExists,
      OrgTrendSectionMemberQty,
      OrgTrendAccountingLicenceExists,
      OrgTrendLegalLicenceExists,
      OrgTrendRelatedWithEngineer,
      ITEngineerWorkEnvironment,
      DevelopmentTerm,
      DevelopmentProcess,
      EmergencySupport,
      EmploymentToRegularEmployee,
      Probation,
      ContractPeriod,
      ContractRenewal,
      ContractExtension,
      RegularOutsourcing,
      SpotOutsourcing,
      CommissionOutsourcing,
      OutsourcingAppeal,
      SpotJobRequest,
      SpotExpLevels,
      Images,
      Interview,
      Tags,
    } = position;

    super({
      ...position,
      BossTypeScores: List(
        // @ts-expect-error: 型エラーが起きないよう後で修正する
        BossTypeScores?.map((value) => new BossTypeRecord(value)),
      ),
      EmploymentType: EmploymentType
        ? new TraitEmploymentTypeRecord(EmploymentType)
        : null,
      Post: Post ? new TraitRecord(Post) : null,
      // @ts-expect-error: 型エラーが起きないよう後で修正する
      Jobs: List(Jobs?.map((job) => new JobRecord(job))),
      JobChange: JobChange ? new JobChangeRecord(JobChange) : null,
      ModelAnnualIncome: ModelAnnualIncome
        ? new ModelAnnualIncomeRecord(ModelAnnualIncome)
        : null,
      StockOption: StockOption ? new TraitRecord(StockOption) : null,
      BonusCount: BonusCount ? new TraitRecord(BonusCount) : null,
      PromotionCount: PromotionCount ? new TraitRecord(PromotionCount) : null,
      WorkAddress: WorkAddress ? new WorkAddressRecord(WorkAddress) : null,
      RemoteWork: RemoteWork ? new TraitRecord(RemoteWork) : null,
      RemoteWorkOfficeFrequency: RemoteWorkOfficeFrequency
        ? new TraitRecord(RemoteWorkOfficeFrequency)
        : null,
      Holiday: Holiday ? new TraitRecord(Holiday) : null,
      WorkTimeSystem: WorkTimeSystem ? new TraitRecord(WorkTimeSystem) : null,
      WorkTimeNightsShift: WorkTimeNightsShift
        ? new TraitRecord(WorkTimeNightsShift)
        : null,
      OvertimeAvg: OvertimeAvg ? new TraitRecord(OvertimeAvg) : null,
      OfficialTripFrequency: OfficialTripFrequency
        ? new TraitRecord(OfficialTripFrequency)
        : null,
      WorkEnvironment: List(
        // @ts-expect-error: 型エラーが起きないよう後で修正する
        WorkEnvironment?.map((value) => new TraitRecord(value)),
      ),
      TransferenceExists: TransferenceExists
        ? new TraitRecord(TransferenceExists)
        : null,
      TransferenceFrequency: TransferenceFrequency
        ? new TraitRecord(TransferenceFrequency)
        : null,
      TransferenceAbroadExists: TransferenceAbroadExists
        ? new TraitRecord(TransferenceAbroadExists)
        : null,
      TransferenceAbroadEnglishIsUnused: TransferenceAbroadEnglishIsUnused
        ? new TraitRecord(TransferenceAbroadEnglishIsUnused)
        : null,
      HREvaluationType: HREvaluationType
        ? new HrEvaluationTypeRecord(HREvaluationType)
        : null,
      HREvaluationCompetency: HREvaluationCompetency
        ? new HrEvaluationCompetencyRecord(HREvaluationCompetency)
        : null,
      SmokeFree: SmokeFree ? new TraitRecord(SmokeFree) : null,
      SmokeFreeEnvironment: SmokeFreeEnvironment
        ? new TraitRecord(SmokeFreeEnvironment)
        : null,
      AccomplishmentRate: AccomplishmentRate
        ? new TraitRecord(AccomplishmentRate)
        : null,
      SalesStyleDive: SalesStyleDive ? new TraitRecord(SalesStyleDive) : null,
      SalesStyleTelAppointment: SalesStyleTelAppointment
        ? new TraitRecord(SalesStyleTelAppointment)
        : null,
      SalesStyleHost: SalesStyleHost ? new TraitRecord(SalesStyleHost) : null,
      BaseMonthlySalary: BaseMonthlySalary
        ? new TraitRecord(BaseMonthlySalary)
        : null,
      OvertimeSalary: OvertimeSalary
        ? new OvertimeSalaryRecord(OvertimeSalary)
        : null,
      CareerPathOutOfSiteExists: CareerPathOutOfSiteExists
        ? new TraitRecord(CareerPathOutOfSiteExists)
        : null,
      CareerPathWorkHeadOfficeExists: CareerPathWorkHeadOfficeExists
        ? new TraitRecord(CareerPathWorkHeadOfficeExists)
        : null,
      OrgTrendEngineerManagerExists: OrgTrendEngineerManagerExists
        ? new TraitRecord(OrgTrendEngineerManagerExists)
        : null,
      OrgTrendSectionMemberQty: OrgTrendSectionMemberQty
        ? new TraitRecord(OrgTrendSectionMemberQty)
        : null,
      OrgTrendAccountingLicenceExists: OrgTrendAccountingLicenceExists
        ? new TraitRecord(OrgTrendAccountingLicenceExists)
        : null,
      OrgTrendLegalLicenceExists: OrgTrendLegalLicenceExists
        ? new TraitRecord(OrgTrendLegalLicenceExists)
        : null,
      OrgTrendRelatedWithEngineer: OrgTrendRelatedWithEngineer
        ? new TraitRecord(OrgTrendRelatedWithEngineer)
        : null,
      ITEngineerWorkEnvironment: ITEngineerWorkEnvironment
        ? new ITEngineerWorkEnvironmentRecord(ITEngineerWorkEnvironment)
        : null,
      DevelopmentTerm: DevelopmentTerm
        ? new TraitRecord(DevelopmentTerm)
        : null,
      DevelopmentProcess: DevelopmentProcess
        ? new TraitWithOptionsRecord(DevelopmentProcess)
        : null,
      EmergencySupport: EmergencySupport
        ? new TraitRecord(EmergencySupport)
        : null,
      EmploymentToRegularEmployee: EmploymentToRegularEmployee
        ? new TraitRecord(EmploymentToRegularEmployee)
        : null,
      Probation: Probation ? new TraitRecord(Probation) : null,
      ContractPeriod: ContractPeriod ? new TraitRecord(ContractPeriod) : null,
      ContractRenewal: ContractRenewal
        ? new TraitRecord(ContractRenewal)
        : null,
      ContractExtension: ContractExtension
        ? new TraitRecord(ContractExtension)
        : null,
      RegularOutsourcing: RegularOutsourcing
        ? new RegularOutsourcingRecord(RegularOutsourcing)
        : null,
      SpotOutsourcing: SpotOutsourcing
        ? new SpotOutsourcingRecord(SpotOutsourcing)
        : null,
      CommissionOutsourcing: CommissionOutsourcing
        ? new CommissionOutsourcingRecord(CommissionOutsourcing)
        : null,
      OutsourcingAppeal: OutsourcingAppeal
        ? new OutsourcingAppealRecord(OutsourcingAppeal)
        : null,
      SpotJobRequest: SpotJobRequest
        ? new SpotJobRequestRecord(SpotJobRequest)
        : null,
      SpotExpLevels: List(
        // @ts-expect-error: 型エラーが起きないよう後で修正する
        SpotExpLevels?.map(
          // @ts-expect-error: 型エラーが起きないよう後で修正する
          (spotExpLevel) => new SpotExpLevelRecord(spotExpLevel),
        ),
      ),
      // @ts-expect-error: 型エラーが起きないよう後で修正する
      Images: List(Images?.map((image) => new PositionImageRecord(image))),
      Interview: new InterviewRecord(Interview || {}),
      // @ts-expect-error: 型エラーが起きないよう後で修正する
      Tags: List(Tags?.map((tag) => new AppealPointTagRecord(tag))),
    });
  }

  /**
   * getMainJobTypeName
   * メインの職種名を返す
   */
  getMainJobTypeName() {
    const jobImtList = this.Jobs;
    return jobImtList.find((jobImtRecord) => {
      return jobImtRecord.Main;
    })?.Name;
  }

  /**
   * getMainJobTypeId
   * メインの職種IDを返す
   */
  getMainJobTypeId() {
    const jobImtList = this.Jobs;
    if (!jobImtList.size) return null;
    return jobImtList.find((jobImtRecord) => {
      return jobImtRecord.Main;
    })?.SmallID;
  }

  /**
   * getSubJobTypes
   * サブの職種レコード一覧を返す
   */
  getSubJobTypes() {
    const jobImtList = this.Jobs;
    return jobImtList.filterNot((jobImtRecord) => {
      return jobImtRecord.Main;
    });
  }

  /**
   * getEmploymentTypeId
   * 契約形態IDを返す
   */
  getEmploymentTypeId() {
    return this.EmploymentType?.ID;
  }

  /**
   * isTraitEmploymentTypeEmployee
   * 契約形態が社員か契約社員かを返す
   */
  isTraitEmploymentTypeEmployee() {
    const employmentTypeId = this.getEmploymentTypeId();
    return (
      employmentTypeId === TRAIT_EMPLOYMENT_TYPE.EMPLOYEE ||
      employmentTypeId === TRAIT_EMPLOYMENT_TYPE.CONTRACT
    );
  }

  /**
   * 契約形態が業務委託（レギュラー）かを返す
   */
  isTraitEmploymentTypeRegularOutsourcing() {
    const employmentTypeId = this.getEmploymentTypeId();
    return employmentTypeId === TRAIT_EMPLOYMENT_TYPE.OUTSOURCING_REGULAR;
  }

  /**
   * 契約形態が業務委託（スポット）かを返す
   */
  isTraitEmploymentTypeSpotOutsourcing() {
    const employmentTypeId = this.getEmploymentTypeId();
    return employmentTypeId === TRAIT_EMPLOYMENT_TYPE.OUTSOURCING_SPOT;
  }

  /**
   * 契約形態が業務委託（完全歩合制）かを返す
   */
  isTraitEmploymentTypeCommissionOutsourcing() {
    const employmentTypeId = this.getEmploymentTypeId();
    return employmentTypeId === TRAIT_EMPLOYMENT_TYPE.OUTSOURCING_COMMISSION;
  }

  /**
   * getMainJobRecord
   * メインの仕事内容レコードを取得する
   */
  getMainJobRecord() {
    return this.Jobs.find((jobImtRecord) => {
      return jobImtRecord.Main;
    });
  }

  /**
   * getSubJobRecords
   * サブの仕事内容レコード一覧を取得する
   */
  getSubJobRecords() {
    return this.Jobs.filter((jobImtRecord) => {
      return !jobImtRecord.Main;
    });
  }

  /**
   * getIncomeFromForPreview
   * プレビュー用確約年収下限の表示値を取得する
   */
  getIncomeFromForPreview() {
    const incomeFromType = this.IncomeFromType;
    switch (incomeFromType) {
      case INCOME_FROM_TYPE.EACH:
        return "[個別で提示した数値が入ります]";
      case INCOME_FROM_TYPE.UNIFORM:
        return this.JobChange?.Income.get("From");
      case INCOME_FROM_TYPE.CURRENT:
        return "[ユーザーの現年収が入ります]";
      case INCOME_FROM_TYPE.DESIRED:
        return "[ユーザーの希望年収が入ります]";
      default:
        return null;
    }
  }

  /**
   * getGuaranteedIncomeDisplayForPreview
   * プレビュー用確約年収の表示値を取得する
   */
  getGuaranteedIncomeDisplayForPreview() {
    const incomeFrom = this.getIncomeFromForPreview();
    const incomeTo = this.JobChange?.Income.get("To");
    // 確約年収を設定する場合は上限値と下限値どちらも必須なのでいずれかがない場合は描画しない
    if (!(incomeFrom && incomeTo)) return null;
    return incomeFrom === incomeTo
      ? `${incomeFrom}万円`
      : `${incomeFrom}～${incomeTo}万円`;
  }

  /**
   * ポジションが質問可能かどうか取得する
   * 2025/03/31 現在、レギュラーのみ質問可能
   */
  canInquiry() {
    return this.isTraitEmploymentTypeRegularOutsourcing();
  }
}
