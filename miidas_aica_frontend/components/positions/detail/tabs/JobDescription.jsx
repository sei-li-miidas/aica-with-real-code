import React from "react";
import PropTypes from "prop-types";

import {
  POSITION_DETAIL,
  TRAIT_OPTION_VALUES,
  READ_MORE_SECTION_OMITTED_HEIGHT,
} from "@/constants/position";

import SectionListItem from "@/components/positions/detail/parts/SectionListItem";
import TraitList from "@/components/positions/detail/parts/trait/TraitList";
import SectionLayout from "@/components/positions/detail/parts/SectionLayout";
import SectionHeader from "@/components/positions/detail/parts/SectionHeader";
import SectionList from "@/components/positions/detail/parts/SectionList";
import ReadMoreSection from "@/components/positions/detail/parts/ReadMoreSection";

import PositionPR from "./jobDescription/PositionPR";
import CompanyPR from "./jobDescription/CompanyPR";
import JobType from "./jobDescription/JobType";
import SpotJobRequest from "./jobDescription/SpotJobRequest";
import CommissionBusinessDescription from "./jobDescription/CommissionBusinessDescription";
import TraitWorkAddress from "./jobDescription/traitListItem/TraitWorkAddress";
import WorkAddress from "./jobDescription/WorkAddress";
import TraitEmploymentType from "./jobDescription/traitListItem/TraitEmploymentType";
import EmploymentType from "./jobDescription/EmploymentType";
import WorkTime from "./jobDescription/WorkTime";
import Salary from "./jobDescription/Salary";
import RegularOutsourcingFee from "./jobDescription/RegularOutsourcingFee";
import SpotOutsourcingFee from "./jobDescription/SpotOutsourcingFee";
import CommissionOutsourcingFee from "./jobDescription/CommissionOutsourcingFee";
import Holiday from "./jobDescription/Holiday";
import TraitSmokeFree from "./jobDescription/traitListItem/TraitSmokeFree";
import Welfare from "./jobDescription/Welfare";
import OtherJobSpecified from "./jobDescription/OtherJobSpecified";

/**
 * 「募集要項」セクション
 */
export default class JobDescription extends React.Component {
  /**
   * 求人のポイント
   */
  renderPositionPR() {
    const contentText = this.props.positionImtRecord.get(POSITION_DETAIL.PR.ID);

    if (!contentText) {
      return null;
    }

    return (
      <SectionListItem title="求人のポイント">
        <ReadMoreSection
          omittedHeight={READ_MORE_SECTION_OMITTED_HEIGHT.POSITION_PR}
          gaClassName="ga-PositionDetail_PositionPR"
        >
          <PositionPR contentText={contentText} />
        </ReadMoreSection>
      </SectionListItem>
    );
  }

  /**
   * 企業の特徴
   */
  renderCompanyPR() {
    // プレビューの場合は、見出しごと表示しない
    if (this.props.isPreview) {
      return null;
    }

    return (
      <SectionListItem title="企業の特徴">
        <ReadMoreSection
          omittedHeight={READ_MORE_SECTION_OMITTED_HEIGHT.COMPANY_PR}
          gaClassName="ga-PositionDetail_CompanyPR"
        >
          <CompanyPR companyImtRecord={this.props.companyImtRecord} />
        </ReadMoreSection>
      </SectionListItem>
    );
  }

  /**
   * 労働の内容
   * （契約形態によってコンテンツを出し分ける）
   */
  renderJobContent() {
    // 業務委託スポット求人の場合は「依頼内容」
    if (this.props.isSpotOutsourcingPosition) {
      return (
        <SectionListItem title="依頼内容">
          <ReadMoreSection
            omittedHeight={READ_MORE_SECTION_OMITTED_HEIGHT.SPOT_JOB_REQUEST}
            gaClassName="ga-PositionDetail_SpotJobRequest"
          >
            <SpotJobRequest positionImtRecord={this.props.positionImtRecord} />
          </ReadMoreSection>
        </SectionListItem>
      );
    }

    // 業務委託完全歩合求人の場合は「業務内容」
    if (this.props.isCommissionOutsourcingPosition) {
      return (
        <SectionListItem title="業務内容">
          <ReadMoreSection
            omittedHeight={
              READ_MORE_SECTION_OMITTED_HEIGHT.COMMISSION_BUSINESS_DESCRIPTION
            }
            gaClassName="ga-PositionDetail_CommissionBusinessDescription"
          >
            <CommissionBusinessDescription
              positionImtRecord={this.props.positionImtRecord}
            />
          </ReadMoreSection>
        </SectionListItem>
      );
    }

    // それ以外は「仕事内容」
    return (
      <SectionListItem title="仕事内容">
        <ReadMoreSection
          omittedHeight={READ_MORE_SECTION_OMITTED_HEIGHT.JOB_TYPE}
          gaClassName="ga-PositionDetail_JobType"
        >
          <JobType positionImtRecord={this.props.positionImtRecord} />
        </ReadMoreSection>
      </SectionListItem>
    );
  }

  /**
   * 休日休暇
   */
  renderHoliday() {
    // 業務委託求人の場合は非表示
    if (this.props.isOutsourcingPosition) {
      return null;
    }

    return (
      <SectionListItem title="休日休暇">
        <Holiday
          positionImtRecord={this.props.positionImtRecord}
          companyImtRecord={this.props.companyImtRecord}
        />
      </SectionListItem>
    );
  }

  /**
   * 勤務時間
   */
  renderWorkTime() {
    // 業務委託求人の場合は非表示
    if (this.props.isOutsourcingPosition) {
      return null;
    }

    return (
      <SectionListItem title="勤務時間">
        <WorkTime positionImtRecord={this.props.positionImtRecord} />
      </SectionListItem>
    );
  }

  /**
   * 支払いなど
   * （契約形態によってコンテンツを出し分ける）
   */
  renderPayment() {
    // 業務委託レギュラー求人の場合
    if (this.props.isRegularOutsourcingPosition) {
      return (
        <SectionListItem title="報酬（税込）/ 稼働時間">
          <RegularOutsourcingFee
            positionImtRecord={this.props.positionImtRecord}
          />
        </SectionListItem>
      );
    }

    // 業務委託スポット求人の場合
    if (this.props.isSpotOutsourcingPosition) {
      return (
        <SectionListItem title="報酬（税込）/ 稼働時間">
          <SpotOutsourcingFee
            positionImtRecord={this.props.positionImtRecord}
          />
        </SectionListItem>
      );
    }

    // 業務委託完全歩合求人の場合
    if (this.props.isCommissionOutsourcingPosition) {
      return (
        <SectionListItem title="報酬">
          <ReadMoreSection
            omittedHeight={READ_MORE_SECTION_OMITTED_HEIGHT.COMMISSION_FEE}
            gaClassName="ga-PositionDetail_CommissionFee"
          >
            <CommissionOutsourcingFee
              positionImtRecord={this.props.positionImtRecord}
            />
          </ReadMoreSection>
        </SectionListItem>
      );
    }

    // それ以外は「給与」を表示
    return (
      <SectionListItem title="給与">
        <Salary positionImtRecord={this.props.positionImtRecord} />
      </SectionListItem>
    );
  }

  /**
   * 福利厚生
   */
  renderWelfare() {
    // 「受動喫煙対策」
    const smokeFreeMasterImtRecord = this.props.positionImtRecord.get(
      POSITION_DETAIL.SMOKE_FREE.ID,
    );
    // 入力済、かつ「なし（喫煙可）」以外が選択されている場合
    const hasSmokeFreeValue =
      smokeFreeMasterImtRecord &&
      smokeFreeMasterImtRecord.get("ID") !==
        TRAIT_OPTION_VALUES.SMOKE_FREE.NONE;

    // 業務委託求人の場合は「受動喫煙対策」のみ表示
    if (this.props.isOutsourcingPosition) {
      // 受動喫煙対策がある場合
      if (hasSmokeFreeValue) {
        return (
          <SectionListItem title="受動喫煙対策">
            <TraitList>
              <TraitSmokeFree
                positionImtRecord={this.props.positionImtRecord}
                smokeFreeMasterImtRecord={smokeFreeMasterImtRecord}
              />
            </TraitList>
          </SectionListItem>
        );
      }

      return null;
    }

    return (
      <SectionListItem title="福利厚生">
        <Welfare
          positionImtRecord={this.props.positionImtRecord}
          companyImtRecord={this.props.companyImtRecord}
          smokeFreeMasterImtRecord={smokeFreeMasterImtRecord}
          hasSmokeFreeValue={hasSmokeFreeValue}
        />
      </SectionListItem>
    );
  }

  /**
   * 勤務地
   */
  renderWorkAddress() {
    // 業務委託求人の場合は「勤務地」のみ表示
    if (this.props.isOutsourcingPosition) {
      return (
        <SectionListItem title="勤務地">
          <TraitList>
            <TraitWorkAddress
              positionImtRecord={this.props.positionImtRecord}
            />
          </TraitList>
        </SectionListItem>
      );
    }

    return (
      <SectionListItem title="勤務地">
        <WorkAddress positionImtRecord={this.props.positionImtRecord} />
      </SectionListItem>
    );
  }

  /**
   * 雇用形態
   */
  renderEmploymentType() {
    // 業務委託求人の場合は「契約形態」のみ表示
    if (this.props.isOutsourcingPosition) {
      return (
        <SectionListItem title="契約形態">
          <TraitList>
            <TraitEmploymentType
              positionImtRecord={this.props.positionImtRecord}
            />
          </TraitList>
        </SectionListItem>
      );
    }

    return (
      <SectionListItem title="雇用形態">
        <EmploymentType positionImtRecord={this.props.positionImtRecord} />
      </SectionListItem>
    );
  }

  /**
   * その他の特徴
   */
  renderOtherJobSpecified() {
    // 業務委託求人の場合は非表示
    if (this.props.isOutsourcingPosition) {
      return null;
    }

    return (
      <SectionListItem title="その他の特徴">
        <ReadMoreSection
          omittedHeight={READ_MORE_SECTION_OMITTED_HEIGHT.OTHER_JOB_SPECIFIED}
          gaClassName="ga-PositionDetail_OtherJobSpecified"
        >
          <OtherJobSpecified
            positionImtRecord={this.props.positionImtRecord}
            competencyStatus={this.props.competencyStatus}
            isPreview={this.props.isPreview}
            userCompetencyResultImtRecord={
              this.props.userCompetencyResultImtRecord
            }
          />
        </ReadMoreSection>
      </SectionListItem>
    );
  }

  render() {
    const positionPR = this.renderPositionPR();
    const companyPR = this.renderCompanyPR();
    const jobContent = this.renderJobContent();
    const holiday = this.renderHoliday();
    const workTime = this.renderWorkTime();
    const payment = this.renderPayment();
    const welfare = this.renderWelfare();
    const workAddress = this.renderWorkAddress();
    const employmentType = this.renderEmploymentType();
    const otherJobSpecified = this.renderOtherJobSpecified();

    return (
      <SectionLayout>
        <SectionHeader>募集要項</SectionHeader>
        <SectionList>
          {positionPR}
          {companyPR}
          {jobContent}
          {holiday}
          {workTime}
          {payment}
          {welfare}
          {workAddress}
          {employmentType}
          {otherJobSpecified}
        </SectionList>
      </SectionLayout>
    );
  }
}

JobDescription.propTypes = {
  positionImtRecord: PropTypes.object.isRequired,
  companyImtRecord: PropTypes.object.isRequired,
  isOutsourcingPosition: PropTypes.bool.isRequired,
  isRegularOutsourcingPosition: PropTypes.bool.isRequired,
  isSpotOutsourcingPosition: PropTypes.bool.isRequired,
  isCommissionOutsourcingPosition: PropTypes.bool.isRequired,
  competencyStatus: PropTypes.number.isRequired,
  isPreview: PropTypes.bool,
  userCompetencyResultImtRecord: PropTypes.object.isRequired,
};

JobDescription.defaultProps = {
  isPreview: false,
};
