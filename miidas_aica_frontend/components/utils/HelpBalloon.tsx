import React, { type ReactNode, type ComponentPropsWithoutRef } from "react";
import ReactDOM from "react-dom";

import { clsx } from "@/utils/className";
import { nl2br } from "@/utils/jsx";
import { isPCWidth, isSPWidth } from "@/utils/screenWidth";
import { isSmartphone } from "@/utils/device";
import { type ClassComponentProps } from "@/types/utility-types";
import styles from "./HelpBalloon.module.scss";

type Position = "top" | "bottom";

type Help = {
  title?: ReactNode;
  text: ReactNode;
};

type DefaultProps = {
  className: string;
  onClose: ComponentPropsWithoutRef<"button">["onClick"];
  position: Position;
  bottom: string;
  isOnModal: boolean;
  isCloseButton: boolean;
  isArrowHidden: boolean;
};

type Props = ClassComponentProps<
  DefaultProps,
  {
    help: Help;
    display: boolean;
    className?: string;
    onClose?: ComponentPropsWithoutRef<"button">["onClick"];
    position?: Position; // top or bottomを指定する（default値はtop）
    bottom?: string;
    isOnModal?: boolean;
    isCloseButton?: boolean;
    isArrowHidden?: boolean;
  }
>;

/**
 * ヘルプバルーンコンポーネント
 */
export default class HelpBalloon extends React.Component<Props> {
  static defaultProps: DefaultProps = {
    className: "",
    onClose: () => {},
    position: "top",
    bottom: "",
    isOnModal: false,
    isCloseButton: false,
    isArrowHidden: false,
  };

  /** ターゲット要素を見つけるためのダミー要素 */
  private dummyRef: React.RefObject<HTMLDivElement | null>;

  /** バルーンのRef */
  private balloonRef: React.RefObject<HTMLDivElement | null>;

  /** 矢印のRef */
  private arrowRef: React.RefObject<HTMLDivElement | null>;

  /** バルーン表示の対象になる要素のNode */
  private triggerNode: HTMLElement | null;

  constructor(props: Props) {
    super(props);

    this.dummyRef = React.createRef();
    this.balloonRef = React.createRef();
    this.arrowRef = React.createRef();
    this.triggerNode = null;
    this.setHelpBalloonPosition = this.setHelpBalloonPosition.bind(this);
  }

  componentDidMount() {
    this.initialize();
  }

  componentDidUpdate(prevProps: Props) {
    if (!prevProps.display && this.props.display) {
      this.initialize();
    }
  }

  componentWillUnmount() {
    // バインドしたイベントを削除する
    window.removeEventListener("resize", this.setHelpBalloonPosition);
    window.removeEventListener("scroll", this.setHelpBalloonPosition);
  }

  /**
   * 親DOMを返す
   */
  getParentDom() {
    return (
      document.getElementById("App") ||
      document.getElementById("Preview") ||
      document.getElementById("Secret")
    );
  }

  /**
   * ヘルプバルーンの位置を設定する
   */
  setHelpBalloonPosition() {
    if (
      !this.balloonRef?.current ||
      !this.arrowRef?.current ||
      !this.triggerNode
    )
      return;
    // 表示対象の座標を取得
    const triggerClientRect = this.triggerNode.getBoundingClientRect();
    // ドキュメント幅
    const documentWidth = document.body.clientWidth;
    // バルーン要素の横幅
    const balloonWidth = this.balloonRef.current.offsetWidth;
    // バルーン要素の縦幅
    const balloonHeight = this.balloonRef.current.offsetHeight;
    // 矢印の横幅
    const arrowWidth = this.arrowRef.current.offsetWidth;
    // 表示対象要素のトップ位置
    const triggerElTop = triggerClientRect.top;
    // 表示対象要素の左位置
    const triggerElLeft = triggerClientRect.left;
    // 表示対象要素の左右中心位置
    const triggerElCenter = triggerElLeft + this.triggerNode.offsetWidth / 2;
    // 表示対象要素の高さ
    const triggerElHeight = this.triggerNode.offsetHeight;
    // バルーン要素の左位置
    const balloonLeft =
      triggerElCenter - balloonWidth / 2 > 0
        ? triggerElCenter - balloonWidth / 2
        : 0;
    // #68211 PC幅の場合のみツールチップが画面左のタブバーに隠れるのを防ぐため、balloonLeftがMainContentの外に出ないようにする
    const mainContentLeft = document
      .getElementById("JsMainContent")
      ?.getBoundingClientRect().x;
    const balloonLeftForPCWidth =
      mainContentLeft !== undefined && balloonLeft < mainContentLeft
        ? mainContentLeft
        : balloonLeft;
    // 画面右にはみ出した場合に相殺する値
    const balloonRightDiff =
      balloonLeft + balloonWidth - documentWidth > 0
        ? balloonLeft + balloonWidth - documentWidth
        : 0;
    // 矢印の左位置
    let arrowLeft = 0;

    // ヘルプの左右位置を設定
    if (isPCWidth()) {
      // 表示が右にはみ出してしまう場合は、rightを0にする
      if (balloonRightDiff) {
        this.balloonRef.current.style.right = "0";
        this.balloonRef.current.style.left = "";
      } else {
        this.balloonRef.current.style.left = `${balloonLeftForPCWidth}px`;
      }
    } else {
      this.balloonRef.current.style.left = "0";
    }

    // ヘルプの上下位置を設定
    if (this.props.bottom && isSmartphone()) {
      this.balloonRef.current.style.bottom = this.props.bottom;
    } else if (this.props.position === "bottom") {
      this.balloonRef.current.style.top = `${triggerElTop + triggerElHeight + 5}px`;
    } else {
      this.balloonRef.current.style.top = `${triggerElTop - balloonHeight - 5}px`;
    }

    // 矢印の位置を設定する
    if (isSPWidth()) {
      const balloonPadding = this.props.isOnModal ? 32 : 16; // styles.helpBalloonに定義されている左右の余白（SP版でモーダル上に表示する場合は余白を大きくしているので）
      arrowLeft = triggerElCenter - arrowWidth / 2 - balloonPadding;
    } else {
      // 画面右にはみ出す場合があるのでballoonRightDiffで相殺する
      arrowLeft =
        triggerElCenter -
        balloonLeftForPCWidth -
        arrowWidth / 2 +
        balloonRightDiff;
    }
    this.arrowRef.current.style.left = `${arrowLeft}px`;

    // 位置設定完了後表示する
    this.balloonRef.current.style.visibility = "visible";

    if (!isSmartphone() && this.balloonRef?.current.style.bottom) {
      // spからpcへ切り替えた際に、bottomの値が残るとdivの縦幅が伸びてしまう
      this.balloonRef.current.style.bottom = "";
    }
  }

  /**
   * windowに対してリサイズイベントリスナーをセットする
   */
  setResizeEventListener() {
    // リサイズイベントをバインド
    window.addEventListener("resize", this.setHelpBalloonPosition);
  }

  /**
   * スクロール対象のコンテナ要素を取得し、イベントリスナーをセットする
   */
  setScrollEventListener() {
    // スクロールイベントをバインド
    window.addEventListener("scroll", this.setHelpBalloonPosition);
  }

  /**
   * コンポーネントがマウントまたはアップデートされた際に行う処理
   */
  initialize() {
    if (this.balloonRef.current) {
      // 一つ前の要素をトリガーとする
      if (this.dummyRef?.current?.previousSibling instanceof HTMLElement) {
        this.triggerNode = this.dummyRef?.current.previousSibling;
      }
      this.setHelpBalloonPosition();
      this.setResizeEventListener();
      this.setScrollEventListener();
    }
  }

  /**
   * 閉じるボタンを描画する
   */
  renderCloseButton() {
    if (!this.props.isCloseButton) return null;

    return (
      <button
        aria-label="閉じる"
        type="button"
        className={styles.closeBtn}
        onClick={this.props.onClose}
      />
    );
  }

  /**
   * タイトルを描画する
   */
  renderBalloonTitle() {
    if (!this.props.help.title) return null;
    return <strong className={styles.title}>{this.props.help.title}</strong>;
  }

  /**
   * ヘルプバルーンを描画する
   */
  renderBalloon() {
    const { className, help, display, position } = this.props;

    // 親DOMを取得
    const parentDom = this.getParentDom();

    if (!display || !parentDom) return null;

    const closeButton = this.renderCloseButton();
    const title = this.renderBalloonTitle();

    // propsからバルーンの表示位置クラスを振り分ける
    const arrowClass = clsx(
      position === "bottom"
        ? `${styles.arrow} ${styles.arrowBottom}`
        : `${styles.arrow} ${styles.arrowTop}`,
      this.props.isArrowHidden && styles.arrowHidden,
    );

    const helpBalloonCls = clsx(
      styles.helpBalloon,
      // モーダル上に表示する場合は余白調整クラスを追加
      this.props.isOnModal && styles.onModal,
      // 閉じるボタン有りの場合の調整クラスを追加
      this.props.isCloseButton && styles.withCloseBtn,
      className,
    );

    const text = typeof help.text === "string" ? nl2br(help.text) : help.text;

    return ReactDOM.createPortal(
      <div className={helpBalloonCls} ref={this.balloonRef}>
        <div className={styles.inner}>
          {closeButton}
          {title}
          <p className={styles.text}>{text}</p>
          <span className={arrowClass} ref={this.arrowRef} />
        </div>
      </div>,
      parentDom,
    );
  }

  render() {
    return <span ref={this.dummyRef}>{this.renderBalloon()}</span>;
  }
}
