import PropTypes from "prop-types";

import { TRAITS } from "@/constants/position";

import Text2LinkWrapper from "@/components/positions/detail/parts/Text2LinkWrapper";
import TraitList from "@/components/positions/detail/parts/trait/TraitList";
import TraitListItem from "@/components/positions/detail/parts/trait/TraitListItem";
import ContentList from "@/components/positions/detail/parts/trait/ContentList";
import ContentListItem from "@/components/positions/detail/parts/trait/ContentListItem";

/**
 * 「依頼内容」
 */
export default function SpotJobRequest(props) {
  // 依頼内容
  const request = renderRequest(props.positionImtRecord);
  // 依頼内容（詳細）
  const requestDescription = props.positionImtRecord.get("SpotJobDescription");
  const requestDetail = <Text2LinkWrapper text={requestDescription} />;

  return (
    <TraitList>
      <TraitListItem
        itemKey={TRAITS.PTE_SPOT_JOB_REQUEST.ID}
        itemName="依頼内容"
        content={request}
      />
      <TraitListItem
        itemKey={TRAITS.PTE_SPOT_JOB_DESCRIPTION.ID}
        itemName="依頼内容（詳細）"
        content={requestDetail}
      />
    </TraitList>
  );
}

SpotJobRequest.propTypes = {
  positionImtRecord: PropTypes.object.isRequired,
};

/**
 * 「依頼内容」欄の内容
 */
function renderRequest(positionImtRecord) {
  const masterImtRecord = positionImtRecord.get("SpotJobRequest");

  if (!masterImtRecord) {
    return null;
  }

  return (
    <ContentList>
      <ContentListItem traitImtRecord={masterImtRecord} />
    </ContentList>
  );
}
