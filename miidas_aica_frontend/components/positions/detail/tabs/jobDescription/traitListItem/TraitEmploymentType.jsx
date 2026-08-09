import PropTypes from "prop-types";

import { getModifiedLabel } from "@/helpers/traitLabel";

import {
  TRAITS,
  POSITION_DETAIL,
  POSITION_LABEL_DISPLAY_TYPE,
} from "@/constants/position";

import TraitListItem from "@/components/positions/detail/parts/trait/TraitListItem";
import ContentList from "@/components/positions/detail/parts/trait/ContentList";
import ContentListItem from "@/components/positions/detail/parts/trait/ContentListItem";

/**
 * 契約形態
 */
export default function TraitEmploymentType(props) {
  const employmentType = renderEmploymentType(props.positionImtRecord);

  return (
    <TraitListItem
      itemKey={TRAITS.PTX_EMPLOYMENT_TYPE.ID}
      itemName="契約形態"
      content={employmentType}
    />
  );
}

TraitEmploymentType.propTypes = {
  positionImtRecord: PropTypes.object.isRequired,
};

/**
 * 「契約形態」欄の内容
 */
function renderEmploymentType(positionImtRecord) {
  // 契約形態
  const employmentTypeMasterImtRecord = positionImtRecord.get(
    POSITION_DETAIL.EMPLOYMENT_TYPE.ID,
  );
  // 試用期間
  const probationId = POSITION_DETAIL.PROBATION.ID;
  const probationMasterImtRecord = positionImtRecord.get(probationId);

  // 表示するものが無い場合
  if (!(employmentTypeMasterImtRecord || probationMasterImtRecord)) {
    return null;
  }

  const employmentType = employmentTypeMasterImtRecord ? (
    <ContentListItem traitImtRecord={employmentTypeMasterImtRecord} />
  ) : null;

  const labelModifier = () => {
    return getModifiedLabel(
      probationId,
      probationMasterImtRecord,
      POSITION_LABEL_DISPLAY_TYPE.DETAIL,
    );
  };
  const probation = probationMasterImtRecord ? (
    <ContentListItem
      traitImtRecord={probationMasterImtRecord}
      labelModifier={labelModifier}
    />
  ) : null;

  return (
    <ContentList>
      {employmentType}
      {probation}
    </ContentList>
  );
}
