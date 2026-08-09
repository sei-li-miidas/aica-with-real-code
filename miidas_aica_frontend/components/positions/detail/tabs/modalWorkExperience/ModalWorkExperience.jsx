import PropTypes from "prop-types";

import Modal from "@/containers/utils/Modal";
import ModalLayout from "@/components/utils/modalLayout/ModalLayout";

import ModalLayoutHeader from "@/components/utils/modalLayout/ModalLayoutHeader";
import ModalLayoutFooter from "@/components/utils/modalLayout/ModalLayoutFooter";
import { MODAL_BTN_VARIANTS, MODAL_SIZE } from "@/constants/modal";
import ModalLayoutButton from "@/components/utils/modalLayout/ModalLayoutButton";
import styles from "./ModalWorkExperience.module.scss";
import UseCase from "./UseCase";

const ModalWorkExperience = ({ hideModal, isDisplayModal }) => {
  const header = (
    <ModalLayoutHeader title="リアル職場体験とは？" onClose={hideModal} />
  );

  const footer = (
    <ModalLayoutFooter
      primaryBtn={
        <ModalLayoutButton
          variant={MODAL_BTN_VARIANTS.BLUE_FILL}
          onClick={hideModal}
        >
          OK
        </ModalLayoutButton>
      }
    />
  );

  return (
    <Modal display={isDisplayModal}>
      <ModalLayout header={header} footer={footer} pcSize={MODAL_SIZE.LARGE}>
        <div className={styles.wrapper}>
          <p className={styles.main}>
            入社前に
            <span className={styles.primary}>職場のリアルな雰囲気</span>
            を知ることができる体験プログラムです。
          </p>

          <p className={styles.sub}>
            体験を通して職場のことをより深く知り、
            <span className={styles.primary}>
              本当に自分に合うか“入社前に”見極める
            </span>
            ことができます。
          </p>
          <div className={styles.useCases}>
            <UseCase
              image="/assets/next/img/offers/img_work_experience_modal_01.png"
              indexText="実施例 01"
              title="職場見学"
              description="職場を見てまわることで、入社後の自分をイメージしやすくなります。"
            />
            <UseCase
              image="/assets/next/img/offers/img_work_experience_modal_02.png"
              indexText="実施例 02"
              title="実務体験"
              description="実際の業務を体験しながら、自分のスキルが活かせるか確認できます。"
            />
            <UseCase
              image="/assets/next/img/offers/img_work_experience_modal_03.png"
              indexText="実施例 03"
              title="座談会・交流会・相談会"
              description="面接では聞きづらかった疑問や不安も、ざっくばらんに質問できます。"
            />
            <UseCase
              image="/assets/next/img/offers/img_work_experience_modal_04.png"
              indexText="実施例 04"
              title="お茶会・ランチ会・飲み会"
              description="よりリラックスした雰囲気のなかで、交流を深めることができます。"
            />
          </div>
        </div>
      </ModalLayout>
    </Modal>
  );
};

ModalWorkExperience.propTypes = {
  hideModal: PropTypes.func.isRequired,
  isDisplayModal: PropTypes.bool.isRequired,
};

export default ModalWorkExperience;
