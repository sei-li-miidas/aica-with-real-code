import { type MFC } from "react";

import type TraitRecord from "@/models/position/records/Trait";
import type MasterV2Record from "@/models/records/MasterV2";
import ContentMultipleValue from "./ContentMultipleValue";
import ContentListItemNoteModal from "./ContentListItemNoteModal";

type Props = {
  valueImtList: Immutable.List<TraitRecord | MasterV2Record>;
  hasNotApplicable: boolean;
  /** hasNotApplicableがtrueの場合は必要 */
  notApplicableValue?: number;
  /** hasNotApplicableがtrueの場合は必要 */
  optionImtList?: Immutable.List<MasterV2Record>;
};

/**
 * 複数の設定値（補足あり）を横並べで表示
 */
const ContentMultipleValueWithNote: MFC<Props> = ({
  valueImtList,
  hasNotApplicable,
  notApplicableValue = undefined,
  optionImtList = undefined,
}) => {
  /**
   * 横並べのラベル生成（補足あり）
   */
  const itemWithNoteRenderer = (
    masterImtRecord: TraitRecord | MasterV2Record,
  ) => {
    return (
      <ContentListItemNoteModal
        key={`${masterImtRecord.ID}_${masterImtRecord.Name}`}
        traitImtRecord={masterImtRecord}
      />
    );
  };

  return (
    <ContentMultipleValue
      valueImtList={valueImtList}
      hasNotApplicable={hasNotApplicable}
      notApplicableValue={notApplicableValue}
      optionImtList={optionImtList}
      itemRenderer={itemWithNoteRenderer}
    />
  );
};

export default ContentMultipleValueWithNote;
