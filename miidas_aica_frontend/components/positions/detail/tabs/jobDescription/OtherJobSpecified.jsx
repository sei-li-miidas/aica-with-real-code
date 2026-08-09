import PropTypes from "prop-types";

import {
  TRAITS as POSITION_TRAITS,
  POSITION_DETAIL,
  POSITION_LABEL_DISPLAY_TYPE,
} from "@/constants/position";
import { ImmutableListFinder } from "@/utils/finder";
import { getModifiedLabel } from "@/helpers/traitLabel";
import { hasSomeTraitValues } from "@/helpers/positionDetail";

import HelpTooltip from "@/components/utils/HelpTooltip";
import NoteModalBtn from "@/components/positions/detail/parts/NoteModalBtn";
import TraitList from "@/components/positions/detail/parts/trait/TraitList";
import TraitListItem from "@/components/positions/detail/parts/trait/TraitListItem";
import ContentList from "@/components/positions/detail/parts/trait/ContentList";
import ContentListItemHrEvaluationCompetency from "@/components/positions/detail/parts/trait/ContentListItemHrEvaluationCompetency";
import ContentHorizontalList from "@/components/positions/detail/parts/trait/ContentHorizontalList";
import BossType from "./BossType";

import styles from "./OtherJobSpecified.module.scss";

/**
 * 「求人の特徴」 > 「その他の特徴」
 */
export default function OtherJobSpecified({
  positionImtRecord,
  competencyStatus,
  isPreview,
  userCompetencyResultImtRecord,
}) {
  const hrEvaluationCompetencyName = renderHrEvaluationCompetencyName(
    positionImtRecord.get(POSITION_DETAIL.HR_EVALUATION_COMPETENCY.ID),
  );
  const hrEvaluationCompetency =
    renderHrEvaluationCompetency(positionImtRecord);

  const bossTypeName = renderBossTypeName();
  const bossTypeLabels = renderBossTypeLabels(
    positionImtRecord,
    competencyStatus,
    isPreview,
    userCompetencyResultImtRecord,
  );

  const jobDependenciesSpecified =
    renderJobDependenciesSpecified(positionImtRecord);

  return (
    <TraitList>
      <TraitListItem
        itemKey={POSITION_TRAITS.PTX_HR_EVALUATION__COMPETENCY.ID}
        itemName={hrEvaluationCompetencyName}
        content={hrEvaluationCompetency}
      />
      <TraitListItem
        itemKey="boss_type"
        itemName={bossTypeName}
        content={bossTypeLabels}
      />
      <TraitListItem
        itemKey="job_dependencies_specified"
        itemName="仕事情報の補足"
        content={jobDependenciesSpecified}
      />
    </TraitList>
  );
}

OtherJobSpecified.propTypes = {
  positionImtRecord: PropTypes.object.isRequired,
  competencyStatus: PropTypes.number.isRequired,
  isPreview: PropTypes.bool,
  userCompetencyResultImtRecord: PropTypes.object.isRequired,
};

OtherJobSpecified.defaultProps = {
  isPreview: false,
};

/**
 * 「特に評価されるコンピテンシー」欄の内容
 */
function renderHrEvaluationCompetency(positionImtRecord) {
  const traitImtRecord = positionImtRecord.get(
    POSITION_DETAIL.HR_EVALUATION_COMPETENCY.ID,
  );

  const traitValueImtList = traitImtRecord?.get("Axes");

  if (!traitImtRecord || !traitValueImtList?.size) {
    return null;
  }

  const hrEvaluationCompetencyItems = traitValueImtList.map(
    (traitValueImtRecord) => {
      return (
        <ContentListItemHrEvaluationCompetency
          key={traitValueImtRecord.get("Axis")}
          traitValueImtRecord={traitValueImtRecord}
        />
      );
    },
  );

  return <ContentList>{hrEvaluationCompetencyItems}</ContentList>;
}

/**
 * 「特に評価されるコンピテンシー」欄の項目名
 */
function renderHrEvaluationCompetencyName(traitImtRecord) {
  const noteText = traitImtRecord?.get("Note");
  // モーダルで表示する補足
  const noteModalBtn = noteText ? (
    <NoteModalBtn contentText={noteText} />
  ) : null;

  // [補足] ボタン横につけたラベル
  return (
    <>
      特に評価されるコンピテンシー
      {noteModalBtn}
    </>
  );
}

/**
 * 「上司との相性」欄の項目名
 */
function renderBossTypeName() {
  const help = {
    title: "上司との相性",
    text: "この求人であなたの上司となる人との相性",
  };

  return (
    <span className={styles.nameWithHelp}>
      上司との相性
      <HelpTooltip help={help} />
    </span>
  );
}

/**
 * 「上司との相性」のラベル表示
 */
function renderBossTypeLabels(
  positionImtRecord,
  competencyStatus,
  isPreview,
  userCompetencyResultImtRecord,
) {
  const bossImtList = positionImtRecord.get("BossTypeScores");
  if (!bossImtList?.size) {
    return null;
  }

  return (
    <BossType
      bossImtList={bossImtList}
      competencyStatus={competencyStatus}
      isPreview={isPreview}
      userCompetencyResultImtRecord={userCompetencyResultImtRecord}
    />
  );
}

/**
 * 「仕事情報の補足」欄の内容
 */
function renderJobDependenciesSpecified(positionImtRecord) {
  // HWエンジニア
  // キャリアパス
  const hwEnginnerCareerPath = renderLabel(
    positionImtRecord,
    POSITION_DETAIL.CAREER_PATH_WORK_HEAD_OFFICE_EXISTS.ID,
  );

  // 組織
  // エンジニア出身役員
  const engineerManagerExists = renderLabel(
    positionImtRecord,
    POSITION_DETAIL.ORG_TREND_ENGINEER_MANAGER_EXISTS.ID,
  );

  // エンジニアと他部署（企画、営業など）との関係性
  const relatedWithEngineer = renderLabel(
    positionImtRecord,
    POSITION_DETAIL.ORG_TREND_RELATED_WITH_ENGINEER.ID,
  );

  // 管理専門職 配属部署の人数
  const sectionMemberQty = renderLabel(
    positionImtRecord,
    POSITION_DETAIL.ORG_TREND_SECTION_MEMBER_QTY.ID,
  );

  // 管理専門職 会計士、税理士在籍
  const accountingLicenceExists = renderLabel(
    positionImtRecord,
    POSITION_DETAIL.ORG_TREND_ACCOUNTING_LICENCE_EXISTS.ID,
  );

  // 管理専門職 弁護士、弁理士在籍
  const legalLicenceExists = renderLabel(
    positionImtRecord,
    POSITION_DETAIL.ORG_TREND_LEGAL_LICENCE_EXISTS.ID,
  );

  // HWエンジニア
  // 開発スパン
  const hwEngineerDevelopmentTerm = renderLabel(
    positionImtRecord,
    POSITION_DETAIL.DEVELOPMENT_TERM.ID,
  );

  // 営業
  // 個人の業績目標の達成率
  const salesAccomplishmentRate = renderLabel(
    positionImtRecord,
    POSITION_DETAIL.ACCOMPLISHMENT_RATE.ID,
  );

  // 新規飛び込み営業
  const salesStyleDive = renderLabel(
    positionImtRecord,
    POSITION_DETAIL.SALES_STYLE_DIVE.ID,
  );

  // 新規テレアポ（電話営業）
  const salesStyleTelAppointment = renderLabel(
    positionImtRecord,
    POSITION_DETAIL.SALES_STYLE_TEL_APPOINTMENT.ID,
  );

  // 接待
  const salesStyleHost = renderLabel(
    positionImtRecord,
    POSITION_DETAIL.SALES_STYLE_HOST.ID,
  );

  // 営業・サービス
  // 他部署への異動
  const salesAndServiceCareerPath = renderLabel(
    positionImtRecord,
    POSITION_DETAIL.CAREER_PATH_OUT_OF_SITE_EXISTS.ID,
  );

  // アプリエンジニア
  // 開発手法
  const appEngineerDevelopmentProcess =
    renderAppEngineerDevelopmentProcess(positionImtRecord);

  // 緊急対応
  const emergencySupport = renderLabel(
    positionImtRecord,
    POSITION_DETAIL.EMERGENCY_SUPPORT.ID,
  );

  const items = [
    hwEnginnerCareerPath,
    engineerManagerExists,
    relatedWithEngineer,
    sectionMemberQty,
    accountingLicenceExists,
    legalLicenceExists,
    hwEngineerDevelopmentTerm,
    salesAccomplishmentRate,
    salesStyleDive,
    salesStyleTelAppointment,
    salesStyleHost,
    salesAndServiceCareerPath,
    appEngineerDevelopmentProcess,
    emergencySupport,
  ];

  if (!hasSomeTraitValues(items)) {
    return null;
  }

  return <ContentHorizontalList isNoLineBreak>{items}</ContentHorizontalList>;
}

/**
 * トレイトの値ラベル
 */
function renderLabel(positionImtRecord, traitId) {
  const traitImtRecord = positionImtRecord.get(traitId);

  if (!traitImtRecord) {
    return null;
  }

  // 補足
  const noteText = traitImtRecord.get("Note");
  // モーダルで表示する補足
  const noteModalBtn = noteText ? (
    <NoteModalBtn contentText={noteText} />
  ) : null;

  const label = getModifiedLabel(
    traitId,
    traitImtRecord,
    POSITION_LABEL_DISPLAY_TYPE.DETAIL,
  );

  return (
    <li key={traitId}>
      {label}
      {noteModalBtn}
    </li>
  );
}

/**
 * アプリエンジニア-開発手法
 */
function renderAppEngineerDevelopmentProcess(positionImtRecord) {
  const traitId = POSITION_DETAIL.DEVELOPMENT_PROCESS.ID;
  const masterWithOptionsImtRecord = positionImtRecord.get(traitId);

  if (!masterWithOptionsImtRecord) {
    return null;
  }

  const value = masterWithOptionsImtRecord.get("ID");
  // 「開発手法」のオプション一覧
  const optionLabelImtList = masterWithOptionsImtRecord.get("Options");

  const noteText = masterWithOptionsImtRecord.get("Note");

  const label = ImmutableListFinder.findNameById(optionLabelImtList, value);
  // モーダルで表示する補足
  const noteModalBtn = noteText ? (
    <NoteModalBtn contentText={noteText} />
  ) : null;

  return (
    <li key={traitId}>
      開発手法：
      {label}
      {noteModalBtn}
    </li>
  );
}
