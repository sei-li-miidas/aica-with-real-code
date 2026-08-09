import PropTypes from "prop-types";

import { POSITION_DETAIL, TRAITS } from "@/constants/position";

import Text2LinkWrapper from "@/components/positions/detail/parts/Text2LinkWrapper";
import TraitList from "@/components/positions/detail/parts/trait/TraitList";
import TraitListItem from "@/components/positions/detail/parts/trait/TraitListItem";
import ContentList from "@/components/positions/detail/parts/trait/ContentList";
import ContentListItem from "@/components/positions/detail/parts/trait/ContentListItem";

/**
 * 「勤務時間」
 */
export default function WorkTime(props) {
  const worktime = renderWorktime(props.positionImtRecord);

  const overtimeAvg = renderOvertimeAvg(props.positionImtRecord);

  return (
    <TraitList>
      <TraitListItem
        itemKey={TRAITS.PTX_WORKTIME.ID}
        itemName="勤務時間"
        content={worktime}
      />
      <TraitListItem
        itemKey={TRAITS.PTX_OVERTIME_AVG.ID}
        itemName="平均残業時間"
        content={overtimeAvg}
      />
    </TraitList>
  );
}

WorkTime.propTypes = {
  positionImtRecord: PropTypes.object.isRequired,
};

/**
 * 「勤務時間」欄の内容
 */
function renderWorktime(positionImtRecord) {
  const worktimeMasterImtRecord = positionImtRecord.get(
    POSITION_DETAIL.WORK_TIME_SYSTEM.ID,
  );
  const worktimeText = positionImtRecord.get(POSITION_DETAIL.WORK_TIME.ID);
  const worktimeNightsShiftMasterImtRecord = positionImtRecord.get(
    POSITION_DETAIL.WORK_TIME_NIGHTS_SHIFT.ID,
  );

  if (
    !(
      worktimeMasterImtRecord ||
      worktimeText ||
      worktimeNightsShiftMasterImtRecord
    )
  ) {
    return null;
  }

  return (
    <ContentList>
      <ContentListItem traitImtRecord={worktimeMasterImtRecord} />
      <li>
        <Text2LinkWrapper text={worktimeText} />
      </li>
      <ContentListItem traitImtRecord={worktimeNightsShiftMasterImtRecord} />
    </ContentList>
  );
}

/**
 * 「平均残業時間」欄の内容
 */
function renderOvertimeAvg(positionImtRecord) {
  const masterImtRecord = positionImtRecord.get(
    POSITION_DETAIL.OVERTIME_AVG.ID,
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
