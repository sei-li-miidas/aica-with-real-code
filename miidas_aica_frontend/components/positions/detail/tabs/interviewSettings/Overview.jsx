import PropTypes from "prop-types";

import { hasSomeTraitValues } from "@/helpers/positionDetail";

import Text2LinkWrapper from "@/components/positions/detail/parts/Text2LinkWrapper";
import TraitList from "@/components/positions/detail/parts/trait/TraitList";
import TraitListItem from "@/components/positions/detail/parts/trait/TraitListItem";
import CollapsibleNote from "@/components/positions/detail/parts/CollapsibleNote";

import styles from "./Overview.module.scss";

/**
 * 選考方法の基本情報
 */
export default function Overview({ interviewImtRecord }) {
  const estimatedTerm = interviewImtRecord?.get("EstimatedTerm");
  const interviewTimes = interviewImtRecord?.getInterviewTimesForDisplay();
  const exam = renderExam(interviewImtRecord);
  const dress = interviewImtRecord?.getCasualDressFlgForDisplay();
  const inteviewer = interviewImtRecord?.getInterviewerForDisplay();
  const contact = renderContact(interviewImtRecord);

  const items = [
    estimatedTerm,
    interviewTimes,
    exam,
    dress,
    inteviewer,
    contact,
  ];

  if (!hasSomeTraitValues(items)) {
    return null;
  }

  return (
    <li>
      <section>
        <TraitList>
          <TraitListItem
            itemKey="estimated_term"
            itemName="選考期間"
            content={estimatedTerm}
          />
          <TraitListItem
            itemKey="interview_times"
            itemName="面接回数"
            content={interviewTimes}
          />
          <TraitListItem itemKey="exam" itemName="試験内容" content={exam} />
          <TraitListItem
            itemKey="dress"
            itemName="面接時の服装"
            content={dress}
          />
          <TraitListItem
            itemKey="interviewer"
            itemName="面接官"
            content={inteviewer}
          />
          <TraitListItem
            itemKey="contact"
            itemName="連絡先"
            content={contact}
          />
        </TraitList>
      </section>
    </li>
  );
}

Overview.propTypes = {
  interviewImtRecord: PropTypes.object,
};

Overview.defaultProps = {
  interviewImtRecord: null,
};

/**
 * 「試験内容」
 */
function renderExam(interviewImtRecord) {
  const value = interviewImtRecord?.getExamForDisplay();

  if (value) {
    const noteText = interviewImtRecord.get("SelectionRemarks");

    // 折りたたんで表示する補足
    const collapsibleNote = noteText ? (
      <li className={styles.value}>
        <CollapsibleNote contentText={noteText} />
      </li>
    ) : null;

    return (
      <ol>
        <li className={styles.value}>
          <Text2LinkWrapper text={value} />
        </li>
        {collapsibleNote}
      </ol>
    );
  }

  return null;
}

/**
 * 「連絡先」
 */
function renderContact(interviewImtRecord) {
  const value = interviewImtRecord?.get("Contact");

  if (value) {
    return <Text2LinkWrapper text={value} />;
  }

  return null;
}
