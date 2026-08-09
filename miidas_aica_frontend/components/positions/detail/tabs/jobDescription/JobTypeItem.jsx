import PropTypes from "prop-types";

import { useState, useRef } from "react";

import { getHash } from "@/utils";
import { clsx } from "@/utils/className";
import { getLabelFromMasterRecord } from "@/helpers/positionDetail";

import CollapsibleJobTypeItem from "@/components/positions/detail/parts/CollapsibleJobTypeItem";

import styles from "./JobTypeItem.module.scss";

/**
 * 職種（メイン業務）/ 職種（メイン以外で行う業務）のスキルグループ名とスキルアイテム
 */
export default function JobTypeItem({ traitImtRecord }) {
  // スキルグループを展開しているかの状態
  const [isExpanded, setIsExpanded] = useState(false);

  const skillGroupNameRef = useRef(null);
  const dummyGroupNameRef = useRef(null);
  const skillItemsRef = useRef(null);

  const jobName = renderJobName(traitImtRecord);

  const skillGroupsImtList = traitImtRecord?.get("SkillGroups");

  if (!skillGroupsImtList?.size) {
    return jobName;
  }

  // 最初のスキルグループ
  const firstSkillGroupImtRecord = skillGroupsImtList.first();
  // 最初の偽階層グループ
  const firstDummyGroupImtRecord = firstSkillGroupImtRecord
    ?.get("DummyGroups")
    ?.first();
  // 最初の偽階層グループ名が空かどうか
  const isFirstDummyGroupNameEmpty = firstDummyGroupImtRecord?.isNameEmpty();

  // 最初のスキルグループ
  // 最初の偽階層グループ名が空、かつ折り畳んだ状態の場合は、スキルリストを省略表示にする
  const isNeedEllipsis = isFirstDummyGroupNameEmpty && !isExpanded;
  const firstJobSkillItems = renderJobSkill(
    firstSkillGroupImtRecord,
    isNeedEllipsis,
    true,
    skillGroupNameRef,
    dummyGroupNameRef,
    skillItemsRef,
  );

  // 2番目以降のスキルグループ
  const jobSkillItems = renderJobSkills(skillGroupsImtList.rest());

  return (
    <>
      {jobName}
      <dd>
        <dl className={styles.jobSkills}>
          <CollapsibleJobTypeItem
            isNameEmpty={isFirstDummyGroupNameEmpty}
            isExpanded={isExpanded}
            setIsExpanded={setIsExpanded}
            skillGroupNameRef={skillGroupNameRef}
            dummyGroupNameRef={dummyGroupNameRef}
            skillItemsRef={skillItemsRef}
            skillGroupSize={skillGroupsImtList.size}
          >
            {firstJobSkillItems}
            {jobSkillItems}
          </CollapsibleJobTypeItem>
        </dl>
      </dd>
    </>
  );
}

JobTypeItem.propTypes = {
  traitImtRecord: PropTypes.object.isRequired,
};

/**
 * 職種名を返す
 */
function renderJobName(traitImtRecord) {
  return traitImtRecord ? (
    <dt className={styles.jobName}>
      {getLabelFromMasterRecord(traitImtRecord)}
    </dt>
  ) : null;
}

/**
 * スキルグループを返す
 */
function renderJobSkill(
  skillGroupImtRecord,
  isNeedEllipsis = false,
  isFirst = false,
  skillGroupNameRef = null,
  dummyGroupNameRef = null,
  skillItemsRef = null,
) {
  const skillGroupName = getLabelFromMasterRecord(skillGroupImtRecord);
  const skillGroupDummyItems = renderSkillGroupDummyItems(
    skillGroupImtRecord,
    isNeedEllipsis,
    isFirst,
    dummyGroupNameRef,
    skillItemsRef,
  );

  return (
    <div key={getHash(skillGroupName)} className={styles.skillGroupItem}>
      <dt
        className={styles.skillGroupName}
        ref={isFirst ? skillGroupNameRef : null}
      >
        {skillGroupName}
      </dt>
      <dd>
        <ul>{skillGroupDummyItems}</ul>
      </dd>
    </div>
  );
}

/**
 * 2番目以降のスキルグループを返す
 */
function renderJobSkills(skillGroupsImtList) {
  if (!skillGroupsImtList.size) {
    return null;
  }

  return skillGroupsImtList.map((skillGroupImtRecord) => {
    return renderJobSkill(skillGroupImtRecord);
  });
}

/**
 * 偽階層のスキルリストを返す
 */
function renderSkillGroupDummyItems(
  skillGroupImtRecord,
  isNeedEllipsis,
  isFirst,
  dummyGroupNameRef,
  skillItemsRef,
) {
  const dummyGroupItems = skillGroupImtRecord
    .get("DummyGroups")
    .map((dummyGroupImtRecord) => {
      const lastIndex = dummyGroupImtRecord.get("Skills").size - 1;

      const dummyGroupSkillItems = dummyGroupImtRecord
        .get("Skills")
        .map((skillImtRecord, index) => {
          const label = getLabelFromMasterRecord(skillImtRecord);
          if (index === lastIndex) {
            return skillImtRecord.get("Main") ? (
              <span
                key={getHash(label)}
                className={styles.dummyGroupMainSkillItem}
              >
                {label}
              </span>
            ) : (
              label
            );
          }
          return skillImtRecord.get("Main") ? (
            <span
              key={getHash(label)}
              className={styles.dummyGroupMainSkillItem}
            >
              {`${label}、`}
            </span>
          ) : (
            `${label}、`
          );
        });

      const skillItemsCls = clsx(
        styles.dummyGroupSkillItems,
        isNeedEllipsis && styles.omitted,
      );

      return (
        <li
          key={getLabelFromMasterRecord(dummyGroupImtRecord)}
          className={styles.dummyGroupItem}
        >
          {renderDummyGroupName(
            dummyGroupImtRecord,
            isFirst,
            dummyGroupNameRef,
          )}
          <p className={skillItemsCls} ref={isFirst ? skillItemsRef : null}>
            {dummyGroupSkillItems}
          </p>
        </li>
      );
    });

  return dummyGroupItems;
}

/**
 * 偽階層グループ名を返す
 */
function renderDummyGroupName(dummyGroupImtRecord, isFirst, dummyGroupNameRef) {
  const dummyGroupName = getLabelFromMasterRecord(dummyGroupImtRecord);

  return dummyGroupName ? (
    <div
      className={styles.dummyGroupName}
      ref={isFirst ? dummyGroupNameRef : null}
    >
      {dummyGroupName}
    </div>
  ) : null;
}
