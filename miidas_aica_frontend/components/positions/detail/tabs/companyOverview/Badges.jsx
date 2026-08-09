import PropTypes from "prop-types";

import * as ICON from "@/constants/icon";

import HelpTooltipModal from "@/components/utils/HelpTooltipModal";
import SvgIcon from "@/components/utils/SvgIcon";
import CertificationRankBadge from "./badges/CertificationRankBadge";
import HatarakuhitoFirstBadge from "./badges/HatarakuhitoFirstBadge";

import styles from "./Badges.module.scss";

/**
 * 認定バッジ（ミイダス認定、はたらく人ファースト、健康経営）
 */
export default function Badges(props) {
  const miidasCertification = renderMiidasCertification(
    props.certificationRank,
    props.handleCertificationModalOpen,
  );

  // はたらく人ファースト宣言や健康経営優良法人認定のバッジについてのヘルプツールチップ
  const badgeDescriptionHelp = (
    <HelpTooltipModal showModal={props.handleBadgeDescriptionModalOpen} />
  );

  const hatarakuhitoFirstBadge = renderHatarakuhitoFirstBadge(
    props.isAgreedHatarakuhitoFirst,
    badgeDescriptionHelp,
  );

  return (
    <ul className={styles.badgeList}>
      {miidasCertification}
      {hatarakuhitoFirstBadge}
    </ul>
  );
}

Badges.propTypes = {
  certificationRank: PropTypes.number,
  isAgreedHatarakuhitoFirst: PropTypes.bool.isRequired,
  handleBadgeDescriptionModalOpen: PropTypes.func.isRequired,
  handleCertificationModalOpen: PropTypes.func.isRequired,
};

Badges.defaultProps = {
  certificationRank: null,
};

/**
 * 「ミイダス認定」
 */
function renderMiidasCertification(
  certificationRank,
  handleCertificationModalOpen,
) {
  const certificationRankHelpTip = (
    <SvgIcon icon={ICON.COMMON.NOTICE_QUESTION} />
  );

  return certificationRank ? (
    <li>
      <CertificationRankBadge
        certificationRank={certificationRank}
        onClick={handleCertificationModalOpen}
        width={54}
        helpTip={certificationRankHelpTip}
      />
    </li>
  ) : null;
}

/**
 * 「はたらく人ファースト宣言」バッジ
 */
function renderHatarakuhitoFirstBadge(
  isAgreedHatarakuhitoFirst,
  badgeDescriptionHelp,
) {
  return isAgreedHatarakuhitoFirst ? (
    <li>
      <HatarakuhitoFirstBadge helpTip={badgeDescriptionHelp} />
    </li>
  ) : null;
}
