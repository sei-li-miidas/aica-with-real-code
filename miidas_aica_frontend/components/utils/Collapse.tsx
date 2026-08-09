import React from "react";
import { EXPAND_BUTTON_CLS } from "@/constants/app";
import { clsx } from "@/utils/className";

import { type ClassComponentProps } from "@/types/utility-types";
import styles from "./Collapse.module.scss";

type DefaultProps = {
  className: string;
  showBtnLabel: string;
  hideBtnLabel: string;
};

type Props = ClassComponentProps<
  DefaultProps,
  {
    children: React.ReactNode;
    className?: string;
    showBtnLabel?: string;
    hideBtnLabel?: string;
  }
>;

type State = {
  isExpanded: boolean;
};

/**
 * コンテンツを展開/折りたたむトグルボタンを表示する
 */
export default class Collapse extends React.Component<Props, State> {
  static defaultProps: DefaultProps = {
    className: "",
    showBtnLabel: "詳細を見る",
    hideBtnLabel: "詳細を閉じる",
  };

  private detailAreaRef = React.createRef<HTMLDivElement>();

  constructor(props: Props) {
    super(props);
    // コンテンツを展開しているかの状態
    this.state = {
      isExpanded: false,
    };

    this.setContentMaxHeight = this.setContentMaxHeight.bind(this);
    this.handleResize = this.handleResize.bind(this);
    this.handleToggleClick = this.handleToggleClick.bind(this);
  }

  componentDidMount() {
    // 折りたたんでいる要素が一瞬表示されるのを防ぐため最大高を0pxにする
    this.setContentMaxHeight(0);

    // resizeイベントをバインド
    window.addEventListener("resize", this.handleResize);
  }

  componentWillUnmount() {
    // resizeイベントをアンバインド
    window.removeEventListener("resize", this.handleResize);
  }

  /**
   * resizeイベントをハンドルする
   */
  handleResize() {
    // 展開中なら最大高をセットする
    if (this.state.isExpanded) {
      this.setContentMaxHeight(this.detailAreaRef?.current?.scrollHeight ?? 0);
    }
  }

  /**
   * トグルボタンのクリックイベントをハンドルする
   */
  handleToggleClick() {
    if (this.state.isExpanded) {
      // 展開中なら最大高を0pxにする
      this.setContentMaxHeight(0);
    } else {
      // 折りたたみ中なら最大高をセットする
      this.setContentMaxHeight(this.detailAreaRef?.current?.scrollHeight ?? 0);
    }

    this.setState((prevState) => ({
      isExpanded: !prevState.isExpanded,
    }));
  }

  /**
   * コンテンツの最大の高さをセットする
   */
  setContentMaxHeight(height: number) {
    if (!this.detailAreaRef?.current) return;

    this.detailAreaRef.current.style.maxHeight = `${height}px`;
  }

  /**
   * トグルボタンを描画する
   */
  renderToggleButton() {
    // 展開中
    if (this.state.isExpanded) {
      return (
        <button
          type="button"
          className={`${styles.collapseToggleBtn} ${styles.hide}`}
          onClick={this.handleToggleClick}
        >
          {this.props.hideBtnLabel}
        </button>
      );
    }

    // 折りたたみ中
    return (
      <button
        type="button"
        className={`${styles.collapseToggleBtn} ${EXPAND_BUTTON_CLS}`}
        onClick={this.handleToggleClick}
      >
        {this.props.showBtnLabel}
      </button>
    );
  }

  render() {
    const toggleButton = this.renderToggleButton();

    const cls = clsx(
      styles.collapse,
      this.state.isExpanded && styles.isReadMore,
    );

    return (
      <div className={this.props.className}>
        <div className={cls} ref={this.detailAreaRef}>
          {this.props.children}
        </div>
        {toggleButton}
      </div>
    );
  }
}
