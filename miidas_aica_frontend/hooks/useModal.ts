import { useCallback, useState } from "react";

/**
 * useModal
 * モーダルを扱うためのhooks
 */
export const useModal = (initialIsDisplayModal = false) => {
  const [isDisplayModal, setIsDisplayModal] = useState(initialIsDisplayModal);

  const showModal = useCallback(() => {
    setIsDisplayModal(true);
  }, []);

  const hideModal = useCallback(() => {
    setIsDisplayModal(false);
  }, []);

  const toggleModal = useCallback(() => {
    setIsDisplayModal((prev) => !prev);
  }, []);

  return {
    /** モーダルを開く */
    showModal,
    /** モーダルを閉じる */
    hideModal,
    /** モーダルの表示状態をトグルする */
    toggleModal,
    /** モーダルの表示状態 */
    isDisplayModal,
  };
};
