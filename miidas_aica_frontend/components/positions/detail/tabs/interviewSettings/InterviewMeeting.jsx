import PropTypes from "prop-types";

import { getHash } from "@/utils";
import { nl2br } from "@/utils/jsx";

import { EVENT_METHOD } from "@/constants/offers/detail";

import Text2LinkWrapper from "@/components/positions/detail/parts/Text2LinkWrapper";
import CollapsibleNote from "@/components/positions/detail/parts/CollapsibleNote";
import TraitList from "@/components/positions/detail/parts/trait/TraitList";
import TraitListItem from "@/components/positions/detail/parts/trait/TraitListItem";

import styles from "./InterviewMeeting.module.scss";

/**
 * 「対面面接」
 */
export default function InterviewMeeting(props) {
  const place = renderPlace(props.interviewImtRecord);
  const eventPossibleDateTime = renderEventPossibleDateTime(
    props.interviewImtRecord,
  );
  const interviewTime = props.interviewImtRecord?.getEventTimeForDisplay(
    EVENT_METHOD.MEETING,
  );
  const transportationPayment = renderTransportationPayment(
    props.interviewImtRecord,
  );

  return (
    <TraitList>
      <TraitListItem itemKey="place" itemName="面接場所" content={place} />
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
      <TraitListItem
        itemKey="transportation_payment"
        itemName="面接交通費"
        content={transportationPayment}
      />
    </TraitList>
  );
}

InterviewMeeting.propTypes = {
  interviewImtRecord: PropTypes.object,
};

InterviewMeeting.defaultProps = {
  interviewImtRecord: null,
};

/**
 * 面接場所
 */
function renderPlace(interviewImtRecord) {
  const placeImtSet = interviewImtRecord?.getIn(["Meeting", "PlaceOptions"]);
  if (!placeImtSet || placeImtSet.size === 0) {
    return null;
  }

  const placeListItems = placeImtSet.map((place) => {
    return (
      <li
        key={`event_place_${getHash(place)}`}
        className={styles.placeListItem}
      >
        {nl2br(place)}
      </li>
    );
  });

  return <ul>{placeListItems}</ul>;
}

/**
 * 面接可能日時
 */
function renderEventPossibleDateTime(interviewImtRecord) {
  const eventPossibleDateTime =
    interviewImtRecord?.getEventPossibleDateTimeForDisplay(
      EVENT_METHOD.MEETING,
    );

  if (!eventPossibleDateTime) {
    return null;
  }

  const noteText = interviewImtRecord?.getIn([
    "Meeting",
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

/**
 * 面接交通費
 */
function renderTransportationPayment(interviewImtRecord) {
  const noteText = interviewImtRecord?.getIn([
    "Meeting",
    "TransportationPaymentRemarks",
  ]);

  // 折りたたんで表示する補足
  const collapsibleNote = noteText ? (
    <li className={styles.value}>
      <CollapsibleNote contentText={noteText} />
    </li>
  ) : null;

  // 交通費支給がある場合、補足文追加
  const showNotice = interviewImtRecord?.getIn([
    "Meeting",
    "TransportationPaymentFlg",
  ]) ? (
    <li className={styles.value}>※支給額の上限は企業によって異なります。</li>
  ) : null;

  return (
    <ol>
      <li className={styles.value}>
        {interviewImtRecord?.getTransportationPaymentForDisplay()}
      </li>
      {collapsibleNote}
      {showNotice}
    </ol>
  );
}
