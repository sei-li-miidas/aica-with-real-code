import { type MFC } from "react";

import TraitRecord from "@/models/position/records/Trait";
import type MasterV2Record from "@/models/records/MasterV2";
import { type TRAIT_OPTION_HELPS } from "@/constants/position";
import { type TRAIT_OPTION_HELPS as COMPANY_TRAIT_OPTION_HELPS } from "@/constants/companies";

import { getLabelFromMasterRecord } from "@/helpers/positionDetail";
import NoteModalBtn from "@/components/positions/detail/parts/NoteModalBtn";
import TraitHelpTooltip from "./TraitHelpTooltip";

import styles from "./ContentListItemWithHelp.module.scss";

type Props = {
  traitId: keyof typeof TRAIT_OPTION_HELPS &
    keyof typeof COMPANY_TRAIT_OPTION_HELPS;
  traitImtRecord?: TraitRecord | MasterV2Record;
};

/*
 * トレイトの値説明（ラベルとヘルプツールチップ）
 */
const ContentListItemWithHelp: MFC<Props> = ({
  traitId,
  traitImtRecord = undefined,
}) => {
  const helpTooltip = traitImtRecord ? (
    <TraitHelpTooltip traitId={traitId} traitValue={traitImtRecord.ID} />
  ) : null;

  const label = getLabelFromMasterRecord(traitImtRecord);

  // 補足
  const noteText =
    traitImtRecord instanceof TraitRecord ? traitImtRecord.Note : undefined;
  // モーダルで表示する補足
  const noteModalBtn = noteText ? (
    <NoteModalBtn contentText={noteText} />
  ) : null;

  return (
    <li key={traitId}>
      <span className={styles.labelWithHelp}>
        {label}
        {helpTooltip}
      </span>
      {noteModalBtn}
    </li>
  );
};

export default ContentListItemWithHelp;
