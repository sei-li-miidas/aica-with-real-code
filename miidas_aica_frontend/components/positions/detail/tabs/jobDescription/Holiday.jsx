import PropTypes from "prop-types";

import { TRAITS as POSITION_TRAITS } from "@/constants/position";
import {
  TRAITS as COMPANY_TRAITS,
  EXCEPTION_HIDDEN_TRAIT_OPTION,
} from "@/constants/companies";
import { ImmutableListFinder } from "@/utils/finder";

import HelpTooltip from "@/components/utils/HelpTooltip";
import TraitHelpTooltip from "@/components/positions/detail/parts/trait/TraitHelpTooltip";
import TraitList from "@/components/positions/detail/parts/trait/TraitList";
import TraitListItem from "@/components/positions/detail/parts/trait/TraitListItem";
import ContentList from "@/components/positions/detail/parts/trait/ContentList";
import ContentListItem from "@/components/positions/detail/parts/trait/ContentListItem";
import ContentMultipleValueWithNote from "@/components/positions/detail/parts/trait/ContentMultipleValueWithNote";

import styles from "./Holiday.module.scss";

/**
 * 「休日休暇」
 */
export default function Holiday(props) {
  // 休日
  const holiday = renderHoliday(props.positionImtRecord);
  // 休暇
  const vacations = renderVacations(props.companyImtRecord);
  // 年間休日
  const yearHolidays = renderYearHolidays(props.companyImtRecord);
  // 有給休暇取得率
  const paidHolidayUseRateName = renderPaidHolidayUseRateName();
  const paidHolidayUseRate = renderPaidHolidayUseRate(props.companyImtRecord);

  return (
    <TraitList>
      <TraitListItem
        itemKey={POSITION_TRAITS.PTX_HOLIDAY.ID}
        itemName="休日"
        content={holiday}
      />
      <TraitListItem
        itemKey={COMPANY_TRAITS.CTX_VACATIONS.ID}
        itemName="休暇"
        content={vacations}
      />
      <TraitListItem
        itemKey={COMPANY_TRAITS.CTX_YEAR_HOLIDAYS.ID}
        itemName="年間休日"
        content={yearHolidays}
      />
      <TraitListItem
        itemKey={COMPANY_TRAITS.CTX_PAID_HOLIDAY_USE_RATE.ID}
        itemName={paidHolidayUseRateName}
        content={paidHolidayUseRate}
      />
    </TraitList>
  );
}

Holiday.propTypes = {
  positionImtRecord: PropTypes.object.isRequired,
  companyImtRecord: PropTypes.object.isRequired,
};

/**
 * 「休日」欄の内容
 */
function renderHoliday(positionImtRecord) {
  const masterImtRecord = positionImtRecord.get("Holiday");

  if (!masterImtRecord) {
    return null;
  }

  const helpTooltip = (
    <TraitHelpTooltip
      traitId={POSITION_TRAITS.PTX_HOLIDAY.ID}
      traitValue={masterImtRecord.get("ID")}
    />
  );

  const labelWithHelpTooltip = (label) => {
    return (
      <div className={styles.holidayLabel}>
        {label}
        {helpTooltip}
      </div>
    );
  };

  return (
    <ContentList>
      <ContentListItem
        traitImtRecord={masterImtRecord}
        labelModifier={labelWithHelpTooltip}
      />
    </ContentList>
  );
}

/**
 * 「休暇」欄の内容
 */
function renderVacations(companyImtRecord) {
  const vacationsImtMap = companyImtRecord?.get("Vacations");

  // 「休暇」の設定値一覧
  const valueImtList = vacationsImtMap?.get("ValueTexts");

  // 未入力の場合は非表示
  if (!valueImtList || !valueImtList.size) {
    return null;
  }

  // 「該当なし」が選択されている場合はそのRecordを取得
  const exceptionImtRecord = ImmutableListFinder.findById(
    valueImtList,
    EXCEPTION_HIDDEN_TRAIT_OPTION.MULTIPLE_TRAIT,
  );

  // 「休暇」のオプション一覧
  const optionImtList = vacationsImtMap?.get("Options");

  return (
    <ContentMultipleValueWithNote
      valueImtList={valueImtList}
      hasNotApplicable={Boolean(exceptionImtRecord)}
      notApplicableValue={EXCEPTION_HIDDEN_TRAIT_OPTION.MULTIPLE_TRAIT}
      optionImtList={optionImtList}
    />
  );
}

/**
 * 「年間休日」欄の内容
 */
function renderYearHolidays(companyImtRecord) {
  const masterImtRecord = companyImtRecord?.get("YearHolidays");

  if (!masterImtRecord?.get("ID")) {
    return null;
  }

  return (
    <ContentList>
      <ContentListItem traitImtRecord={masterImtRecord} />
    </ContentList>
  );
}

/**
 * 「有給休暇取得率」の見出し表示
 */
function renderPaidHolidayUseRateName() {
  return (
    <>
      有給休暇取得率
      <HelpTooltip
        help={COMPANY_TRAITS.CTX_PAID_HOLIDAY_USE_RATE.Help}
        className={styles.helpBtn}
      />
    </>
  );
}

/**
 * 「有給休暇取得率」欄の内容
 */
function renderPaidHolidayUseRate(companyImtRecord) {
  const masterImtRecord = companyImtRecord?.get("PaidHolidayUseRate");

  if (!masterImtRecord) {
    return null;
  }

  const isDisplayNA =
    masterImtRecord?.get("ID") ===
    EXCEPTION_HIDDEN_TRAIT_OPTION.CTX_PAID_HOLIDAY_USE_RATE;
  const noteText = masterImtRecord?.get("Note");

  // 「不明」かつ補足も無い場合は非表示
  if (isDisplayNA && !noteText) {
    return null;
  }

  return (
    <ContentList>
      <ContentListItem traitImtRecord={masterImtRecord} />
    </ContentList>
  );
}
