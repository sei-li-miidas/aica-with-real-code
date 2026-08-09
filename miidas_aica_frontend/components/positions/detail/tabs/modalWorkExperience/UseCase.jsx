import Image from "next/image";
import PropTypes from "prop-types";
import styles from "./UseCase.module.scss";

const UseCase = ({ image, indexText, title, description }) => {
  return (
    <div className={styles.container}>
      <Image src={image} width={175} height={98} alt="リアル職場体験実施例" />
      <div className={styles.texts}>
        <p className={styles.index}>{indexText}</p>
        <p className={styles.title}>{title}</p>
        <p className={styles.description}>{description}</p>
      </div>
    </div>
  );
};

UseCase.propTypes = {
  image: PropTypes.string.isRequired,
  indexText: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
};

export default UseCase;
