import PropTypes from "prop-types";

import Text2LinkWrapper from "@/components/positions/detail/parts/Text2LinkWrapper";

import styles from "./PositionPR.module.scss";

/**
 * 求人のポイント
 */
export default function PositionPR(props) {
  return (
    <div className={styles.container}>
      <Text2LinkWrapper text={props.contentText} />
    </div>
  );
}

PositionPR.propTypes = {
  contentText: PropTypes.string.isRequired,
};
