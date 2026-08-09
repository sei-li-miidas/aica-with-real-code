import PropTypes from "prop-types";

import { BOSS_NAMES } from "@/constants/position";
import {
  COMPETENCY_NAVIGATION,
  COMPETENCY_EXAM_STATUS,
} from "@/constants/competency/competency";

import { getHash } from "@/utils";

import styles from "./BossType.module.scss";

/**
 * BossType
 * 上司との相性
 */
export default function BossType(props) {
  // プレビューまたは受験済みの場合は、上司との相性を表示する
  const isDisplayBossType =
    props.isPreview ||
    props.competencyStatus === COMPETENCY_EXAM_STATUS.FINISHED;

  if (!isDisplayBossType) {
    return (
      <div>
        <p className={styles.bossCompetencyExamAlert}>
          未実施のため結果が出ません
        </p>
        <p className={styles.bossCompetencyExamDescription}>
          コンピテンシー診断でこの企業に所属している上司との相性がわかります
        </p>
        <a
          href={COMPETENCY_NAVIGATION.INDEX}
          target="_blank"
          rel="noopener noreferrer"
          className={styles.competencyExamBtn}
        >
          コンピテンシー診断を受験する
        </a>
      </div>
    );
  }

  const list = props.bossImtList.map((bossImtRecord, index) =>
    renderListItem(bossImtRecord, index, props.userCompetencyResultImtRecord),
  );

  return <ul className={styles.list}>{list}</ul>;
}

function renderListItem(bossImtRecord, index, userCompetencyResultImtRecord) {
  const { good, bad } = userCompetencyResultImtRecord.getHierarchyBossMatch(
    bossImtRecord.toJS(),
  );

  let title = "";
  let bossTypes = "";
  if (good.bossTypes.length && bad.bossTypes.length) {
    title = (
      <p>
        あなたとの相性は<span className={styles.matchGood}>良い</span>部分と
        <span className={styles.matchBad}>良くない</span>部分があります。
      </p>
    );
    bossTypes = (
      <>
        <p>相性が良い … {good.bossTypes.join("、")}</p>
        <p>相性が良くない … {bad.bossTypes.join("、")}</p>
      </>
    );
  } else if (good.bossTypes.length) {
    title = (
      <p>
        あなたとの相性は<span className={styles.matchGood}>良い</span>です。
      </p>
    );
    bossTypes = <p>{good.bossTypes.join("、")}</p>;
  } else if (bad.bossTypes.length) {
    title = (
      <p>
        あなたとの相性は<span className={styles.matchBad}>良くない</span>です。
      </p>
    );
    bossTypes = <p>{bad.bossTypes.join("、")}</p>;
  } else {
    title = <p>あなたとの相性は普通です。</p>;
  }

  const typeValue = bossTypes ? (
    <dd className={styles.typeValue}>
      上司{BOSS_NAMES[index]}のタイプ：
      <br />
      {bossTypes}
    </dd>
  ) : null;

  return (
    <li className={styles.listItem} key={getHash(`Boss${index}`)}>
      <div className={styles.header}>上司{BOSS_NAMES[index]}</div>
      <dl className={styles.body}>
        <dt className={styles.typeKey}>{title}</dt>
        {typeValue}
      </dl>
    </li>
  );
}

BossType.propTypes = {
  bossImtList: PropTypes.object.isRequired,
  competencyStatus: PropTypes.number.isRequired,
  isPreview: PropTypes.bool,
  userCompetencyResultImtRecord: PropTypes.object.isRequired,
};

BossType.defaultProps = {
  isPreview: false,
};
