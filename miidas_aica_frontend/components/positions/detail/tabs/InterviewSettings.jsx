import React from "react";
import PropTypes from "prop-types";

import SectionLayout from "@/components/positions/detail/parts/SectionLayout";
import SectionHeader from "@/components/positions/detail/parts/SectionHeader";
import SectionList from "@/components/positions/detail/parts/SectionList";
import SectionListItem from "@/components/positions/detail/parts/SectionListItem";

import Overview from "./interviewSettings/Overview";
import InterviewMeeting from "./interviewSettings/InterviewMeeting";
import InterviewPhone from "./interviewSettings/InterviewPhone";
import InterviewOnline from "./interviewSettings/InterviewOnline";
import WorkExperience from "./interviewSettings/WorkExperience";

/**
 * 「選考方法」セクション
 */
export default class InterviewSettings extends React.Component {
  /**
   * 対面面接
   */
  renderInterviewMeeting() {
    if (!this.props.interviewImtRecord.getIn(["Meeting", "EnableFlg"])) {
      return null;
    }

    return (
      <SectionListItem title="対面面接">
        <InterviewMeeting interviewImtRecord={this.props.interviewImtRecord} />
      </SectionListItem>
    );
  }

  /**
   * 電話面接
   */
  renderInterviewPhone() {
    if (!this.props.interviewImtRecord.getIn(["Phone", "EnableFlg"])) {
      return null;
    }

    return (
      <SectionListItem title="電話面接">
        <InterviewPhone interviewImtRecord={this.props.interviewImtRecord} />
      </SectionListItem>
    );
  }

  /**
   * オンライン面接
   */
  renderInterviewOnline() {
    if (!this.props.interviewImtRecord.getIn(["Online", "EnableFlg"])) {
      return null;
    }

    return (
      <SectionListItem title="オンライン面接">
        <InterviewOnline interviewImtRecord={this.props.interviewImtRecord} />
      </SectionListItem>
    );
  }

  render() {
    const interviewMeeting = this.renderInterviewMeeting();
    const interviewPhone = this.renderInterviewPhone();
    const interviewOnline = this.renderInterviewOnline();

    return (
      <SectionLayout>
        <SectionHeader>選考方法</SectionHeader>
        <SectionList>
          <Overview interviewImtRecord={this.props.interviewImtRecord} />
          {interviewMeeting}
          {interviewPhone}
          {interviewOnline}
          <WorkExperience
            positionDetailImtRecord={this.props.positionDetailImtRecord}
          />
        </SectionList>
      </SectionLayout>
    );
  }
}

InterviewSettings.propTypes = {
  positionDetailImtRecord: PropTypes.object.isRequired,
  interviewImtRecord: PropTypes.object,
};

InterviewSettings.defaultProps = {
  interviewImtRecord: null,
};
