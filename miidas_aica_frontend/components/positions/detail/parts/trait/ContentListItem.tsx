import { type MFC } from "react";

import type TraitRecord from "@/models/position/records/Trait";
import type TraitEmploymentTypeRecord from "@/models/position/records/TraitEmploymentType";
import type SpotJobRequestRecord from "@/models/records/SpotJobRequest";
import { getLabelFromMasterRecord } from "@/helpers/positionDetail";
import CollapsibleNote from "@/components/positions/detail/parts/CollapsibleNote";
import styles from "./ContentListItem.module.scss";

type Flg = {
  On: boolean;
  Name: string;
};

type Props = {
  /** トレイトに応じて型が異なる */
  traitImtRecord?:
    | TraitRecord
    | TraitEmploymentTypeRecord
    | SpotJobRequestRecord
    | Flg;
  /** traitImtRecord.get('Note')の値以外を使いたい場合にpropで渡す */
  noteText?: string;
  /** ラベルに変更を加えたい場合にpropで渡す */
  labelModifier?: (label: string) => string;
};

/**
 * トレイトの値説明（ラベルと補足）
 */
const ContentListItem: MFC<Props> = ({
  traitImtRecord = undefined,
  noteText = undefined,
  labelModifier = (label) => label, // labelをそのまま返す
}) => {
  // 補足
  let note: string = "";
  if (noteText !== undefined) {
    note = noteText;
  } else if (traitImtRecord && "Note" in traitImtRecord) {
    note = traitImtRecord.Note;
  }

  // トレイトの値ラベル
  const valueLabel = traitImtRecord ? (
    <li className={styles.item}>
      {labelModifier(getLabelFromMasterRecord(traitImtRecord))}
    </li>
  ) : null;

  // 何も表示するものが無い場合
  if (!valueLabel) {
    return null;
  }

  // 折りたたんで表示する補足
  const collapsibleNote = note ? renderCollapsibleNote(note) : null;

  return (
    <>
      {valueLabel}
      {collapsibleNote}
    </>
  );
};

export default ContentListItem;

/**
 * 補足を折りたたんで表示する
 */
function renderCollapsibleNote(noteText: string) {
  return (
    <li>
      <CollapsibleNote contentText={noteText} />
    </li>
  );
}
