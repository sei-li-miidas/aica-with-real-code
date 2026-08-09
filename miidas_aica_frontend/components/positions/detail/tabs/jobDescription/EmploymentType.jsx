import PropTypes from "prop-types";

import { getModifiedLabel } from "@/helpers/traitLabel";

import {
  POSITION_DETAIL,
  TRAITS,
  POSITION_LABEL_DISPLAY_TYPE,
} from "@/constants/position";

import TraitList from "@/components/positions/detail/parts/trait/TraitList";
import TraitListItem from "@/components/positions/detail/parts/trait/TraitListItem";
import ContentList from "@/components/positions/detail/parts/trait/ContentList";
import ContentListItem from "@/components/positions/detail/parts/trait/ContentListItem";
import TraitEmploymentType from "./traitListItem/TraitEmploymentType";

/**
 * 「雇用形態」
 */
export default function EmploymentType(props) {
  const contractPeriodDescription = renderContractPeriodDescription(
    props.positionImtRecord,
  );

  const employmentToRegularEmployee = renderEmploymentToRegularEmployee(
    props.positionImtRecord,
  );

  const post = renderPost(props.positionImtRecord);

  return (
    <TraitList>
      <TraitEmploymentType positionImtRecord={props.positionImtRecord} />
      <TraitListItem
        itemKey={TRAITS.PTE_CONTRACT_PERIOD.ID}
        itemName="契約期間"
        content={contractPeriodDescription}
      />
      <TraitListItem
        itemKey={TRAITS.PTE_EMPLOYMENT_TO_REGULAR_EMPLOYEE.ID}
        itemName="正社員登用"
        content={employmentToRegularEmployee}
      />
      <TraitListItem
        itemKey={TRAITS.PTX_POST.ID}
        itemName="役職"
        content={post}
      />
    </TraitList>
  );
}

EmploymentType.propTypes = {
  positionImtRecord: PropTypes.object.isRequired,
};

/**
 * 「契約期間」欄の内容
 */
function renderContractPeriodDescription(positionImtRecord) {
  // 契約期間
  const contractPeriodMasterImtRecord = positionImtRecord.get(
    POSITION_DETAIL.CONTRACT_PERIOD.ID,
  );
  // 契約更新
  const contractRenewalId = POSITION_DETAIL.CONTRACT_RENEWAL.ID;
  const contractRenewalMasterImtRecord =
    positionImtRecord.get(contractRenewalId);

  // 何も表示するものが無い場合
  if (!(contractPeriodMasterImtRecord || contractRenewalMasterImtRecord)) {
    return null;
  }

  const contractPeriod = contractPeriodMasterImtRecord ? (
    <ContentListItem traitImtRecord={contractPeriodMasterImtRecord} />
  ) : null;

  const labelModifier = () => {
    return getModifiedLabel(
      contractRenewalId,
      contractRenewalMasterImtRecord,
      POSITION_LABEL_DISPLAY_TYPE.DETAIL,
    );
  };
  const contractRenewal = contractRenewalMasterImtRecord ? (
    <ContentListItem
      traitImtRecord={contractRenewalMasterImtRecord}
      labelModifier={labelModifier}
      noteText={positionImtRecord.get(POSITION_DETAIL.CONTRACT_RENEWAL_TEXT.ID)}
    />
  ) : null;

  return (
    <ContentList>
      {contractPeriod}
      {contractRenewal}
    </ContentList>
  );
}

/**
 * 「正社員登用」欄の内容
 */
function renderEmploymentToRegularEmployee(positionImtRecord) {
  const masterImtRecord = positionImtRecord.get(
    POSITION_DETAIL.EMPLOYMENT_TO_REGULAR_EMPLOYEE.ID,
  );

  if (!masterImtRecord) {
    return null;
  }

  return (
    <ContentList>
      <ContentListItem traitImtRecord={masterImtRecord} />
    </ContentList>
  );
}

/**
 * 「役職」欄の内容
 */
function renderPost(positionImtRecord) {
  const masterImtRecord = positionImtRecord.get(POSITION_DETAIL.POST.ID);

  if (!masterImtRecord) {
    return null;
  }

  return (
    <ContentList>
      <ContentListItem traitImtRecord={masterImtRecord} />
    </ContentList>
  );
}
