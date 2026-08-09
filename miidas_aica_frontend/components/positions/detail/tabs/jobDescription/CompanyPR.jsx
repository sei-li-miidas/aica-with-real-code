import PropTypes from "prop-types";

import Text2LinkWrapper from "@/components/positions/detail/parts/Text2LinkWrapper";
import HelpTooltipModal from "@/components/utils/HelpTooltipModal";
// import { showModalHPMCertificationDescription } from '@/actions/positions/detail';
import HPMDeclaration from "./HPMDeclaration";
import styles from "./CompanyPR.module.scss";

/**
 * 企業の特徴
 */
export default function CompanyPR(props) {
  const introduction = props.companyImtRecord.get("Introduction");
  const pr = props.companyImtRecord.get("PR");

  // const dispatch = useDispatch();
  // 健康経営優良法人認定のヘルプボタンのタッチイベントを処理する
  const handleHPMCertificationHelpBtnTouch = () => {
    // TODO: 後でどうやるかを考える
    // return dispatch(showModalHPMCertificationDescription());
  };

  const hpmCertificationYear = props.companyImtRecord.get(
    "HPMCertificationDisplayYear",
  ) ? (
    <p className={styles.hpmCertificationYear}>
      {`${props.companyImtRecord.get("HPMCertificationDisplayYear")}年度 健康経営優良法人認定取得`}
      <HelpTooltipModal showModal={handleHPMCertificationHelpBtnTouch} />
    </p>
  ) : null;
  const hpmCompanyDeclarationText = props.companyImtRecord.get(
    "HPMCompanyDeclaration",
  );
  const hpmCompanyDeclarationTextBox = hpmCompanyDeclarationText ? (
    <HPMDeclaration text={hpmCompanyDeclarationText} />
  ) : null;

  return (
    <div className={styles.container}>
      <Text2LinkWrapper
        text={introduction}
        className={styles.title}
        itemTagName="h4"
      />
      <Text2LinkWrapper text={pr} />
      {hpmCertificationYear}
      {hpmCompanyDeclarationTextBox}
    </div>
  );
}

CompanyPR.propTypes = {
  companyImtRecord: PropTypes.object.isRequired,
};
