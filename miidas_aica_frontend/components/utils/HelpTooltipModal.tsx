import React, { type MouseEvent } from "react";

import SvgIcon from "@/components/utils/SvgIcon";
import * as ICON from "@/constants/icon";
import { type ClassComponentProps } from "@/types/utility-types";
import styles from "./HelpTooltip.module.scss";

type DefaultProps = {
  className: string;
  dateKey: string;
};

type Props = ClassComponentProps<
  DefaultProps,
  {
    className?: string;
    dataKey?: string;
    showModal: (key: string | MouseEvent<HTMLButtonElement>) => void;
  }
>;

/**
 * ヘルプツールチップコンポーネント
 * ツールチップをクリックした際にモーダルを表示する用途
 */
export default class HelpTooltipModal extends React.Component<Props> {
  static defaultProps: DefaultProps = {
    className: "",
    dateKey: "",
  };

  constructor(props: Props) {
    super(props);

    this.handleHelpBtnTouch = this.handleHelpBtnTouch.bind(this);
  }

  /**
   * ヘルプボタンのタッチイベントをハンドルする
   */
  handleHelpBtnTouch(e: MouseEvent<HTMLButtonElement>) {
    e.preventDefault();
    e.stopPropagation();
    if (e.currentTarget?.dataset?.key) {
      this.props.showModal(e.currentTarget.dataset.key);
    } else {
      this.props.showModal(e);
    }
  }

  render() {
    return (
      <button
        type="button"
        aria-label="Help"
        className={`${styles.helpTooltipBtn} ${this.props.className}`}
        data-key={this.props.dataKey}
        onClick={this.handleHelpBtnTouch}
      >
        <SvgIcon icon={ICON.COMMON.NOTICE_QUESTION} />
      </button>
    );
  }
}
