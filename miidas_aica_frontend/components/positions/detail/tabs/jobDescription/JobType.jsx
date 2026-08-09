import PropTypes from "prop-types";

import { POSITION_DETAIL } from "@/constants/position";

import Text2LinkWrapper from "@/components/positions/detail/parts/Text2LinkWrapper";
import JobTypeItem from "./JobTypeItem";

import styles from "./JobType.module.scss";

/**
 * 「仕事内容」
 */
export default function JobType(props) {
  // 必須入力項目だが、昔実装されていたダミー求人という求人には仕事内容（職種）がない場合があるので未入力チェックを行う
  const jobImtList = props.positionImtRecord.get(POSITION_DETAIL.JOBS.ID);
  if (!jobImtList?.size) return null;

  const jobDetail = renderJobDetail(props.positionImtRecord);
  const mainJob = renderMainJob(props.positionImtRecord);
  const subJobs = renderSubJobs(props.positionImtRecord);

  return (
    <ul className={styles.jobType}>
      {jobDetail}
      {mainJob}
      {subJobs}
    </ul>
  );
}

JobType.propTypes = {
  positionImtRecord: PropTypes.object.isRequired,
};

/**
 * 「仕事内容詳細」
 */
function renderJobDetail(positionImtRecord) {
  const jobText = positionImtRecord.get(POSITION_DETAIL.MAIN_JOB_TEXT.ID);

  if (!jobText) {
    return null;
  }

  return (
    <li className={styles.jobTypeItem}>
      <Text2LinkWrapper text={jobText} />
    </li>
  );
}

/**
 * 「職種（メイン業務）」
 */
function renderMainJob(positionImtRecord) {
  // メイン業務の仕事内容
  const traitImtRecord = positionImtRecord.getMainJobRecord();

  if (!traitImtRecord) {
    return null;
  }

  return (
    <li className={styles.jobTypeItem}>
      <h4 className={styles.subGroupHeader}>職種（メイン業務）</h4>
      <dl>
        <JobTypeItem traitImtRecord={traitImtRecord} />
      </dl>
    </li>
  );
}

/**
 * 「職種（メイン以外で行う業務）」
 */
function renderSubJobs(positionImtRecord) {
  // メイン以外で行う業務の仕事内容リスト
  const traitImtList = positionImtRecord.getSubJobRecords();

  if (!traitImtList?.size) {
    return null;
  }

  const subJobItems = traitImtList.map((traitImtRecord) => {
    return (
      <div key={traitImtRecord.get("SmallID")} className={styles.subJobItem}>
        <JobTypeItem traitImtRecord={traitImtRecord} />
      </div>
    );
  });

  return (
    <li className={styles.jobTypeItem}>
      <h4 className={styles.subGroupHeader}>職種（メイン以外で行う業務）</h4>
      <dl>{subJobItems}</dl>
    </li>
  );
}
