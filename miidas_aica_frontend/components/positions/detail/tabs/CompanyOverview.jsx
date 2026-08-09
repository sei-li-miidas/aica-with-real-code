import React from "react";
import PropTypes from "prop-types";

import SectionLayout from "@/components/positions/detail/parts/SectionLayout";
import SectionHeader from "@/components/positions/detail/parts/SectionHeader";
import SectionList from "@/components/positions/detail/parts/SectionList";
import SectionListItem from "@/components/positions/detail/parts/SectionListItem";
import ReadMoreSection from "@/components/positions/detail/parts/ReadMoreSection";
import { READ_MORE_SECTION_OMITTED_HEIGHT } from "@/constants/position";

import Overview from "./companyOverview/Overview";
import BusinessOverview from "./companyOverview/BusinessOverview";
import BusinessSpecified from "./companyOverview/BusinessSpecified";
import CultureAndHREvaluation from "./companyOverview/CultureAndHREvaluation";
import Career from "./companyOverview/Career";
import EmployeeAttributes from "./companyOverview/EmployeeAttributes";
import Badges from "./companyOverview/Badges";
import ModalCertification from "./companyOverview/ModalCertification";

import styles from "./CompanyOverview.module.scss";

/**
 * 「企業情報」セクション
 */
export default class CompanyOverview extends React.Component {
  constructor(props) {
    super(props);

    this.handleCertificationModalOpen =
      this.handleCertificationModalOpen.bind(this);
    this.handleCertificationModalClose =
      this.handleCertificationModalClose.bind(this);

    this.state = {
      isModalCertificationDisplay: false,
    };
  }

  /**
   * ミイダス認定説明モーダルを表示
   */
  handleCertificationModalOpen() {
    this.setState({ isModalCertificationDisplay: true });
  }

  /**
   * ミイダス認定説明モーダルを非表示
   */
  handleCertificationModalClose() {
    this.setState({ isModalCertificationDisplay: false });
  }

  /**
   * 概要
   */
  renderOverview() {
    return (
      <Overview
        positionImtRecord={this.props.positionImtRecord}
        companyImtRecord={this.props.companyImtRecord}
        showModalHPMCertificationDescription={
          this.props.showModalHPMCertificationDescription
        }
      />
    );
  }

  /**
   * 事業情報
   */
  renderBusinessOverview() {
    return (
      <SectionListItem title="事業の特徴">
        <ReadMoreSection
          omittedHeight={READ_MORE_SECTION_OMITTED_HEIGHT.BUSINESS_OVERVIEW}
          gaClassName="ga-PositionDetail_BusinessOverview"
        >
          <div className={styles.container}>
            <BusinessOverview
              businessImtRecord={this.props.businessImtRecord}
              traitOptionLabelImtMap={this.props.businessTraitOptionLabelImtMap}
            />
          </div>
        </ReadMoreSection>
      </SectionListItem>
    );
  }

  /**
   * 事業の詳細
   */
  // renderBusinessSpecified() {
  //   return (
  //     <BusinessSpecified
  //       businessImtRecord={this.props.businessImtRecord}
  //       traitOptionLabelImtMap={this.props.businessTraitOptionLabelImtMap}
  //     />
  //   );
  // }

  /**
   * 「社風・評価基準」
   */
  // renderCultureAndHREvaluation() {
  //   return (
  //     <SectionListItem title="社風・評価基準">
  //       <ReadMoreSection
  //         omittedHeight={
  //           READ_MORE_SECTION_OMITTED_HEIGHT.CULTURE_AND_HR_EVALUATION
  //         }
  //         gaClassName="ga-PositionDetail_CultureAndHREvaluation"
  //       >
  //         <CultureAndHREvaluation
  //           businessImtRecord={this.props.businessImtRecord}
  //           positionImtRecord={this.props.positionImtRecord}
  //         />
  //       </ReadMoreSection>
  //     </SectionListItem>
  //   );
  // }

  /**
   * 「キャリア制度」
   */
  // renderCareer() {
  //   // 業務委託求人の場合は表示しない
  //   if (this.props.isOutsourcingPosition) {
  //     return null;
  //   }

  //   return <Career companyImtRecord={this.props.companyImtRecord} />;
  // }

  /**
   * 「社員属性」
   */
  // renderEmployeeAttributes() {
  //   return (
  //     <SectionListItem title="社員属性">
  //       <ReadMoreSection
  //         omittedHeight={READ_MORE_SECTION_OMITTED_HEIGHT.EMPLOYEE_ATTRIBUTES}
  //         gaClassName="ga-PositionDetail_EmployeeAttributes"
  //       >
  //         <div className={styles.container}>
  //           <EmployeeAttributes
  //             companyImtRecord={this.props.companyImtRecord}
  //             businessImtRecord={this.props.businessImtRecord}
  //             traitOptionLabelImtMap={this.props.businessTraitOptionLabelImtMap}
  //           />
  //         </div>
  //       </ReadMoreSection>
  //     </SectionListItem>
  //   );
  // }

  /**
   * 認定バッジ（ミイダス認定、はたらく人ファースト、健康経営）を表示
   */
  // renderBadges() {
  //   // 業務委託求人の場合は表示しない
  //   if (this.props.isOutsourcingPosition) {
  //     return null;
  //   }

  //   const certificationRank =
  //     this.props.positionImtRecord?.get("CertificationRank");

  //   // はたらく人ファースト宣言バッジの有無
  //   const isAgreedHatarakuhitoFirst = this.props.companyImtRecord?.get(
  //     "IsAgreedHatarakuhitoFirst",
  //   );

  //   // 全てなければ表示しない
  //   if (!certificationRank && !isAgreedHatarakuhitoFirst) {
  //     return null;
  //   }

  //   return (
  //     <li className={styles.badges}>
  //       <Badges
  //         certificationRank={certificationRank}
  //         isAgreedHatarakuhitoFirst={isAgreedHatarakuhitoFirst}
  //         handleBadgeDescriptionModalOpen={this.props.showModalBadgeDescription}
  //         handleCertificationModalOpen={this.handleCertificationModalOpen}
  //       />
  //       <ModalCertification
  //         display={this.state.isModalCertificationDisplay}
  //         onCloseBtnClick={this.handleCertificationModalClose}
  //       ></ModalCertification>
  //     </li>
  //   );
  // }

  render() {
    const overview = this.renderOverview();
    const businessOverview = this.renderBusinessOverview();
    // const businessSpecified = this.renderBusinessSpecified();
    // const cultureAndHREvaluation = this.renderCultureAndHREvaluation();
    // const career = this.renderCareer();
    // const employeeAttributes = this.renderEmployeeAttributes();
    // const badges = this.renderBadges();

    return (
      <SectionLayout>
        <SectionHeader>企業情報</SectionHeader>
        <SectionList>
          <li>{overview}</li>
          {businessOverview}
          {/* {businessSpecified}
          {cultureAndHREvaluation}
          {career}
          {employeeAttributes}
          {badges} */}
        </SectionList>
      </SectionLayout>
    );
  }
}

CompanyOverview.propTypes = {
  businessImtRecord: PropTypes.object.isRequired,
  positionImtRecord: PropTypes.object.isRequired,
  companyImtRecord: PropTypes.object.isRequired,
  showModalBadgeDescription: PropTypes.func.isRequired,
  showModalHPMCertificationDescription: PropTypes.func.isRequired,
  isOutsourcingPosition: PropTypes.bool.isRequired,
};
