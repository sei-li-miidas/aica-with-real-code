import { type MFC } from "react";

import { useModal } from "@/hooks/useModal";
import { isSmartphone } from "@/utils/device";
// 補足モーダル（PC用）
import ModalSupplement from "@/components/positions/detail/tabs/ModalSupplement";
// 補足モーダル（SP用)
import ModalSupplementHalfView from "@/components/positions/detail/tabs/ModalSupplementHalfView";

import styles from "./NoteModalBtn.module.scss";

type Props = {
  contentText: string;
};

/**
 * 補足をモーダルで表示する
 */
const NoteModalBtn: MFC<Props> = ({ contentText }) => {
  const { showModal, hideModal, isDisplayModal } = useModal();

  const modal = isSmartphone() ? (
    <ModalSupplementHalfView
      isDisplay={isDisplayModal}
      content={contentText}
      onClose={hideModal}
    />
  ) : (
    <ModalSupplement
      display={isDisplayModal}
      text={contentText}
      onCloseBtnClick={hideModal}
    />
  );

  return (
    <>
      <button type="button" className={styles.infoBtn} onClick={showModal}>
        [補足]
      </button>
      {modal}
    </>
  );
};

export default NoteModalBtn;
