import { WORK_EXPERIENCE_KEYS } from "@/models/records/WorkExperience";

import CollapsibleNote from "@/components/positions/detail/parts/CollapsibleNote";
import SectionListItem from "@/components/positions/detail/parts/SectionListItem";
import TraitList from "@/components/positions/detail/parts/trait/TraitList";
import TraitListItem from "@/components/positions/detail/parts/trait/TraitListItem";
import WorkExperienceHeader from "@/components/positions/detail/tabs/interviewSettings/WorkExperienceHeader";

import styles from "./WorkExperience.module.scss";

/**
 * リアル職場体験を表示するコンポーネント
 * @param {Object} props
 * @param {Object} props.positionDetailImtRecord - Position detail immutable record
 */
const WorkExperience = ({ positionDetailImtRecord }) => {
  const workExperienceImtRecord = positionDetailImtRecord.getIn([
    "OfferDetail",
    "Position",
    "Interview",
    "WorkExperience",
  ]);

  if (!workExperienceImtRecord) return null;
  if (workExperienceImtRecord.isWorkExperienceNotSet()) return null;

  const timingDescription = renderTimingDescription(workExperienceImtRecord);

  const workTypesDescription = workExperienceImtRecord
    .getLabel(WORK_EXPERIENCE_KEYS.WORK_TYPES)
    .join(" / ");

  const timeFrameDescription = renderDescriptionWithRemark(
    workExperienceImtRecord,
    WORK_EXPERIENCE_KEYS.TIMEFRAME,
    WORK_EXPERIENCE_KEYS.TIMEFRAME_REMARKS,
  );

  const needTimeDescription = renderDescriptionWithRemark(
    workExperienceImtRecord,
    WORK_EXPERIENCE_KEYS.NEED_TIME,
    WORK_EXPERIENCE_KEYS.NEED_TIME_REMARKS,
  );

  const rewardDescription = renderRewardDescription(workExperienceImtRecord);

  const content = workExperienceImtRecord.isWorkExperienceEnabled() ? (
    <>
      <TraitListItem
        itemKey="pattern"
        itemName="実施可否"
        content={workExperienceImtRecord.getLabel(WORK_EXPERIENCE_KEYS.PATTERN)}
      />
      <TraitListItem
        itemKey="timing"
        itemName="実施タイミング"
        content={timingDescription}
      />
      <TraitListItem
        itemKey="workTypes"
        itemName="実施内容"
        content={workTypesDescription}
      />
      <TraitListItem
        itemKey="timeframe"
        itemName="実施日時"
        content={timeFrameDescription}
      />
      <TraitListItem
        itemKey="needTime"
        itemName="所要時間"
        content={needTimeDescription}
      />
      <TraitListItem
        itemKey="reward"
        itemName="実務体験の報酬"
        content={rewardDescription}
      />
      <TraitListItem
        itemKey="workContent"
        itemName="実施内容詳細"
        content={workExperienceImtRecord.getLabel(
          WORK_EXPERIENCE_KEYS.WORK_CONTENT,
        )}
      />
    </>
  ) : (
    // 実施しない場合も実施可否以外もAPIから返ってくるので、実施可否のみ表示する
    <TraitListItem
      itemKey="pattern"
      itemName="実施可否"
      content={workExperienceImtRecord.getLabel(WORK_EXPERIENCE_KEYS.PATTERN)}
    />
  );

  return (
    <SectionListItem title={<WorkExperienceHeader />}>
      <TraitList>{content}</TraitList>
    </SectionListItem>
  );
};

/**
 * 補足つきの内容を返す
 */
function renderDescriptionWithRemark(workExperienceImtRecord, key, remarkKey) {
  const description = workExperienceImtRecord.getLabel(key);
  return workExperienceImtRecord.getLabel(remarkKey) ? (
    <ul>
      <li>{description}</li>
      <li className={styles.remarks}>
        <CollapsibleNote
          contentText={workExperienceImtRecord.getLabel(remarkKey)}
        />
      </li>
    </ul>
  ) : (
    description
  );
}

/**
 * 「実施タイミング」
 */
function renderTimingDescription(workExperienceImtRecord) {
  const description = workExperienceImtRecord.isOtherTimingTextShown() ? (
    <>
      <p>{workExperienceImtRecord.getLabel(WORK_EXPERIENCE_KEYS.TIMING)}</p>
      <p className={styles.otherTimingText}>
        {workExperienceImtRecord.getLabel(
          WORK_EXPERIENCE_KEYS.OTHER_TIMING_TEXT,
        )}
      </p>
    </>
  ) : (
    workExperienceImtRecord.getLabel(WORK_EXPERIENCE_KEYS.TIMING)
  );

  return workExperienceImtRecord.getLabel(
    WORK_EXPERIENCE_KEYS.TIMING_REMARKS,
  ) ? (
    <ul>
      <li>{description}</li>
      <li className={styles.remarks}>
        <CollapsibleNote
          contentText={workExperienceImtRecord.getLabel(
            WORK_EXPERIENCE_KEYS.TIMING_REMARKS,
          )}
        />
      </li>
    </ul>
  ) : (
    description
  );
}

/**
 * 「実務体験の報酬」
 */
function renderRewardDescription(workExperienceImtRecord) {
  let reward = null;
  if (workExperienceImtRecord.isRewardValueShown()) {
    // 報酬の時給
    const rewardValue = workExperienceImtRecord
      .getLabel(WORK_EXPERIENCE_KEYS.REWARD_VALUE)
      .toLocaleString();
    reward = (
      <li>
        1時間あたり
        {rewardValue}円
      </li>
    );
  }

  const description = (
    <ul>
      <li>{workExperienceImtRecord.getLabel(WORK_EXPERIENCE_KEYS.REWARD)}</li>
      {reward}
    </ul>
  );

  return workExperienceImtRecord.getLabel(
    WORK_EXPERIENCE_KEYS.REWARD_REMARKS,
  ) ? (
    <ul>
      <li>{description}</li>
      <li className={styles.remarks}>
        <CollapsibleNote
          contentText={workExperienceImtRecord.getLabel(
            WORK_EXPERIENCE_KEYS.REWARD_REMARKS,
          )}
        />
      </li>
    </ul>
  ) : (
    description
  );
}

export default WorkExperience;
