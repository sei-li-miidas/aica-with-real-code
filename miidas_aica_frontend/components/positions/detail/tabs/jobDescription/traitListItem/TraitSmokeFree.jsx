import PropTypes from "prop-types";

import { POSITION_DETAIL } from "@/constants/position";
import TraitListItem from "@/components/positions/detail/parts/trait/TraitListItem";
import ContentList from "@/components/positions/detail/parts/trait/ContentList";
import ContentListItem from "@/components/positions/detail/parts/trait/ContentListItem";

/**
 * 受動喫煙対策
 */
export default function TraitSmokeFree({
  positionImtRecord,
  smokeFreeMasterImtRecord,
}) {
  const smokeFree = renderSmokeFree(
    positionImtRecord,
    smokeFreeMasterImtRecord,
  );

  return (
    <TraitListItem
      itemKey={POSITION_DETAIL.SMOKE_FREE.ID}
      itemName="受動喫煙対策"
      content={smokeFree}
    />
  );
}

TraitSmokeFree.propTypes = {
  positionImtRecord: PropTypes.object.isRequired,
  smokeFreeMasterImtRecord: PropTypes.object.isRequired,
};

/**
 * 「受動喫煙対策」欄の内容
 */
function renderSmokeFree(positionImtRecord, smokeFreeMasterImtRecord) {
  // 「受動喫煙対策」の具体的な内容
  const smokeFreeEnvironmentMasterImtRecord = positionImtRecord.get(
    POSITION_DETAIL.SMOKE_FREE_ENVIRONMENT.ID,
  );

  return (
    <ContentList>
      <ContentListItem traitImtRecord={smokeFreeMasterImtRecord} />
      <ContentListItem traitImtRecord={smokeFreeEnvironmentMasterImtRecord} />
    </ContentList>
  );
}
