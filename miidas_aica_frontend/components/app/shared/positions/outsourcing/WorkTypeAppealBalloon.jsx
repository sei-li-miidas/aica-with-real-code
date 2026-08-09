import PropTypes from "prop-types";

import { APPEAL_WORK_TYPE_ID_ICON_MAP } from "@/constants/position";
import SvgIcon from "@/components/utils/SvgIcon";

import styles from "./WorkTypeAppealBalloon.module.scss";

/**
 * 業務委託のアピールポイント「業務内容」のバルーン
 */
export default function WorkTypeAppealBalloon({ outsourcingAppealImtRecord }) {
  const workTypeAppealLabel = outsourcingAppealImtRecord.getWorkTypeLabel();

  const workTypeIconId =
    APPEAL_WORK_TYPE_ID_ICON_MAP[outsourcingAppealImtRecord.get("WorkType")];

  const workTypeIcon = workTypeIconId ? (
    <SvgIcon icon={workTypeIconId} className={styles.icon} />
  ) : null;

  return (
    <div className={styles.wrapper}>
      <div className={styles.content}>
        {workTypeIcon}
        <span className={styles.label}>{workTypeAppealLabel}</span>
      </div>
    </div>
  );
}

WorkTypeAppealBalloon.propTypes = {
  outsourcingAppealImtRecord: PropTypes.object.isRequired,
};

WorkTypeAppealBalloon.defaultProps = {};
