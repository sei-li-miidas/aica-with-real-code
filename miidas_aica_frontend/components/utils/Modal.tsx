import React, { type ReactNode } from "react";
import ReactDOM from "react-dom";

import { type ClassComponentProps } from "@/types/utility-types";

import Overlay from "./Overlay";
import styles from "./Modal.module.scss";

type DefaultProps = {
  id: string;
  bgClose: () => void;
  scrollElementGetter: () => Element | (Window & typeof globalThis) | null;
};

type Props = ClassComponentProps<
  DefaultProps,
  {
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
  }
>;

/**
 * Modal
 * モーダルをレンダリングするコンポーネント
 */
export default class Modal extends React.Component<Props> {
  static defaultProps: DefaultProps = {
    id: "",
    bgClose: () => {},
    scrollElementGetter: () => null,
  };

  private portalEl: HTMLDivElement | null;

  private htmlEl: HTMLHtmlElement | null;

  private bodyEl: HTMLBodyElement | null;

  private scrollAreaRef: React.RefObject<HTMLDivElement | null>;

  private modalContentRef: React.RefObject<HTMLDivElement | null>;

  private isFocusModal: boolean;

  constructor(props: Props) {
    super(props);

    this.portalEl = null;
    this.htmlEl = null;
    this.bodyEl = null;
    this.scrollAreaRef = React.createRef();
    this.modalContentRef = React.createRef();

    // モーダルをフォーカスするかどうか（表示された直後のフォーカスを制御するため）
    this.isFocusModal = false;

    this.createAndShowPortal = this.createAndShowPortal.bind(this);
    this.hideAndRemovePortal = this.hideAndRemovePortal.bind(this);
  }

  componentDidMount() {
    this.htmlEl = document.getElementsByTagName("html")[0];
    this.bodyEl = document.getElementsByTagName("body")[0];

    if (this.props.display) {
      this.createAndShowPortal();
    }
  }

  componentDidUpdate(prevProps: Props) {
    // umountされずLoadingコンポーネントがずっと存在し続ける場合も、表示・非表示をコントロールする

    // 非表示から表示になる場合
    if (!prevProps.display && this.props.display) {
      // ポータルを作って表示する
      this.createAndShowPortal();
    }

    // 表示から非表示になる場合
    if (prevProps.display && !this.props.display) {
      // ポータルを非表示にして削除する
      this.hideAndRemovePortal();
    }

    // 表示コンテンツが変わった場合はTOPへスクロール
    if (
      this.scrollAreaRef?.current &&
      ((!prevProps.children && this.props.children) ||
        prevProps.children.type?.name !== this.props.children.type?.name)
    ) {
      this.scrollAreaRef.current.scrollTop = 0;
    }

    // モーダル表示後のキー操作で背後の要素が動いてしまう問題を解消するため、表示されるタイミングでFocusを持ってくる
    if (this.isFocusModal) {
      this.modalContentRef?.current?.focus();

      // ポータルが表示された直後の１回限定する
      this.isFocusModal = false;
    }
  }

  componentWillUnmount() {
    if (this.props.display) {
      this.hideAndRemovePortal();
    }
  }

  /**
   * wrap要素クリック時の処理
   */
  handleModalWrapClick = (e: React.MouseEvent<HTMLDivElement>) => {
    // padding設定されている部分がクリックされた場合のみ、bgCloseを実行
    if (e.target === e.currentTarget) {
      this.props.bgClose();
    }
  };

  /**
   * ポータルを作成して表示する
   */
  createAndShowPortal() {
    if (!this.htmlEl || !this.bodyEl) return;

    // 現在のモーダル表示数を文字列で管理する
    if (!this.htmlEl.dataset.modalStack) {
      this.htmlEl.dataset.modalStack = "";
    }
    // 現在のモーダル表示数を1つ増やす
    this.htmlEl.dataset.modalStack = this.htmlEl.dataset.modalStack.concat("|");

    // 親要素にモーダルをレンダリングするためのラッパー要素を追加
    this.portalEl = document.createElement("div");
    this.portalEl.classList.add("modalPortal", "js-ModalPortal");
    this.portalEl.setAttribute("data-testid", "E2eModalPortal");
    this.bodyEl.appendChild(this.portalEl);

    // 最初のレンダリングでthis.portalElがないため描画されないので、ここで強制更新する
    this.forceUpdate();

    // レンダリング直後のcomponentDidUpdateで、フォーカス処理を行う
    this.isFocusModal = true;
  }

  /**
   * ポータルを非表示にして削除する
   */
  hideAndRemovePortal() {
    if (!this.htmlEl || !this.bodyEl) return;

    // 現在のモーダル表示数を1つ減らす
    if (this.htmlEl.dataset.modalStack) {
      this.htmlEl.dataset.modalStack = this.htmlEl.dataset.modalStack.slice(1);
    }
    // ポータルをunmount
    if (this.portalEl) {
      this.bodyEl.removeChild(this.portalEl);
      this.portalEl = null;
    }
  }

  render() {
    return this.portalEl && this.props.display
      ? ReactDOM.createPortal(
          <Overlay
            isDisplay
            scrollElementGetter={this.props.scrollElementGetter}
            onClick={this.props.bgClose}
          >
            <div className={styles.modal} id={this.props.id || ""}>
              <div
                ref={this.scrollAreaRef}
                className={styles.modalWrap}
                onClick={this.handleModalWrapClick}
              >
                <div
                  className={styles.modalContent}
                  tabIndex={-1}
                  ref={this.modalContentRef}
                >
                  {this.props.children}
                </div>
              </div>
            </div>
          </Overlay>,
          this.portalEl,
        )
      : null;
  }
}
