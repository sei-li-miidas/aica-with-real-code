import PropTypes from "prop-types";

import { EVENT_METHOD } from "@/constants/offers/detail";

import Text2LinkWrapper from "@/components/positions/detail/parts/Text2LinkWrapper";
import CollapsibleNote from "@/components/positions/detail/parts/CollapsibleNote";
import TraitList from "@/components/positions/detail/parts/trait/TraitList";
import TraitListItem from "@/components/positions/detail/parts/trait/TraitListItem";

import styles from "./InterviewOnline.module.scss";

/**
 * 「オンライン面接」
 */
export default function InterviewOnline(props) {
  const eventPossibleDateTime = renderEventPossibleDateTime(
    props.interviewImtRecord,
  );
  const interviewTime = props.interviewImtRecord?.getEventTimeForDisplay(
    EVENT_METHOD.ONLINE,
  );

  return (
    <TraitList>
      <TraitListItem
        itemKey="possible_date"
        itemName="面接可能日時"
        content={eventPossibleDateTime}
      />
      <TraitListItem
        itemKey="interview_time"
        itemName="面接所要時間"
        content={interviewTime}
      />
    </TraitList>
  );
}

InterviewOnline.propTypes = {
  interviewImtRecord: PropTypes.object,
};

InterviewOnline.defaultProps = {
  interviewImtRecord: null,
};

/**
 * 面接可能日時
 */
function renderEventPossibleDateTime(interviewImtRecord) {
  const eventPossibleDateTime =
    interviewImtRecord?.getEventPossibleDateTimeForDisplay(EVENT_METHOD.ONLINE);

  if (!eventPossibleDateTime) {
    return null;
  }

  const noteText = interviewImtRecord?.getIn([
    "Online",
    "PossibleTimeComplement",
  ]);

  // 折りたたんで表示する補足
  const collapsibleNote = noteText ? (
    <li className={styles.value}>
      <CollapsibleNote contentText={noteText} />
    </li>
  ) : null;

  return (
    <ol>
      <li className={styles.value}>
        <Text2LinkWrapper text={eventPossibleDateTime} />
      </li>
      {collapsibleNote}
    </ol>
  );
}
