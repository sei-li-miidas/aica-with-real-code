import PropTypes from "prop-types";

import { TRAITS } from "@/constants/companies";
import { TRAITS as BUSINESS_TRAITS } from "@/constants/business";

import TraitList from "@/components/positions/detail/parts/trait/TraitList";
import TraitListItem from "@/components/positions/detail/parts/trait/TraitListItem";
import ContentList from "@/components/positions/detail/parts/trait/ContentList";
import ContentListItem from "@/components/positions/detail/parts/trait/ContentListItem";

import styles from "./EmployeeAttributes.module.scss";

/**
 * 「求人の特徴」 > 「社員属性」
 */
export default function EmployeeAttributes({
  companyImtRecord,
  businessImtRecord,
}) {
  const employeeAverageAge = renderBusinessItem(
    businessImtRecord.get("EmployeeAverageAge"),
  );

  const employeeMidCareerRate = renderBusinessItem(
    businessImtRecord.get("EmployeeMidCareerRate"),
  );

  const employeeWomanRate = renderBusinessItem(
    businessImtRecord.get("EmployeeWomanRate"),
  );

  const employeeWomanManagerRate =
    renderEmployeeWomanManagerRate(companyImtRecord);

  const employee20sManagerRate = renderEmployee20sManagerRate(companyImtRecord);

  const employeeForeignNationalityRate =
    renderEmployeeForeignNationalityRate(businessImtRecord);

  return (
    <TraitList>
      <TraitListItem
        itemKey={BUSINESS_TRAITS.BTX_EMPLOYEE_AVERAGE_AGE.ID}
        itemName="平均年齢"
        content={employeeAverageAge}
      />
      <TraitListItem
        itemKey={BUSINESS_TRAITS.BTX_EMPLOYEE_MID_CAREER_RATE.ID}
        itemName="中途入社社員比率"
        content={employeeMidCareerRate}
      />
      <TraitListItem
        itemKey={BUSINESS_TRAITS.BTX_EMPLOYEE_WOMAN_RATE.ID}
        itemName="女性社員比率"
        content={employeeWomanRate}
      />
      <TraitListItem
        itemKey={TRAITS.CTX_HR_EVALUATION__WOMAN_MANAGER_RATE.ID}
        itemName="女性管理職比率"
        content={employeeWomanManagerRate}
      />
      <TraitListItem
        itemKey={TRAITS.CTX_HR_EVALUATION__20S_MANAGER_RATE.ID}
        itemName="20代管理職"
        content={employee20sManagerRate}
      />
      <TraitListItem
        itemKey={BUSINESS_TRAITS.BTX_EMPLOYEE_FOREIGN_NATIONALITY_RATE.ID}
        itemName="外国籍社員比率"
        content={employeeForeignNationalityRate}
      />
    </TraitList>
  );
}

EmployeeAttributes.propTypes = {
  companyImtRecord: PropTypes.object.isRequired,
  businessImtRecord: PropTypes.object.isRequired,
};

/**
 * 事業項目の内容を返す
 */
function renderBusinessItem(traitImtRecord) {
  if (!traitImtRecord) return null;

  return (
    <ContentList>
      <ContentListItem traitImtRecord={traitImtRecord} />
    </ContentList>
  );
}

/**
 * 「女性管理職比率」の内容
 */
function renderEmployeeWomanManagerRate(companyImtRecord) {
  const masterImtRecord = companyImtRecord?.get("HREvaluationWomanManagerRate");

  if (!masterImtRecord) {
    return null;
  }

  return (
    <ContentList>
      <ContentListItem traitImtRecord={masterImtRecord} />
    </ContentList>
  );
}

/**
 * 「20代管理職」の内容
 */
function renderEmployee20sManagerRate(companyImtRecord) {
  const masterImtRecord = companyImtRecord?.get("HREvaluation20sManagerRate");

  if (!masterImtRecord) {
    return null;
  }

  return (
    <ContentList>
      <ContentListItem traitImtRecord={masterImtRecord} />
    </ContentList>
  );
}

/**
 * 「外国籍社員比率」欄の内容
 */
function renderEmployeeForeignNationalityRate(businessImtRecord) {
  const traitImtRecord = businessImtRecord.get(
    "EmployeeForeignNationalityRate",
  );
  if (!traitImtRecord) return null;

  const labelModifier = (label) => {
    const foreignNationalityRecruiting = renderForeignNationalityRecruiting(
      businessImtRecord.get("ForeignNationalityRecruiting"),
    );

    return (
      <>
        {label}
        {foreignNationalityRecruiting}
      </>
    );
  };

  return (
    <ContentList>
      <ContentListItem
        traitImtRecord={traitImtRecord}
        labelModifier={labelModifier}
      />
    </ContentList>
  );
}

/**
 * 「外国籍社員積極採用」
 */
function renderForeignNationalityRecruiting(foreignNationalityRecruiting) {
  // トレイト値がないか、外国籍社員積極採用をしていない場合は描画しない
  // NOTE: 外国籍社員積極採用をしていない場合について
  // 企業側で1度もチェックされていない場合の値は null
  // チェックしたあとにチェックを外した場合の値は false
  if (!foreignNationalityRecruiting) {
    return null;
  }

  return (
    <div className={styles.foreignNationalityRecruitingLabel}>
      外国籍社員積極採用
    </div>
  );
}
