import PropTypes from "prop-types";

import {
  POSITION_DETAIL,
  TRAITS,
  TRAIT_OPTION_VALUES,
  EXCEPTION_TRAIT_OPTION,
  POSITION_LABEL_DISPLAY_TYPE,
} from "@/constants/position";
import { getLabelFromMasterRecord } from "@/helpers/positionDetail";
import { getModifiedLabel } from "@/helpers/traitLabel";

import TraitList from "@/components/positions/detail/parts/trait/TraitList";
import TraitListItem from "@/components/positions/detail/parts/trait/TraitListItem";
import ContentList from "@/components/positions/detail/parts/trait/ContentList";
import ContentListItem from "@/components/positions/detail/parts/trait/ContentListItem";
import NoteModalBtn from "@/components/positions/detail/parts/NoteModalBtn";
import TraitWorkAddress from "./traitListItem/TraitWorkAddress";

import styles from "./WorkAddress.module.scss";

/**
 * 「勤務地」
 */
export default function WorkAddress(props) {
  const transference = renderTransference(props.positionImtRecord);

  const remoteWork = renderRemoteWork(props.positionImtRecord);

  const officialTripFrequency = renderOfficialTripFrequency(
    props.positionImtRecord,
  );

  return (
    <TraitList>
      <TraitWorkAddress positionImtRecord={props.positionImtRecord} />
      <TraitListItem
        itemKey={TRAITS.PTX_TRANSFERENCE_EXISTS.ID}
        itemName="転勤"
        content={transference}
      />
      <TraitListItem
        itemKey={TRAITS.PTX_REMOTE_WORK.ID}
        itemName="在宅勤務"
        content={remoteWork}
      />
      <TraitListItem
        itemKey={TRAITS.PTX_OFFICIAL_TRIP_FREQUENCY.ID}
        itemName="出張"
        content={officialTripFrequency}
      />
    </TraitList>
  );
}

WorkAddress.propTypes = {
  positionImtRecord: PropTypes.object.isRequired,
};

/**
 * 「転勤」欄の内容
 */
function renderTransference(positionImtRecord) {
  // 国内転勤
  const transferenceExistImtRecord = positionImtRecord.get(
    POSITION_DETAIL.TRANSFERENCE_EXISTS.ID,
  );
  const transferenceExist = renderContentListItemNoteModal(
    transferenceExistImtRecord,
  );

  // 国内転勤の頻度
  const transferenceFrequencyImtRecord = positionImtRecord.get(
    POSITION_DETAIL.TRANSFERENCE_FREQUENCY.ID,
  );
  const transferenceFrequency = renderTransferenceFrequency(
    transferenceFrequencyImtRecord,
  );

  // 海外転勤
  const transferenceAbroadExistsImtRecord = positionImtRecord.get(
    POSITION_DETAIL.TRANSFERENCE_ABROAD_EXISTS.ID,
  );
  const transferenceAbroadExists = renderContentListItemNoteModal(
    transferenceAbroadExistsImtRecord,
  );

  // 海外転勤で現地赴任する際の英語力
  const transferenceAbroadEnglishImtRecord = positionImtRecord.get(
    POSITION_DETAIL.TRANSFERENCE_ABROAD_ENGLISH_IS_UNUSED.ID,
  );
  const transferenceAbroadEnglish = renderTransferenceAbroadEnglish(
    transferenceAbroadEnglishImtRecord,
  );

  // 何も表示するものが無い場合
  if (
    !(
      transferenceExist ||
      transferenceFrequency ||
      transferenceAbroadExists ||
      transferenceAbroadEnglish
    )
  ) {
    return null;
  }

  return (
    <ContentList>
      {transferenceExist}
      {transferenceFrequency}
      {transferenceAbroadExists}
      {transferenceAbroadEnglish}
    </ContentList>
  );
}

/**
 *  「国内転勤の頻度」
 */
function renderTransferenceFrequency(masterImtRecord) {
  if (!masterImtRecord) return null;

  const label = getModifiedLabel(
    POSITION_DETAIL.TRANSFERENCE_FREQUENCY.ID,
    masterImtRecord,
    POSITION_LABEL_DISPLAY_TYPE.DETAIL,
  );

  // 補足
  const noteText = masterImtRecord?.get("Note");

  // モーダルで表示する補足
  const noteModal = noteText ? <NoteModalBtn contentText={noteText} /> : null;

  return (
    <li key={TRAITS.PTX_TRANSFERENCE_FREQUENCY.ID} className={styles.note}>
      {label}
      {noteModal}
    </li>
  );
}

/**
 *  「海外転勤で現地赴任する際の英語力」
 */
function renderTransferenceAbroadEnglish(masterImtRecord) {
  if (!masterImtRecord) return null;

  const transferenceAbroadEnglishIsUnusedText =
    getTransferenceAbroadEnglishText(masterImtRecord);

  if (!transferenceAbroadEnglishIsUnusedText) return null;

  // 補足
  const noteText = masterImtRecord?.get("Note");

  // モーダルで表示する補足
  const noteModal = noteText ? <NoteModalBtn contentText={noteText} /> : null;

  return (
    <li
      key={TRAITS.PTX_TRANSFERENCE_ABROAD_ENGLISH_IS_UNUSED.ID}
      className={styles.note}
    >
      {transferenceAbroadEnglishIsUnusedText}
      {noteModal}
    </li>
  );
}

/**
 * 「海外転勤で現地赴任する際の英語力」のテキストを返す
 */
function getTransferenceAbroadEnglishText(masterImtRecord) {
  if (
    masterImtRecord.get("ID") ===
    TRAIT_OPTION_VALUES.TRANSFERENCE_ABROAD_ENGLISH_IS_UNUSED.REQUIRED
  ) {
    return "海外転勤で現地赴任する際の英語力は必須";
  }

  if (
    masterImtRecord.get("ID") ===
    TRAIT_OPTION_VALUES.TRANSFERENCE_ABROAD_ENGLISH_IS_UNUSED.NOT_REQUIRED
  ) {
    return "海外転勤で現地赴任する際の英語力は不問";
  }

  return null;
}

/**
 * トレイトの値と補足
 */
function renderContentListItemNoteModal(traitImtRecord) {
  if (!traitImtRecord) {
    return null;
  }

  const label = getLabelFromMasterRecord(traitImtRecord);
  // 補足
  const noteText = traitImtRecord.get("Note");
  // モーダルで表示する補足
  const noteModalBtn = noteText ? (
    <NoteModalBtn contentText={noteText} />
  ) : null;

  return (
    <li key={label} className={styles.item}>
      {label}
      {noteModalBtn}
    </li>
  );
}

/**
 * 「在宅勤務」（企業側「リモート勤務」）
 */
function renderRemoteWork(positionImtRecord) {
  // 在宅勤務
  const remoteWorkMasterImtRecord = positionImtRecord.get(
    POSITION_DETAIL.REMOTE_WORK.ID,
  );

  if (!remoteWorkMasterImtRecord) {
    return null;
  }

  // トレイト値が「なし」の場合
  if (
    remoteWorkMasterImtRecord.get("ID") ===
    EXCEPTION_TRAIT_OPTION.PTX_REMOTE_WORK
  ) {
    // 補足なしの場合は描画しない
    if (!remoteWorkMasterImtRecord.get("Note")) {
      return null;
    }

    return (
      <ContentList>
        <ContentListItem traitImtRecord={remoteWorkMasterImtRecord} />
      </ContentList>
    );
  }

  // 在宅勤務の条件
  const remoteWorkConditionText =
    positionImtRecord.get(POSITION_DETAIL.REMOTE_WORK_CONDITION.ID) ||
    undefined;
  // オフィス出社
  const remoteWorkOfficeFrequency =
    renderRemoteWorkOfficeFrequency(positionImtRecord);

  return (
    <ContentList>
      <ContentListItem
        traitImtRecord={remoteWorkMasterImtRecord}
        noteText={remoteWorkConditionText}
      />
      {remoteWorkOfficeFrequency}
    </ContentList>
  );
}

/**
 * 「オフィス出社」（企業側「出社頻度」）
 */
function renderRemoteWorkOfficeFrequency(positionImtRecord) {
  // オフィス出社
  const traitId = POSITION_DETAIL.REMOTE_WORK_OFFICE_FREQUENCY.ID;
  const masterImtRecord = positionImtRecord.get(traitId);

  if (!masterImtRecord) {
    return null;
  }

  const labelModifier = () => {
    return getModifiedLabel(
      traitId,
      masterImtRecord,
      POSITION_LABEL_DISPLAY_TYPE.DETAIL,
    );
  };

  return (
    <ContentListItem
      traitImtRecord={masterImtRecord}
      labelModifier={labelModifier}
    />
  );
}

/**
 * 「出張」（企業側「出張頻度」）
 */
function renderOfficialTripFrequency(positionImtRecord) {
  // 出張
  const masterImtRecord = positionImtRecord.get(
    POSITION_DETAIL.OFFICIAL_TRIP_FREQUENCY.ID,
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
