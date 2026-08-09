import PropTypes from "prop-types";

import { ArrayFinder } from "@/utils/finder";
import {
  POSITION_DETAIL,
  TRAITS,
  MODEL_ANNUAL_INCOME,
} from "@/constants/position";
import { HAS_OVERTIME_SALARY, STOCK_OPTION } from "@/constants/master";

import TraitList from "@/components/positions/detail/parts/trait/TraitList";
import TraitListItem from "@/components/positions/detail/parts/trait/TraitListItem";
import ContentList from "@/components/positions/detail/parts/trait/ContentList";
import ContentListItem from "@/components/positions/detail/parts/trait/ContentListItem";
import ContentHorizontalList from "@/components/positions/detail/parts/trait/ContentHorizontalList";
import NoteModalBtn from "@/components/positions/detail/parts/NoteModalBtn";
import CollapsibleNote from "@/components/positions/detail/parts/CollapsibleNote";

import HelpTooltip from "@/components/utils/HelpTooltip";
import AsteriskedParagraph from "@/components/utils/AsteriskedParagraph";
import SpBr from "@/components/utils/SpBr";

import styles from "./Salary.module.scss";

/**
 * 「給与」
 */
export default function Salary(props) {
  const baseMonthlySalary = renderBaseMonthlySalary(props.positionImtRecord);

  const incomeName = renderIncomeName();
  const income = renderIncome(props.positionImtRecord);

  const bonusCount = renderBonusCount(props.positionImtRecord);

  const promotionCount = renderPromotionCount(props.positionImtRecord);

  const stockOption = renderStockOption(props.positionImtRecord);

  const joinedReserve = renderJoinedReserve(props.positionImtRecord);

  return (
    <TraitList>
      <TraitListItem
        itemKey={TRAITS.PTE_BASE_MONTHLY_SALARY.ID}
        itemName="月給"
        content={baseMonthlySalary}
      />
      <TraitListItem
        itemKey={TRAITS.PTX_GUARANTEED_INCOME.ID}
        itemName={incomeName}
        content={income}
      />
      <TraitListItem
        itemKey={TRAITS.PTX_BONUS_COUNT.ID}
        itemName="賞与"
        content={bonusCount}
      />
      <TraitListItem
        itemKey={TRAITS.PTX_PROMOTION_COUNT.ID}
        itemName="昇給・昇格"
        content={promotionCount}
      />
      <TraitListItem
        itemKey={TRAITS.PTX_STOCK_OPTION.ID}
        itemName="ストックオプション"
        content={stockOption}
      />
      <TraitListItem
        itemKey={TRAITS.PTE_JOINED_RESERVE.ID}
        itemName="入社祝い金"
        content={joinedReserve}
      />
    </TraitList>
  );
}

Salary.propTypes = {
  positionImtRecord: PropTypes.object.isRequired,
};

/**
 * 「月給」
 */
function renderBaseMonthlySalary(positionImtRecord) {
  // 基本月給
  const baseMonthlySalaryMasterImtRecord = positionImtRecord.get(
    POSITION_DETAIL.BASE_MONTHLY_SALARY.ID,
  );

  if (!baseMonthlySalaryMasterImtRecord) return null;

  const value = baseMonthlySalaryMasterImtRecord.get("ID");
  if (!value) return null;

  const noteText = baseMonthlySalaryMasterImtRecord.get("Note");

  // モーダルで表示する補足
  const noteModalBtn = noteText ? (
    <NoteModalBtn contentText={noteText} />
  ) : null;

  // 固定残業代
  const overtimeSalaryImtRecord = positionImtRecord.get(
    POSITION_DETAIL.OVERTIME_SALARY.ID,
  );

  const overtimeSalary = renderOvertimeSalary(overtimeSalaryImtRecord);

  return (
    <>
      {`${value}万円以上`}
      {noteModalBtn}
      {overtimeSalary}
    </>
  );
}

/**
 * 「固定残業代」
 */
function renderOvertimeSalary(overtimeSalaryImtRecord) {
  const hasOvertimeSalary = overtimeSalaryImtRecord?.get("HasOvertimeSalary");

  if (hasOvertimeSalary !== HAS_OVERTIME_SALARY.EXIST) {
    return null;
  }

  // 固定残業代の月額
  const monthlyAmount = overtimeSalaryImtRecord.get("MonthlyAmount");
  // 固定残業代の見込み時間
  const expectedHours = overtimeSalaryImtRecord.get("ExpectedHours");

  if (!monthlyAmount || !expectedHours) return null;

  return (
    <AsteriskedParagraph className={styles.overtimeSalaryText}>
      {`固定残業代${monthlyAmount}万円/${expectedHours}時間相当分を含む`}
      <SpBr />
      （超過分は別途支給）
    </AsteriskedParagraph>
  );
}

/**
 * 「入社時年収」の見出し表示
 */
function renderIncomeName() {
  return (
    <>
      入社時年収
      <HelpTooltip
        help={{
          title: "入社時年収",
          text: "給与12ヶ月分、賞与、インセンティブなどを合計した金額です。",
        }}
        className={styles.helpBtn}
      />
    </>
  );
}

/**
 * 「入社時年収」
 */
function renderIncome(positionImtRecord) {
  // 入社時年収
  const jobChangeImtRecord = positionImtRecord.get(
    POSITION_DETAIL.JOB_CHANGE.ID,
  );

  const jobChangeContent = renderJobChange(jobChangeImtRecord);

  // 年収イメージ
  const modelAnnualIncomeImtRecord = positionImtRecord.get(
    POSITION_DETAIL.MODEL_ANNUAL_INCOME.ID,
  );

  const modelAnnualIncomeContent = renderModelAnnualIncome(
    modelAnnualIncomeImtRecord,
  );

  // 何も表示するものが無い場合
  if (!(jobChangeContent || modelAnnualIncomeContent)) {
    return null;
  }

  const jobChange = jobChangeContent ? <li>{jobChangeContent}</li> : null;

  const modelAnnualIncome = modelAnnualIncomeContent ? (
    <li>{modelAnnualIncomeContent}</li>
  ) : null;

  return (
    <ContentList>
      {jobChange}
      {modelAnnualIncome}
    </ContentList>
  );
}

/**
 * 「入社時年収」（企業側「確約年収」)
 */
function renderJobChange(jobChangeImtRecord) {
  // 求人年収の下限値と上限値が空なら表示しない
  if (!jobChangeImtRecord?.isIncomeInputted()) return null;

  // 年収ラベル
  const incomeFrom = jobChangeImtRecord.getIn(["Income", "From"]);
  const incomeTo = jobChangeImtRecord.getIn(["Income", "To"]);
  const income =
    incomeFrom == null
      ? incomeTo != null
        ? `～${incomeTo}万円`
        : ""
      : incomeTo == null
        ? `${incomeFrom}万円～`
        : incomeFrom === incomeTo
          ? `${incomeFrom}万円`
          : `${incomeFrom}～${incomeTo}万円`;

  // 補足
  const noteText = jobChangeImtRecord.getIn(["Income", "Note"]);

  // 折りたたんで表示する補足
  const collapsibleNote = renderCollapsibleNote(noteText);

  return (
    <div className={styles.incomeBody}>
      {income}
      {collapsibleNote}
    </div>
  );
}

/**
 * 「年収イメージ」（企業側「モデル年収」）
 */
function renderModelAnnualIncome(modelAnnualIncomeImtRecord) {
  if (!modelAnnualIncomeImtRecord?.hasSomeValue()) return null;

  const incomeGroups = Object.keys(MODEL_ANNUAL_INCOME.KEYS)
    .map((key) => {
      const incomeObj = MODEL_ANNUAL_INCOME.KEYS[key];
      const incomeId = modelAnnualIncomeImtRecord.get(incomeObj.ID);

      // 年収イメージの値が無い場合は表示しない
      if (!incomeId) return null;

      const incomeName = ArrayFinder.findNameById(
        MODEL_ANNUAL_INCOME.INCOMES,
        incomeId,
      );
      return <li key={incomeObj.ID}>{`${incomeObj.Label}：${incomeName}`}</li>;
    })
    .filter(Boolean);

  // 補足
  const noteText = modelAnnualIncomeImtRecord.get("Note");

  // 折りたたんで表示する補足
  const collapsibleNote = renderCollapsibleNote(noteText);

  return (
    <>
      <h5 className={styles.incomeHeader}>年収イメージ</h5>
      <ContentHorizontalList>{incomeGroups}</ContentHorizontalList>
      {collapsibleNote}
    </>
  );
}

/**
 * 折りたたんで表示する補足
 */
function renderCollapsibleNote(noteText) {
  return noteText ? (
    <div className={styles.note}>
      <CollapsibleNote contentText={noteText} />
    </div>
  ) : null;
}

/**
 * 「賞与」欄の内容
 */
function renderBonusCount(positionImtRecord) {
  // 賞与
  const masterImtRecord = positionImtRecord.get(POSITION_DETAIL.BONUS_COUNT.ID);

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
 * 「昇給・昇格」欄の内容
 */
function renderPromotionCount(positionImtRecord) {
  // 昇給・昇格
  const masterImtRecord = positionImtRecord.get(
    POSITION_DETAIL.PROMOTION_COUNT.ID,
  );

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
 * 「ストックオプション制度」欄の内容
 */
function renderStockOption(positionImtRecord) {
  const masterImtRecord = positionImtRecord.get(
    POSITION_DETAIL.STOCK_OPTION.ID,
  );

  // 未設定か、ストックオプションなしかつ補足なしの場合は描画しない
  if (
    !masterImtRecord?.get("ID") ||
    (masterImtRecord.get("ID") === STOCK_OPTION.NONE &&
      !masterImtRecord.get("Note"))
  ) {
    return null;
  }

  return (
    <ContentList>
      <ContentListItem traitImtRecord={masterImtRecord} />
    </ContentList>
  );
}

/**
 * 「入社祝い金」（企業側「入社支度金」
 */
function renderJoinedReserve(positionImtRecord) {
  const value = positionImtRecord.get(POSITION_DETAIL.JOINED_RESERVE.ID);

  if (!value) {
    return null;
  }

  return (
    <ContentList>
      <li>{`${value}万円`}</li>
    </ContentList>
  );
}
