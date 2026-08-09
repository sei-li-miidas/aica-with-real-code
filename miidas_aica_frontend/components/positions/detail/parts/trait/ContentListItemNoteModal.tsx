import { type MFC } from "react";

import TraitRecord from "@/models/position/records/Trait";
import type MasterV2Record from "@/models/records/MasterV2";
import { getLabelFromMasterRecord } from "@/helpers/positionDetail";
import NoteModalBtn from "@/components/positions/detail/parts/NoteModalBtn";

type Props = {
  traitImtRecord?: TraitRecord | MasterV2Record;
  /** traitImtRecord.get('Note')の値以外を使いたい場合にpropで渡す */
  noteText?: string;
};

/*
 * トレイトの値説明（ラベルとモーダルで表示する補足）
 */
const ContentListItemNoteModal: MFC<Props> = ({
  traitImtRecord = undefined,
  noteText = undefined,
}) => {
  const note =
    noteText ||
    (traitImtRecord instanceof TraitRecord ? traitImtRecord.Note : undefined);

  // モーダルで表示する補足
  const noteModalBtn = note ? <NoteModalBtn contentText={note} /> : null;

  const label = getLabelFromMasterRecord(traitImtRecord);

  return (
    <li key={traitImtRecord?.ID}>
      {label}
      {noteModalBtn}
    </li>
  );
};

export default ContentListItemNoteModal;
