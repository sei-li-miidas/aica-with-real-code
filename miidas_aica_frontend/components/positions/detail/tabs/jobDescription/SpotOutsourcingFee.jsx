import PropTypes from "prop-types";

import { TRAITS } from "@/constants/position";

import TraitList from "@/components/positions/detail/parts/trait/TraitList";
import TraitListItem from "@/components/positions/detail/parts/trait/TraitListItem";
import ContentList from "@/components/positions/detail/parts/trait/ContentList";
import ContentListItem from "@/components/positions/detail/parts/trait/ContentListItem";
import ContentTable from "@/components/positions/detail/parts/trait/ContentTable";
import ContentTableItem from "@/components/positions/detail/parts/trait/ContentTableItem";
import CollapsibleNote from "@/components/positions/detail/parts/CollapsibleNote";

import styles from "./SpotOutsourcingFee.module.scss";

/**
 * 報酬 / 稼働時間（業務委託、スポット）
 */
export default function SpotOutsourcingFee(props) {
  const spotOutsourcingFee = renderSpotOutsourcingFee(props.positionImtRecord);

  const contractExtension = renderContractExtension(props.positionImtRecord);

  return (
    <TraitList>
      <TraitListItem
        itemKey={TRAITS.PTE_SPOT_OUTSOURCING.ID}
        itemName="報酬（税込）稼働時間"
        content={spotOutsourcingFee}
      />
      <TraitListItem
        itemKey={TRAITS.PTE_CONTRACT_EXTENSION.ID}
        itemName="契約延長"
        content={contractExtension}
      />
    </TraitList>
  );
}

SpotOutsourcingFee.propTypes = {
  positionImtRecord: PropTypes.object.isRequired,
};

/**
 * 「報酬（税込）/ 稼働時間」欄の内容
 */
function renderSpotOutsourcingFee(positionImtRecord) {
  const spotOutsourcingImtRecord = positionImtRecord.get("SpotOutsourcing");

  if (!spotOutsourcingImtRecord) {
    return null;
  }

  const fee = spotOutsourcingImtRecord.get("Fee"); // 報酬
  const hourlyFee = spotOutsourcingImtRecord.get("HourlyFee"); // 時給換算
  const workingTime = spotOutsourcingImtRecord.get("WorkingTime"); // 稼働時間

  const content = (
    <>
      <ContentTableItem
        itemKey="fee"
        name="金額"
        value={`${fee.toLocaleString()}円`}
      />
      <ContentTableItem
        itemKey="hourlyFee"
        name="時給換算"
        value={`${hourlyFee.toLocaleString()}円`}
      />
      <ContentTableItem
        itemKey="workingTime"
        name="稼働時間"
        value={`${workingTime}時間`}
      />
    </>
  );

  const note = spotOutsourcingImtRecord.get("Note") ? (
    <CollapsibleNote
      contentText={spotOutsourcingImtRecord.get("Note")}
      className={styles.note}
    />
  ) : null;

  return (
    <>
      <ContentTable>{content}</ContentTable>
      {note}
    </>
  );
}

/**
 * 「契約延長」欄の内容
 */
function renderContractExtension(positionImtRecord) {
  const masterImtRecord = positionImtRecord.get("ContractExtension");

  if (!masterImtRecord) {
    return null;
  }

  return (
    <ContentList>
      <ContentListItem traitImtRecord={masterImtRecord} />
    </ContentList>
  );
}
