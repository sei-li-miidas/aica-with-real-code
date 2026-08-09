import PropTypes from "prop-types";

import Text2LinkWrapper from "@/components/positions/detail/parts/Text2LinkWrapper";
import ContentHorizontalList from "@/components/positions/detail/parts/trait/ContentHorizontalList";

import BusinessScale from "./BusinessScale";

import styles from "./BusinessOverview.module.scss";

/**
 * 事業情報
 */
export default function BusinessOverview(props) {
  return (
    <>
      {renderBusinessIndustry(props.businessImtRecord)}
      {/* <BusinessScale businessImtRecord={props.businessImtRecord} /> */}
    </>
  );
}

BusinessOverview.propTypes = {
  businessImtRecord: PropTypes.object.isRequired,
};

/**
 * 事業内容メインかどうかを判定する
 */
function isMainIndustry(valueImtRecord) {
  return valueImtRecord.get("IsMain") === true;
}

/**
 * 事業内容（メイン/サブ/詳細）
 */
function renderBusinessIndustry(businessImtRecord) {
  // 事業内容（詳細）（旧 btx_business_text）
  const businessText = businessImtRecord?.getIn(["Industries", "Note"]);
  const industryDetail = businessText ? (
    <li className={styles.industryContentListItem}>
      <Text2LinkWrapper text={businessText} />
    </li>
  ) : null;

  // 事業内容（メイン/サブ）
  const businessIndustryImtList = businessImtRecord?.getIn([
    "Industries",
    "Industries",
  ]);

  // 事業内容メイン
  const industryMainValueImtRecord = businessIndustryImtList
    ?.filter(isMainIndustry)
    .first();
  const industryMain = industryMainValueImtRecord ? (
    <li className={styles.industryContentListItem}>
      <h5 className={styles.industryContentTitle}>【メイン】</h5>
      <p>{industryMainValueImtRecord.get("Name")}</p>
    </li>
  ) : null;

  // 事業内容サブ
  const industrySubValueImtList = businessIndustryImtList
    ?.filterNot(isMainIndustry)
    .map((valueImtRecord) => {
      return (
        <li key={valueImtRecord.get("SmallID")}>
          {valueImtRecord.get("Name")}
        </li>
      );
    });

  const industrySub =
    industrySubValueImtList?.size > 0 ? (
      <li className={styles.industryContentListItem}>
        <h5 className={styles.industryContentTitle}>【サブ】</h5>
        <ContentHorizontalList>{industrySubValueImtList}</ContentHorizontalList>
      </li>
    ) : null;

  return (
    <ul>
      {industryDetail}
      {industryMain}
      {industrySub}
    </ul>
  );
}
