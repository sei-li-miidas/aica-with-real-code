import PropTypes from "prop-types";

import { TRAITS } from "@/constants/position";

import TraitList from "@/components/positions/detail/parts/trait/TraitList";
import TraitListItem from "@/components/positions/detail/parts/trait/TraitListItem";
import ContentList from "@/components/positions/detail/parts/trait/ContentList";
import ContentListItem from "@/components/positions/detail/parts/trait/ContentListItem";
import ContentTable from "@/components/positions/detail/parts/trait/ContentTable";
import ContentTableItem from "@/components/positions/detail/parts/trait/ContentTableItem";
import CollapsibleNote from "@/components/positions/detail/parts/CollapsibleNote";

import styles from "./RegularOutsourcingFee.module.scss";

/**
 * 報酬 / 稼働時間（業務委託、レギュラー）
 */
export default function RegularOutsourcingFee(props) {
  const regularOutsourcingFee = renderRegularOutsourcingFee(
    props.positionImtRecord,
  );

  const contractExtension = renderContractExtension(props.positionImtRecord);

  return (
    <TraitList>
      <TraitListItem
        itemKey={TRAITS.PTE_REGULAR_OUTSOURCING.ID}
        itemName="報酬（税込）稼働時間"
        content={regularOutsourcingFee}
      />
      <TraitListItem
        itemKey={TRAITS.PTE_CONTRACT_EXTENSION.ID}
        itemName="契約延長"
        content={contractExtension}
      />
    </TraitList>
  );
}

RegularOutsourcingFee.propTypes = {
  positionImtRecord: PropTypes.object.isRequired,
};

/**
 * 「報酬（税込）/ 稼働時間」欄の内容
 */
function renderRegularOutsourcingFee(positionImtRecord) {
  const regularOutsourcingImtRecord =
    positionImtRecord.get("RegularOutsourcing");

  if (!regularOutsourcingImtRecord) {
    return null;
  }

  const fee = regularOutsourcingImtRecord.get("Fee"); // 報酬
  const monthlyFee = regularOutsourcingImtRecord.get("MonthlyFee"); // 月額換算
  const hourlyFee = regularOutsourcingImtRecord.get("HourlyFee"); // 時給換算
  const incentive = regularOutsourcingImtRecord.get("Incentive"); // インセンティブ
  const contractPeriod = regularOutsourcingImtRecord.get("ContractPeriod"); // 初回契約期間
  const monthlyWorkingTime =
    regularOutsourcingImtRecord.get("MonthlyWorkingTime"); // 月間稼働時間

  // インセンティブがある場合は表示
  const incentiveRow =
    incentive > 0 ? (
      <ContentTableItem
        itemKey="incentive"
        name="インセンティブ"
        value={`〜${incentive.toLocaleString()}万円`}
      />
    ) : null;

  const content = (
    <>
      <ContentTableItem
        itemKey="fee"
        name="総額"
        value={`${fee.toLocaleString()}万円`}
      />
      <ContentTableItem
        itemKey="monthlyFee"
        name="月額約"
        value={`${monthlyFee.toLocaleString()}万円`}
      />
      <ContentTableItem
        itemKey="hourlyFee"
        name="時給換算"
        value={`${hourlyFee.toLocaleString()}円`}
      />
      {incentiveRow}
      <ContentTableItem
        itemKey="contractPeriod"
        name="初回契約期間"
        value={`${contractPeriod}ヶ月`}
      />
      <ContentTableItem
        itemKey="monthlyWorkingTime"
        name="稼働時間"
        value={`${monthlyWorkingTime}時間/月`}
      />
    </>
  );

  const note = regularOutsourcingImtRecord.get("Note") ? (
    <CollapsibleNote
      contentText={regularOutsourcingImtRecord.get("Note")}
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
