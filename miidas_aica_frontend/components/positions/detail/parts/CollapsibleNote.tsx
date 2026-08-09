import React from "react";
import { type ClassComponentProps } from "@/types/utility-types";

import { debounce } from "@/utils/index";
import { clsx } from "@/utils/className";
import { EXPAND_BUTTON_CLS } from "@/constants/app";
import Text2LinkWrapper from "@/components/positions/detail/parts/Text2LinkWrapper";

import styles from "./CollapsibleNote.module.scss";

// 表示するテキストの最大行数
const MAX_NUMBER_OF_LINE = 2;
const DEFAULT_COLLAPSED_MAX_HEIGHT = 0;

type DefaultProps = {
  contentText: string;
  className: string;
};

type Props = ClassComponentProps<
  DefaultProps,
  {
    contentText?: string;
    className?: string;
  }
>;

type State = {
  shouldCollapse: boolean;
  isExpanded: boolean;
  collapsedMaxHeight: number;
};

/**
 * 長い場合に一部を折りたたんで表示する補足コンポーネント
 */
export default class CollapsibleNote extends React.Component<Props, State> {
  static defaultProps: DefaultProps = {
    contentText: "",
    className: "",
  };

  private wrapperRef: React.RefObject<HTMLDivElement | null>;

  private noteRef: React.RefObject<HTMLDivElement | null>;

  private handleResizeDebounce: () => void;

  private cancelHandleResizeDebounce: () => void;

  constructor(props: Props) {
    super(props);

    this.state = {
      shouldCollapse: false, // 折りたたんで表示すべきかどうか
      isExpanded: false, // コンテンツを展開しているかの状態
      collapsedMaxHeight: DEFAULT_COLLAPSED_MAX_HEIGHT, // 折りたたまれた時のmaxHeight（折りたたみ不要の場合はデフォルト値のまま）
    };

    this.handleResize = this.handleResize.bind(this);
    this.handleToggleClick = this.handleToggleClick.bind(this);
    [this.handleResizeDebounce, this.cancelHandleResizeDebounce] = debounce(
      this.handleResize,
      100,
    );

    this.wrapperRef = React.createRef();
    this.noteRef = React.createRef();
  }

  componentDidMount() {
    this.collapseIfNeeded();

    // resizeイベント
    window.addEventListener("resize", this.handleResizeDebounce);
  }

  componentDidUpdate(prevProps: Props, prevState: State) {
    if (prevState.shouldCollapse !== this.state.shouldCollapse) {
      this.setNoteMaxHeight();
    }

    // 閉じた場合
    if (prevState.isExpanded && !this.state.isExpanded) {
      // 続きを読む全体のTOPまでスクロールする
      // NOTE: noteRefは省略表現のためにoverflow: hiddenが必要なので、scroll-margin-topが効かない。
      //       回避策として、セクション全体を囲ったwrapperRefにscroll-margin-topをあてて、fixed・sticky要素を考慮。
      this.wrapperRef?.current?.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    }
  }

  componentWillUnmount() {
    // removeEventListener後にdebounceされた処理が走る可能性があるためキャンセルする
    this.cancelHandleResizeDebounce();
    // resizeイベントを削除
    window.removeEventListener("resize", this.handleResizeDebounce);
  }

  /**
   * resizeイベントをハンドルする
   */
  handleResize() {
    this.setNoteMaxHeight();
    this.collapseIfNeeded();
  }

  /**
   * トグルボタンのクリックイベントをハンドルする
   */
  handleToggleClick() {
    this.setState(
      (prevState) => ({
        isExpanded: !prevState.isExpanded,
      }),
      () => {
        this.setNoteMaxHeight();
      },
    );
  }

  /**
   * 補足のmaxHeightをセットする
   * NOTE: 開くアニメーションのために補足のmaxHeightを指定する。
   */
  setNoteMaxHeight() {
    const { noteRef } = this;
    if (!noteRef?.current) return;

    // 折りたたみ表示でない場合はクリアする
    if (!this.state.shouldCollapse) {
      noteRef.current.style.maxHeight = "";
      return;
    }

    let maxHeight = 0;
    if (this.state.isExpanded) {
      // 展開した場合、補足テキストの全高を指定する（開くアニメーションのためクリアはしない）
      maxHeight = noteRef.current.scrollHeight;
    } else {
      // 折りたたんだ場合
      maxHeight = this.state.collapsedMaxHeight;
    }

    noteRef.current.style.maxHeight = `${maxHeight}px`;
  }

  /**
   * 必要であれば折りたたみ表示にする
   */
  collapseIfNeeded() {
    const { noteRef } = this;
    if (!noteRef?.current) return;

    // 補足のHTML要素の高さが指定の最大行数を超える場合、折りたたみ表示にする
    const lineHeight = getComputedStyle(noteRef.current).lineHeight;
    const targetHeight = parseFloat(lineHeight) * MAX_NUMBER_OF_LINE;
    if (targetHeight < noteRef.current.scrollHeight - 1) {
      // scrollHeightはブラウザ依存で内部的に切り上げ/切り下げされた整数なので、最大1px分のマージンを考慮
      this.setState({
        shouldCollapse: true,
        collapsedMaxHeight: targetHeight,
      });
      // 最大行数を超えない場合、折りたたみ表示を解除する
    } else {
      this.setState({
        shouldCollapse: false,
        collapsedMaxHeight: DEFAULT_COLLAPSED_MAX_HEIGHT,
      });
    }
  }

  /**
   * トグルボタンを描画する
   */
  renderToggleButton() {
    // 折りたたみ不要の場合、描画しない
    if (!this.state.shouldCollapse) return null;

    // 展開中
    if (this.state.isExpanded) {
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
        className={clsx(styles.collapseToggleBtn, EXPAND_BUTTON_CLS)}
        onClick={this.handleToggleClick}
      >
        続きを読む
      </button>
    );
  }

  render() {
    const toggleButton = this.renderToggleButton();

    const noteCls = clsx(
      styles.note,
      this.state.isExpanded ? styles.expanded : styles.collapsed,
    );

    return (
      <div
        ref={this.wrapperRef}
        className={clsx(styles.wrapper, this.props.className)}
      >
        <div ref={this.noteRef} className={noteCls}>
          <Text2LinkWrapper text={this.props.contentText} />
        </div>
        {toggleButton}
      </div>
    );
  }
}
