import React from "react";
import PropTypes from "prop-types";

import { getLabelFromMasterRecord } from "@/helpers/positionDetail";

import { POSITION_DETAIL } from "@/constants/position";

import SectionLayout from "@/components/positions/detail/parts/SectionLayout";

import PositionImages from "@/components/positions/detail/tabs/positionTop/PositionImages";
import WorkTypeAppealBalloon from "@/components/app/shared/positions/outsourcing/WorkTypeAppealBalloon";
import AppealPointTags from "@/components/app/shared/positions/outsourcing/AppealPointTags";

import PositionSummary from "./positionTop/PositionSummary";

import styles from "./PositionTop.module.scss";

/**
 * 「求人TOP」セクション
 */
export default class PositionTop extends React.Component {
  /**
   * リアル職場体験ラベルを表示
   */
  renderWorkExperienceTag() {
    // 業務委託スポット求人は選考方法の設定がないため表示しない
    if (this.props.isSpotOutsourcingPosition) {
      return null;
    }

    const isWorkExperienceEnabled = this.props.interviewImtRecord
      .get("WorkExperience")
      .isWorkExperienceEnabled();

    if (isWorkExperienceEnabled) {
      return (
        <li>
          <div
            className={`${styles.positionTag} ${styles.workExperienceLabel}`}
          >
            リアル職場体験
          </div>
        </li>
      );
    }

    return null;
  }

  /**
   * 契約形態とリアル職場体験タグを表示
   */
  renderEmploymentTypeAndWorkExperienceTag() {
    const employmentTypeImtRecord = this.props.positionImtRecord.get(
      POSITION_DETAIL.EMPLOYMENT_TYPE.ID,
    );
    const workExperienceTag = this.renderWorkExperienceTag();

    return (
      <ul className={styles.positionTags}>
        <li>
          <div
            className={`${styles.positionTag} ${styles.employmentTypeLabel}`}
          >
            {getLabelFromMasterRecord(employmentTypeImtRecord)}
          </div>
        </li>
        {workExperienceTag}
      </ul>
    );
  }

  /**
   * 求人タイトルがあれば表示
   */
  renderPositionTitle() {
    const positionName = this.props.positionImtRecord.get(
      POSITION_DETAIL.TITLE.ID,
    );

    if (!positionName) {
      return null;
    }

    return <h3 className={styles.positionTitle}>{positionName}</h3>;
  }

  /**
   * renderPositionImages
   * 求人画像を表示
   */
  renderPositionImages() {
    return (
      <PositionImages
        positionImageImtList={this.props.positionImtRecord.get("Images")}
      />
    );
  }

  /**
   * マッチ度を描画する
   * TODO: 本体は全画面で/apply/api/positions/will_searchでの結果が必要なので、一旦不要
   */
  // renderMatchRateRank() {
  //   if (!this.props.matchRateRank) {
  //     return null;
  //   }
  //   return <MatchRateRank value={this.props.matchRateRank} />;
  // }

  /**
   * ポジション名/画像/マッチ度を画像有無に応じて描画する
   */
  renderTop() {
    const positionTitle = this.renderPositionTitle();
    // const matchRateRank = this.renderMatchRateRank();
    const positionImageImtList = this.props.positionImtRecord.get("Images");

    if (positionImageImtList.size === 0) {
      return (
        <li>
          <ul>
            <li>
              <div className={styles.titleAndMatchRateRank}>
                {positionTitle}
                {/* <div>{matchRateRank}</div> */}
              </div>
            </li>
          </ul>
        </li>
      );
    }

    const positionImage = this.renderPositionImages();
    return (
      <li>
        <div className={styles.imageArea}>
          {positionImage}
          {/* <div className={styles.matchRateRank}>{matchRateRank}</div> */}
        </div>
        <div className={styles.positionTitleWrap}>{positionTitle}</div>
      </li>
    );
  }

  /**
   * 気になる項目をチェックを描画する
   */
  renderPositionSummary() {
    return (
      <li className={styles.emphasisAreaItem}>
        <PositionSummary
          positionImtRecord={this.props.positionImtRecord}
          companyImtRecord={this.props.companyImtRecord}
          interviewImtRecord={this.props.interviewImtRecord}
        />
      </li>
    );
  }

  /**
   * 業務委託（完全歩合制）のアピールポイント「業務内容」のバルーンを描画する
   */
  renderCommissionWorkTypeAppeal() {
    // 完全歩合制以外では表示しない
    if (!this.props.isCommissionOutsourcingPosition) return null;

    const outsourcingAppealImtRecord =
      this.props.positionImtRecord.get("OutsourcingAppeal");

    if (!outsourcingAppealImtRecord?.isShowWorkTypeAppeal()) return null;

    return (
      <div className={styles.workTypeAppealArea}>
        <WorkTypeAppealBalloon
          outsourcingAppealImtRecord={outsourcingAppealImtRecord}
        />
      </div>
    );
  }

  /**
   * アピールポイントタグを描画する
   */
  renderAppealPointTags() {
    const tagImtList = this.props.positionImtRecord.get("Tags");

    // タグが1つも無い場合は表示しない
    if (tagImtList.size === 0) {
      return null;
    }

    return (
      <div className={styles.appealPointTagsArea}>
        <AppealPointTags tagImtList={tagImtList} />
      </div>
    );
  }

  /**
   * 業務委託の求人TOPを描画する
   */
  renderOutsourcingPositionTop() {
    const employmentTypeAndWorkExperienceTag =
      this.renderEmploymentTypeAndWorkExperienceTag();
    const positionTitle = this.renderPositionTitle();
    const commissionWorkTypeAppeal = this.renderCommissionWorkTypeAppeal();
    const appealPointTags = this.renderAppealPointTags();

    return (
      <SectionLayout>
        {employmentTypeAndWorkExperienceTag}
        <div className={styles.positionTitleOutsourcingWrap}>
          {positionTitle}
          {commissionWorkTypeAppeal}
        </div>
        {appealPointTags}
      </SectionLayout>
    );
  }

  render() {
    // 業務委託の場合
    if (this.props.isOutsourcingPosition) {
      return this.renderOutsourcingPositionTop();
    }

    const top = this.renderTop();
    const positionSummary = this.renderPositionSummary();

    return (
      <section>
        <ul>
          {top}
          <li>
            <ul className={styles.emphasisArea}>{positionSummary}</ul>
          </li>
        </ul>
      </section>
    );
  }
}

PositionTop.propTypes = {
  positionImtRecord: PropTypes.object.isRequired,
  companyImtRecord: PropTypes.object.isRequired,
  interviewImtRecord: PropTypes.object,
  isOutsourcingPosition: PropTypes.bool.isRequired,
  isSpotOutsourcingPosition: PropTypes.bool.isRequired,
  isCommissionOutsourcingPosition: PropTypes.bool.isRequired,
  isUnreadRemindMessage: PropTypes.bool.isRequired,
};

PositionTop.defaultProps = {
  interviewImtRecord: null,
};
