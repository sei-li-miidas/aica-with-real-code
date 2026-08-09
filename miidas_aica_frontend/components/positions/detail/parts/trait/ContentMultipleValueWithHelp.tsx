import type Immutable from "immutable";
import { type MFC } from "react";

import { type TRAIT_OPTION_HELPS } from "@/constants/position";
import { type TRAIT_OPTION_HELPS as COMPANY_TRAIT_OPTION_HELPS } from "@/constants/companies";
import type TraitRecord from "@/models/position/records/Trait";
import type MasterV2Record from "@/models/records/MasterV2";
import ContentMultipleValue from "./ContentMultipleValue";
import ContentListItemWithHelp from "./ContentListItemWithHelp";

type Props = {
  traitId: keyof typeof TRAIT_OPTION_HELPS &
    keyof typeof COMPANY_TRAIT_OPTION_HELPS;
  valueImtList: Immutable.List<TraitRecord | MasterV2Record>;
  hasNotApplicable: boolean;
  /** hasNotApplicableがtrueの場合は必要 */
  notApplicableValue?: number;
  /** hasNotApplicableがtrueの場合は必要 */
  optionImtList?: Immutable.List<MasterV2Record>;
};

/**
 * 複数の設定値（ヘルプツールチップあり）を横並べで表示
 */
const ContentMultipleValueWithHelp: MFC<Props> = ({
  traitId,
  valueImtList,
  hasNotApplicable,
  notApplicableValue = undefined,
  optionImtList = undefined,
}) => {
  /**
   * itemWithHelpRenderer
   * 横並べのラベル生成（ヘルプツールチップあり）
   */
  const itemWithHelpRenderer = (
    masterImtRecord: TraitRecord | MasterV2Record,
  ) => {
    return (
      <ContentListItemWithHelp
        key={masterImtRecord.Name}
        traitId={traitId}
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
      itemRenderer={itemWithHelpRenderer}
    />
  );
};

export default ContentMultipleValueWithHelp;
