import PropTypes from "prop-types";
import {
  POSITION_DETAIL,
  POSITION_LABEL_DISPLAY_TYPE,
} from "@/constants/position";
import { TRAITS as COMPANY_TRAITS } from "@/constants/companies";
import { getModifiedLabel } from "@/helpers/traitLabel";
import Image from "@/components/utils/Image";

import styles from "./PositionSummary.module.scss";

/**
 * 気になる項目をチェック
 */
export default function PositionSummary(props) {
  // 休日
  const holiday = renderItem(
    POSITION_DETAIL.HOLIDAY.Name,
    props.positionImtRecord.getIn(["Holiday", "Name"]),
    "/assets/next/img/offers/ico_summary_holiday.svg",
    43,
  );
  // 年間休日
  const yearHolidays = renderItem(
    COMPANY_TRAITS.CTX_YEAR_HOLIDAYS.Name,
    props.companyImtRecord.getIn(["YearHolidays", "Name"]),
    "/assets/next/img/offers/ico_summary_year_holidays.svg",
    43,
  );
  // 平均残業時間
  const overtimeAvgValueLabel = getModifiedLabel(
    POSITION_DETAIL.OVERTIME_AVG.ID,
    props.positionImtRecord.get("OvertimeAvg"),
    POSITION_LABEL_DISPLAY_TYPE.SUMMARY,
  );
  const overtimeAvg = renderItem(
    POSITION_DETAIL.OVERTIME_AVG.Name,
    overtimeAvgValueLabel,
    "/assets/next/img/offers/ico_summary_overtime_avg.svg",
    41,
  );
  // 在宅勤務
  const remoteWorkValueLabel = getModifiedLabel(
    POSITION_DETAIL.REMOTE_WORK.ID,
    props.positionImtRecord.get("RemoteWork"),
    POSITION_LABEL_DISPLAY_TYPE.SUMMARY,
  );
  const remoteWork = renderItem(
    "在宅勤務", // NOTE: POSITION_DETAIL.REMOTE_WORK.Nameは「リモート勤務」のままで、一部のみ「在宅勤務」表記にする。
    remoteWorkValueLabel,
    "/assets/next/img/offers/ico_summary_remote_work.svg",
    38,
  );
  // 書類選考
  // TODO: プロフが必要なので、不要
  // const menkakuLabel = props.fittingImtRecord.isMenkaku() ? 'なし（通過済み）' : 'あり';
  // const menkaku = renderItem('書類選考', menkakuLabel, '/assets/next/img/offers/ico_summary_menkaku.svg', 34);
  // オンライン面接
  const onlineInterviewLabel = props.interviewImtRecord?.getIn([
    "Online",
    "EnableFlg",
  ])
    ? "OK"
    : "NG";
  const onlineInterview = renderItem(
    "オンライン面接",
    onlineInterviewLabel,
    "/assets/next/img/offers/ico_summary_online_interview.svg",
    44,
  );

  return (
    <div className={styles.container}>
      <p className={styles.title}>気になる項目をチェック！</p>
      <ul className={styles.content}>
        {holiday}
        {yearHolidays}
        {overtimeAvg}
        {remoteWork}
        {/* {menkaku} */}
        {onlineInterview}
      </ul>
    </div>
  );
}

PositionSummary.propTypes = {
  positionImtRecord: PropTypes.object.isRequired,
  companyImtRecord: PropTypes.object.isRequired,
  interviewImtRecord: PropTypes.object,
};

PositionSummary.defaultProps = {
  interviewImtRecord: null,
};

/**
 * 項目を描画
 */
function renderItem(title, valueLabel, iconSrc, iconWidth) {
  if (!valueLabel) return null;

  return (
    <li className={styles.item}>
      <div className={styles.itemIcon}>
        <Image src={iconSrc} alt={title} width={iconWidth} />
      </div>
      <dl>
        <dt className={styles.itemTitle}>{title}</dt>
        <dd className={styles.itemValueLabel}>{valueLabel}</dd>
      </dl>
    </li>
  );
}
