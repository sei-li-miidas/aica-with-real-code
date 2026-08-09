import React from "react";
import { type ClassComponentProps } from "@/types/utility-types";

import { EXPAND_BUTTON_CLS } from "@/constants/app";
import { clsx } from "@/utils/className";

import { debounce } from "@/utils";
import styles from "./CollapsibleJobTypeItem.module.scss";

type DefaultProps = {
  skillGroupNameRef: null;
  dummyGroupNameRef: null;
  skillItemsRef: null;
};

type Props = ClassComponentProps<
  DefaultProps,
  {
    children: React.ReactNode;
    isNameEmpty: boolean;
    isExpanded: boolean;
    setIsExpanded: (isExpanded: boolean) => void;
    skillGroupNameRef?: React.RefObject<HTMLDivElement | null>;
    dummyGroupNameRef?: React.RefObject<HTMLDivElement | null>;
    skillItemsRef?: React.RefObject<HTMLDivElement | null>;
    skillGroupSize: number;
  }
>;

type State = {
  /** スキルリストの一覧が省略されて表示されるかどうか */
  isTruncated: boolean;
};

/**
 * スキルグループを展開/折りたたむトグルボタンを表示する
 */
export default class CollapsibleJobTypeItem extends React.Component<
  Props,
  State
> {
  static defaultProps: DefaultProps = {
    skillGroupNameRef: null,
    dummyGroupNameRef: null,
    skillItemsRef: null,
  };

  private wrapperRef: React.RefObject<HTMLDivElement | null>;

  private contentAreaRef: React.RefObject<HTMLDivElement | null>;

  private initialContentHeight: number;

  private handleWindowResizeDebounce: () => void;

  private cancelHandleWindowResizeDebounce: () => void;

  constructor(props: Props) {
    super(props);

    this.state = {
      isTruncated: false,
    };

    this.wrapperRef = React.createRef();
    this.contentAreaRef = React.createRef();
    this.initialContentHeight = 0;

    this.setContentMaxHeight = this.setContentMaxHeight.bind(this);
    this.handleToggleClick = this.handleToggleClick.bind(this);
    this.handleWindowResize = this.handleWindowResize.bind(this);
    [this.handleWindowResizeDebounce, this.cancelHandleWindowResizeDebounce] =
      debounce(this.handleWindowResize, 200);
  }

  componentDidMount() {
    if (this.props.skillGroupNameRef?.current) {
      const skillGroupNameStyle = getComputedStyle(
        this.props.skillGroupNameRef.current,
      );
      const skillGroupNameHeight = parseFloat(skillGroupNameStyle.height);
      const skillGroupNameMarginBottom = parseFloat(
        skillGroupNameStyle.marginBottom,
      );
      this.initialContentHeight +=
        skillGroupNameHeight + skillGroupNameMarginBottom;
    }

    // 最初の偽階層グループ名が空の場合
    if (this.props.isNameEmpty) {
      if (this.props.skillItemsRef?.current) {
        // スキルリスト1行分の高さをセット
        const skillItemsStyle = getComputedStyle(
          this.props.skillItemsRef.current,
        );
        const skillItemsHeight = parseFloat(skillItemsStyle.lineHeight);
        const skillItemsMarginBottom = parseFloat(skillItemsStyle.marginBottom);
        this.initialContentHeight += skillItemsHeight + skillItemsMarginBottom;
      }
    } else if (this.props.dummyGroupNameRef?.current) {
      // 最初の偽階層グループ名の高さをセット
      const dummyGroupNameStyle = getComputedStyle(
        this.props.dummyGroupNameRef.current,
      );
      const dummyGroupNameHeight = parseFloat(dummyGroupNameStyle.height);
      const dummyGroupNameMarginBottom = parseFloat(
        dummyGroupNameStyle.marginBottom,
      );
      this.initialContentHeight +=
        dummyGroupNameHeight + dummyGroupNameMarginBottom;
    }

    // 最大高をセットする
    setTimeout(() => {
      // ReadMoreSectionの高さ取得処理とずらすために0.5秒の時間間隔を追加
      this.setContentMaxHeight(this.initialContentHeight);
    }, 500);

    if (this.props.skillItemsRef?.current) {
      // スキルリストが省略されているかどうかの判定
      if (
        this.props.skillItemsRef.current.scrollWidth >
        this.props.skillItemsRef.current.offsetWidth
      ) {
        this.setState({ isTruncated: true });
      }
    }

    // windowリサイズイベントハンドラーを登録
    window.addEventListener("resize", this.handleWindowResizeDebounce);
  }

  componentDidUpdate(prevProps: Props) {
    if (prevProps.isExpanded !== this.props.isExpanded) {
      if (this.props.isExpanded) {
        // 展開したら、最大高をセットする
        this.setContentMaxHeight(
          this.contentAreaRef?.current?.scrollHeight ?? 0,
        );
      } else {
        // 折りたたまれたら、最大高をコンテンツの高さの初期値にする
        this.setContentMaxHeight(this.initialContentHeight);

        // 続きを読む全体のTOPまでスクロールする
        // NOTE: contentAreaRefは省略表現のためにoverflow: hiddenが必要なので、scroll-margin-topが効かない。
        //       回避策として、セクション全体を囲ったwrapperRefにscroll-margin-topをあてて、fixed・sticky要素を考慮。
        this.wrapperRef?.current?.scrollIntoView({
          behavior: "smooth",
          block: "nearest",
        });
      }
    }
  }

  componentWillUnmount() {
    // removeEventListener後にdebounceされた処理が走る可能性があるためキャンセルする
    this.cancelHandleWindowResizeDebounce();
    // windowリサイズイベントハンドラーを解除
    window.removeEventListener("resize", this.handleWindowResizeDebounce);
  }

  /**
   * windowリサイズイベントを処理する
   */
  handleWindowResize() {
    // 展開中なら最大高をセットする
    if (this.props.isExpanded) {
      this.setContentMaxHeight(this.contentAreaRef?.current?.scrollHeight ?? 0);
    }
  }

  /**
   * トグルボタンのクリックイベントをハンドルする
   */
  handleToggleClick() {
    this.props.setIsExpanded(!this.props.isExpanded);
  }

  /**
   * コンテンツの最大の高さをセットする
   */
  setContentMaxHeight(height: number) {
    if (!this.contentAreaRef?.current) return;

    this.contentAreaRef.current.style.maxHeight = `${height}px`;
  }

  /**
   * トグルボタンを描画する
   */
  renderToggleButton() {
    // NOTE: トグルボタンの出し分け
    // 最初の偽階層グループ名が空の場合
    //   かつ、スキルグループが１つの場合
    //   かつ、スキルリストが１行の場合はトグルボタンを表示しない
    if (
      this.props.isNameEmpty &&
      this.props.skillGroupSize === 1 &&
      !this.state.isTruncated
    )
      return null;

    // 展開中
    if (this.props.isExpanded) {
      return (
        <button
          type="button"
          className={styles.collapseToggleBtn}
          onClick={this.handleToggleClick}
        >
          閉じる
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
        続きを読む
      </button>
    );
  }

  render() {
    const toggleButton = this.renderToggleButton();

    const cls = clsx(styles.collapse, this.props.isExpanded && styles.expanded);

    return (
      <div ref={this.wrapperRef} className={styles.wrapper}>
        <div className={cls} ref={this.contentAreaRef}>
          {this.props.children}
        </div>
        {toggleButton}
      </div>
    );
  }
}
