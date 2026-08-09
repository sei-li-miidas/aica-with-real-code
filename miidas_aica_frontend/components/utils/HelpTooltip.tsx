import React, { type ComponentPropsWithoutRef } from "react";

import SvgIcon from "@/components/utils/SvgIcon";
import * as ICON from "@/constants/icon";
import { isSmartphone } from "@/utils/device";
import HelpBalloon from "@/components/utils/HelpBalloon";
import { type ClassComponentProps } from "@/types/utility-types";

import styles from "./HelpTooltip.module.scss";

type DefaultProps = {
  className: string;
  position: ComponentPropsWithoutRef<typeof HelpBalloon>["position"];
  isOnModal: boolean;
};

type Props = ClassComponentProps<
  DefaultProps,
  {
    help: ComponentPropsWithoutRef<typeof HelpBalloon>["help"];
    className?: string;
    position?: ComponentPropsWithoutRef<typeof HelpBalloon>["position"];
    isOnModal?: boolean;
  }
>;

type State = {
  display: boolean;
};

/**
 * ヘルプツールチップコンポーネント
 */
export default class HelpTooltip extends React.Component<Props, State> {
  static defaultProps: DefaultProps = {
    className: "",
    position: "top",
    isOnModal: false,
  };

  constructor(props: Props) {
    super(props);

    this.state = {
      display: false,
    };

    this.handleDocumentTouch = this.handleDocumentTouch.bind(this);
    this.handleScroll = this.handleScroll.bind(this);
  }

  componentDidMount() {
    if (isSmartphone()) {
      // イベントをバインド
      // NOTE: touchstartをキャプチャリングにして、先にツールチップ非表示処理を実行する
      document.addEventListener("touchstart", this.handleDocumentTouch, true);
      document.addEventListener("scroll", this.handleScroll, true);
    }
  }

  componentWillUnmount() {
    if (isSmartphone()) {
      // イベントをアンバインド
      document.removeEventListener(
        "touchstart",
        this.handleDocumentTouch,
        true,
      );
      document.removeEventListener("scroll", this.handleScroll, true);
    }
  }

  /**
   * ヘルプボタンのタッチイベントをハンドルする
   */
  handleHelpBtnTouch() {
    // ツールチップを表示する
    this.setState({
      display: true,
    });
  }

  /**
   * ドキュメント全体のタッチイベントをハンドルする
   */
  handleDocumentTouch() {
    // ツールチップを非表示にする
    if (this.state.display) {
      this.setState({
        display: false,
      });
    }
  }

  /**
   * スクロールイベントをハンドルする
   */
  handleScroll() {
    // スクロールしたら非表示にする
    if (this.state.display) {
      this.setState({
        display: false,
      });
    }
  }

  /**
   * MouseEnterイベントをハンドルする
   */
  handleMouseEnter() {
    return this.setState({
      display: true,
    });
  }

  /**
   * MouseLeaveイベントをハンドルする
   */
  handleMouseLeave() {
    return this.setState({
      display: false,
    });
  }

  /**
   * ヘルプ表示バルーンを描画
   */
  renderBalloon() {
    return (
      <HelpBalloon
        display={this.state.display}
        help={this.props.help}
        position={this.props.position}
        isOnModal={this.props.isOnModal}
      />
    );
  }

  render() {
    // デバイスタイプに合わせてツールチップの表示方法を変える
    // SPの場合 ヘルプボタンタッチでツールチップを表示
    // PCの場合 ヘルプボタンホバーでツールチップを表示

    const balloon = this.renderBalloon();

    if (isSmartphone()) {
      return (
        <>
          <button
            type="button"
            aria-label="Help"
            className={`${styles.helpTooltipBtn} ${this.props.className}`}
            onTouchStart={this.handleHelpBtnTouch.bind(this)}
          >
            <SvgIcon icon={ICON.COMMON.NOTICE_QUESTION} />
          </button>
          {balloon}
        </>
      );
    }

    return (
      <>
        <button
          type="button"
          aria-label="Help"
          className={`${styles.helpTooltipBtn} ${this.props.className}`}
          onMouseEnter={this.handleMouseEnter.bind(this)}
          onMouseLeave={this.handleMouseLeave.bind(this)}
        >
          <SvgIcon icon={ICON.COMMON.NOTICE_QUESTION} />
        </button>
        {balloon}
      </>
    );
  }
}
