import { type ReactNode } from "react";
import ModalComponent from "@/components/utils/Modal";

type ModalProps = {
  display: boolean;
  children: ReactNode & {
    // ModalのchildrenがReactコンポーネントの場合、typeがコンポーネントで、type.nameがコンポーネント名になる
    type?: {
      name: string;
    };
  };
  id?: string;
  bgClose?: () => void;
  scrollElementGetter?: () => Element | (Window & typeof globalThis) | null;
};

const Modal = (props: ModalProps) => {
  return (
    <ModalComponent
      display={props.display}
      id={props.id}
      bgClose={props.bgClose}
      scrollElementGetter={props.scrollElementGetter}
    >
      {props.children}
    </ModalComponent>
  );
};

export default Modal;
