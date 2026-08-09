import PropTypes from "prop-types";

import Text2LinkWrapper from "@/components/positions/detail/parts/Text2LinkWrapper";

import styles from "./CommissionBusinessDescription.module.scss";

/**
 * 「業務内容」
 */
export default function CommissionBusinessDescription(props) {
  const businessDescription = props.positionImtRecord.getIn([
    "CommissionOutsourcing",
    "BusinessDescription",
  ]);

  return (
    <div className={styles.container}>
      <Text2LinkWrapper text={businessDescription} />
    </div>
  );
}

CommissionBusinessDescription.propTypes = {
  positionImtRecord: PropTypes.object.isRequired,
};
