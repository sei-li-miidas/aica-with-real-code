import { Record } from "immutable";
import TraitRecord from "@/models/position/records/Trait";
import { type RecordConstructorParameter } from "@/types/utility-types";
import BTIMultipleTraitRecord from "@/models/position/records/business/BTIMultipleTrait";
import BTISingleTraitRecord from "@/models/position/records/business/BTISingleTrait";
import IndustriesRecord from "./Industries";
import EmployeeCharacterRecord from "./EmployeeCharacter";
import DecisionTypeRecord from "./DecisionType";

/**
 * 事業のレコード
 */
export default class Business extends Record<{
  /** 事業ID */
  ID: number | null;
  /** 事業名 */
  Name: string;
  /** 事業の規模(旧 btx_employee_qty) */
  EmployeeQty: TraitRecord | null;
  /** 事業の設立(旧 btx_years_of_establishment) */
  EstablishmentYear: TraitRecord | null;
  /** 事業の売上規模(旧 btx_sales_scale) */
  SalesScale: TraitRecord | null;
  /** 事業内容(旧 btx_business_industry) */
  Industries: IndustriesRecord | null;
  /** 意思決定と裁量(旧 btx_decision_type) */
  DecisionType: DecisionTypeRecord | null;
  /** 平均年齢(旧 btx_employee_average_age) */
  EmployeeAverageAge: TraitRecord | null;
  /** 女性社員比率(旧 btx_employee_woman_rate) */
  EmployeeWomanRate: TraitRecord | null;
  /** 中途入社社員比率(旧 btx_employee_mid_career_rate) */
  EmployeeMidCareerRate: TraitRecord | null;
  /** 外国籍社員積極採用(旧 btx_employee_foreign_nationality_rate) */
  EmployeeForeignNationalityRate: TraitRecord | null;
  /** 組織・社員の特徴(旧 btx_employee_character) */
  EmployeeCharacter: EmployeeCharacterRecord | null;
  /** 外国籍社員積極採用(旧 btx_foreign_nationality_recruiting) */
  ForeignNationalityRecruiting: boolean | null;
  /** 得意領域（メディカル）(旧 bti_medical_advantage_field) */
  MedicalAdvantageField: BTIMultipleTraitRecord | null;
  /** メーカー（自動車部品）Tier (旧 bti_car_parts_tier) */
  CarPartsTier: BTISingleTraitRecord | null;
  /** SI種別 (旧 bti_si__type) */
  SIType: BTISingleTraitRecord | null;
  /** 得意領域（SIer）(旧 bti_si__advantage_industry) */
  SIAdvantageIndustry: BTIMultipleTraitRecord | null;
  /** 主な収益源(旧 bti_contract_company__profit_source) */
  ContractCompanyProfitSource: BTISingleTraitRecord | null;
  /** プロジェクト期間(旧 bti_contract_company__project_term) */
  ContractCompanyProjectTerm: BTISingleTraitRecord | null;
  /** 客先常駐(旧 bti_contract_company__client_resident) */
  ContractCompanyClientResident: BTISingleTraitRecord | null;
  /** 常駐形態(旧 bti_contract_company__resident_type) */
  ContractCompanyResident: BTISingleTraitRecord | null;
}>({
  ID: null,
  Name: "",
  EmployeeQty: null,
  EstablishmentYear: null,
  SalesScale: null,
  Industries: null,
  DecisionType: null,
  EmployeeAverageAge: null,
  EmployeeWomanRate: null,
  EmployeeMidCareerRate: null,
  EmployeeForeignNationalityRate: null,
  EmployeeCharacter: null,
  ForeignNationalityRecruiting: null,
  MedicalAdvantageField: null,
  CarPartsTier: null,
  SIType: null,
  SIAdvantageIndustry: null,
  ContractCompanyProfitSource: null,
  ContractCompanyProjectTerm: null,
  ContractCompanyClientResident: null,
  ContractCompanyResident: null,
}) {
  constructor(business: RecordConstructorParameter<Business>) {
    const {
      EmployeeQty: employeeQty,
      EstablishmentYear: establishmentYear,
      SalesScale: salesScale,
      Industries: industries,
      DecisionType: decisionType,
      EmployeeAverageAge: employeeAverageAge,
      EmployeeWomanRate: employeeWomanRate,
      EmployeeMidCareerRate: employeeMidCareerRate,
      EmployeeForeignNationalityRate: employeeForeignNationalityRate,
      EmployeeCharacter: employeeCharacter,
      MedicalAdvantageField: medicalAdvantageField,
      CarPartsTier: carPartsTier,
      SIType: siType,
      SIAdvantageIndustry: siAdvantageIndustry,
      ContractCompanyProfitSource: contractCompanyProfitSource,
      ContractCompanyProjectTerm: contractCompanyProjectTerm,
      ContractCompanyClientResident: contractCompanyClientResident,
      ContractCompanyResident: contractCompanyResident,
    } = business;

    super({
      ...business,
      EmployeeQty: employeeQty ? new TraitRecord(employeeQty) : null,
      EstablishmentYear: establishmentYear
        ? new TraitRecord(establishmentYear)
        : null,
      SalesScale: salesScale ? new TraitRecord(salesScale) : null,
      Industries: industries ? new IndustriesRecord(industries) : null,
      DecisionType: decisionType ? new DecisionTypeRecord(decisionType) : null,
      EmployeeAverageAge: employeeAverageAge
        ? new TraitRecord(employeeAverageAge)
        : null,
      EmployeeWomanRate: employeeWomanRate
        ? new TraitRecord(employeeWomanRate)
        : null,
      EmployeeMidCareerRate: employeeMidCareerRate
        ? new TraitRecord(employeeMidCareerRate)
        : null,
      EmployeeForeignNationalityRate: employeeForeignNationalityRate
        ? new TraitRecord(employeeForeignNationalityRate)
        : null,
      EmployeeCharacter: employeeCharacter
        ? new EmployeeCharacterRecord(employeeCharacter)
        : null,
      MedicalAdvantageField: medicalAdvantageField
        ? new BTIMultipleTraitRecord(medicalAdvantageField)
        : null,
      CarPartsTier: carPartsTier
        ? new BTISingleTraitRecord(carPartsTier)
        : null,
      SIType: siType ? new BTISingleTraitRecord(siType) : null,
      SIAdvantageIndustry: siAdvantageIndustry
        ? new BTIMultipleTraitRecord(siAdvantageIndustry)
        : null,
      ContractCompanyProfitSource: contractCompanyProfitSource
        ? new BTISingleTraitRecord(contractCompanyProfitSource)
        : null,
      ContractCompanyProjectTerm: contractCompanyProjectTerm
        ? new BTISingleTraitRecord(contractCompanyProjectTerm)
        : null,
      ContractCompanyClientResident: contractCompanyClientResident
        ? new BTISingleTraitRecord(contractCompanyClientResident)
        : null,
      ContractCompanyResident: contractCompanyResident
        ? new BTISingleTraitRecord(contractCompanyResident)
        : null,
    });
  }
}
