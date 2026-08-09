import React, { type ReactNode } from "react";

import { type ClassComponentProps } from "@/types/utility-types";

import styles from "./Overlay.module.scss";

type DefaultProps = {
  isDisplay: boolean;
  className: string;
  onClick: () => void;
  scrollElementGetter: () => Element | (Window & typeof globalThis) | null;
};

type Props = ClassComponentProps<
  DefaultProps,
  {
    children?: ReactNode;
    isDisplay?: boolean;
    className?: string;
    onClick?: () => void;
    scrollElementGetter?: () => Element | (Window & typeof globalThis) | null;
  }
>;

/**
 * オーバーレイのコンポーネント
 * モーダルの背景に利用
 * NOTE: 13以前のiOSやAndroidで背面のコンテンツが動いて（スクロールして）しまう問題に対応するために、
 * タッチイベント発生を監視し、モーダル内のスクロール要素が末端にある場合はイベントをキャンセルする
 */
export default class Overlay extends React.Component<Props> {
  static defaultProps: DefaultProps = {
    isDisplay: false,
    className: "",
    onClick: () => {},
    scrollElementGetter: () => null,
  };

  private overlayRef: React.RefObject<HTMLDivElement | null>;

  private lastClientX: number;

  private lastClientY: number;

  private scrollContentEl: Element | (Window & typeof globalThis) | null;

  constructor(props: Props) {
    super(props);

    this.handleTouchStart = this.handleTouchStart.bind(this);
    this.handleTouchMove = this.handleTouchMove.bind(this);

    this.overlayRef = React.createRef();
    this.lastClientX = 0;
    this.lastClientY = 0;
    this.scrollContentEl = null;
  }

  componentDidMount() {
    if (this.overlayRef?.current) {
      // 表示状態でマウントされる場合、bodyをスクロールできないようにする
      if (this.props.isDisplay) this.disableBodyScroll();
      this.overlayRef.current.addEventListener(
        "touchstart",
        this.handleTouchStart,
      );
      this.overlayRef.current.addEventListener(
        "touchmove",
        this.handleTouchMove,
        {
          passive: false,
        },
      );
    }
  }

  componentDidUpdate(prevProps: Props) {
    if (!prevProps.isDisplay && this.props.isDisplay) {
      // bodyをスクロールできないようにする
      this.disableBodyScroll();
      // タッチ処理の監視開始
      this.overlayRef.current?.addEventListener(
        "touchmove",
        this.handleTouchMove,
        {
          passive: false,
        },
      );
    } else if (prevProps.isDisplay && !this.props.isDisplay) {
      // bodyがスクロールできるようにする
      this.enableBodyScroll();
      // タッチ処理の監視終了
      this.overlayRef.current?.removeEventListener(
        "touchmove",
        this.handleTouchMove,
      );
    }
  }

  componentWillUnmount() {
    if (this.overlayRef?.current) {
      this.enableBodyScroll();
      this.overlayRef.current.removeEventListener(
        "touchstart",
        this.handleTouchStart,
      );
      this.overlayRef.current.removeEventListener(
        "touchmove",
        this.handleTouchMove,
      );
    }
  }

  /**
   * タッチされた瞬間の座標を保存
   * @param {TouchEvent} e
   */
  handleTouchStart(e: TouchEvent) {
    this.lastClientX = e.targetTouches[0].clientX;
    this.lastClientY = e.targetTouches[0].clientY;
  }

  /**
   * タッチでスクロールさせようとした際にイベントの発生要素を起点にスクロール要素を検出
   * その要素のスクロール位置が上端か下端であればタッチイベントをキャンセルする
   * オーバーレイ要素よりも手前にスクロール要素がない場合もタッチイベントをキャンセルする
   * （）
   * @param {TouchEvent} e
   */
  handleTouchMove(e: TouchEvent) {
    if (!(e.target instanceof Element)) return;

    this.scrollContentEl =
      this.props.scrollElementGetter() || this.getScrollElement(e.target);

    if (
      this.scrollContentEl !== window &&
      this.scrollContentEl instanceof Element
    ) {
      const { clientX, clientY, target } = e.targetTouches[0];
      const { top, height } = this.scrollContentEl.getBoundingClientRect();

      // 縦スクロール領域を超えた場合はキャンセル #27941
      if (
        (clientY >= top + height || clientY <= top) &&
        (this.scrollContentEl.scrollTop <= 0 ||
          this.scrollContentEl.scrollTop >=
            Math.round(
              this.scrollContentEl.scrollHeight -
                this.scrollContentEl.clientHeight,
            ))
      ) {
        e.stopPropagation();
        if (e.cancelable) {
          e.preventDefault();
        }
      }

      if (
        (this.lastClientY - clientY <= 0 &&
          this.scrollContentEl.scrollTop === 0) ||
        (this.lastClientY - clientY >= 0 &&
          Math.round(this.scrollContentEl.scrollTop) ===
            Math.round(
              this.scrollContentEl.scrollHeight -
                this.scrollContentEl.clientHeight,
            )) ||
        !this.scrollContentEl.contains(target as Element) // NOTE: scrollContentElの外側のtouchmoveを無効にする
      ) {
        // scrollContentElの横スクロールが許容されていない、または横方向へのタッチ移動がなければイベントをキャンセルする
        // NOTE: タッチ時の横方向へのブレを吸収するために10px（二乗して100）以上の差がないとキャンセル
        const overflowXValues = ["auto", "scroll", "overlay"];
        if (
          !overflowXValues.includes(
            window.getComputedStyle(this.scrollContentEl).overflowX,
          ) ||
          (this.lastClientX - clientX) ** 2 <= 100
        ) {
          e.stopPropagation();
          if (e.cancelable) {
            e.preventDefault();
          }
        }
      }
    } else {
      e.stopPropagation();
      if (e.cancelable) {
        e.preventDefault();
      }
    }
  }

  /**
   * オーバーレイクリック時の処理
   */
  handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    // オーバーレイ要素がクリックされた場合のみ、onClickを実行
    if (e.target === e.currentTarget) {
      this.props.onClick();
    }
  };

  /**
   * イベントの発生したエレメントの親をたどり、overflowの指定がスクローラブルな要素を返す
   * ReactListのスクローラブルな親要素探索ロジックとほぼ同じ
   * Ref: https://github.com/caseywebdev/react-list/blob/master/react-list.es6#L46-L59
   * @param {Element} eventEl
   */
  getScrollElement(eventEl: Element) {
    let el: Element | null = eventEl;
    while (el) {
      switch (window.getComputedStyle(el).overflowY) {
        case "auto":
        case "scroll":
        case "overlay":
          return el;
      }
      el = el.parentElement;
    }
    return window;
  }

  /**
   * bodyのスタイルをスクロール不可能にする
   */
  disableBodyScroll() {
    document.body.style.overflow = "hidden";
  }

  /**
   * bodyのスタイルをスクロール可能にする
   */
  enableBodyScroll() {
    document.body.style.overflow = "";
  }

  render() {
    const classNames = [
      this.props.className,
      styles.overlay,
      !this.props.isDisplay ? styles.isHidden : null,
    ]
      .filter((v) => {
        return v;
      })
      .join(" ");

    return (
      <div
        ref={this.overlayRef}
        className={classNames}
        onClick={this.handleClick}
      >
        {this.props.children}
      </div>
    );
  }
}
