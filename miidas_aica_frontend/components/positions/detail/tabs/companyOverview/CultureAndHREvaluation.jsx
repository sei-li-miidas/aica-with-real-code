import PropTypes from "prop-types";

import {
  TRAITS as BUSINESS_TRAITS,
  TRAIT_OPTION_HELPS as BUSINESS_TRAIT_OPTION_HELPS,
} from "@/constants/business";
import {
  POSITION_DETAIL,
  TRAITS as POSITION_TRAITS,
} from "@/constants/position";

import TraitList from "@/components/positions/detail/parts/trait/TraitList";
import TraitListItem from "@/components/positions/detail/parts/trait/TraitListItem";
import ContentList from "@/components/positions/detail/parts/trait/ContentList";
import ContentListRangeItem from "@/components/positions/detail/parts/trait/ContentListRangeItem";

/**
 * 「社風・評価基準」
 */
export default function CultureAndHREvaluation(props) {
  const decisionType = renderDecisionType(props.businessImtRecord);
  const employeeCharacter = renderEmployeeCharacter(props.businessImtRecord);
  const hrEvaluationType = renderHREvaluationType(props.positionImtRecord);

  return (
    <TraitList>
      <TraitListItem
        itemKey={BUSINESS_TRAITS.BTX_DECISION_TYPE.ID}
        itemName="意思決定と裁量"
        content={decisionType}
      />
      <TraitListItem
        itemKey={BUSINESS_TRAITS.BTX_EMPLOYEE_CHARACTER.ID}
        itemName="組織・社員の特徴"
        content={employeeCharacter}
      />
      <TraitListItem
        itemKey={POSITION_TRAITS.PTX_HR_EVALUATION_TYPE.ID}
        itemName="評価基準の特徴"
        content={hrEvaluationType}
      />
    </TraitList>
  );
}

CultureAndHREvaluation.propTypes = {
  businessImtRecord: PropTypes.object.isRequired,
  positionImtRecord: PropTypes.object.isRequired,
};

/**
 * 「意思決定と裁量」
 */
function renderDecisionType(businessImtRecord) {
  const traitId = BUSINESS_TRAITS.BTX_DECISION_TYPE.ID;
  const traitValueImtOrderedMap = businessImtRecord.getIn([
    "Traits",
    traitId,
    "TraitValue",
    "Values",
  ]);

  if (!traitValueImtOrderedMap) {
    return null;
  }

  const noteText = businessImtRecord.getIn([
    "Traits",
    traitId,
    "TraitValue",
    "Text",
  ]);

  return (
    <ContentList>
      <ContentListRangeItem
        traitId={traitId}
        traitValueImtOrderedMap={traitValueImtOrderedMap}
        traitOptionsHelps={BUSINESS_TRAIT_OPTION_HELPS}
        noteText={noteText}
      />
    </ContentList>
  );
}

/**
 * 「組織・社員の特徴」
 */
function renderEmployeeCharacter(businessImtRecord) {
  const traitId = BUSINESS_TRAITS.BTX_EMPLOYEE_CHARACTER.ID;
  const traitValueImtOrderedMap = businessImtRecord.getIn([
    "Traits",
    traitId,
    "TraitValue",
    "Values",
  ]);

  if (!traitValueImtOrderedMap) {
    return null;
  }

  const noteText = businessImtRecord.getIn([
    "Traits",
    traitId,
    "TraitValue",
    "Text",
  ]);

  return (
    <ContentList>
      <ContentListRangeItem
        traitId={traitId}
        traitValueImtOrderedMap={traitValueImtOrderedMap}
        traitOptionsHelps={BUSINESS_TRAIT_OPTION_HELPS}
        noteText={noteText}
      />
    </ContentList>
  );
}

/**
 * 「評価基準の特徴」
 */
function renderHREvaluationType(positionImtRecord) {
  const traitId = POSITION_TRAITS.PTX_HR_EVALUATION_TYPE.ID;
  const traitValueImtOrderedMap = positionImtRecord
    .get(POSITION_DETAIL.HR_EVALUATION_TYPE.ID)
    ?.getValuesOrderedMap();

  if (!traitValueImtOrderedMap) {
    return null;
  }

  const noteText = positionImtRecord.getIn([
    POSITION_DETAIL.HR_EVALUATION_TYPE.ID,
    "Note",
  ]);

  return (
    <ContentList>
      <ContentListRangeItem
        traitId={traitId}
        traitValueImtOrderedMap={traitValueImtOrderedMap}
        noteText={noteText}
      />
    </ContentList>
  );
}
