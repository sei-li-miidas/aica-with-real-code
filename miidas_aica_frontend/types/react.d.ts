/**
 * React関連の型をこのファイルにまとめる
 */

/* eslint-disable @typescript-eslint/consistent-type-definitions, @typescript-eslint/ban-types, @typescript-eslint/no-explicit-any */
declare module "react" {
  export = React;

  /**
   * {@link VoidFunctionComponent} から`propTypes`と`defaultProps`を無くしたもの
   */
  export interface MiidasFunctionComponent<P = {}>
    extends Omit<VoidFunctionComponent<P>, "propTypes" | "defaultProps"> {
    (props: P, context?: any): React.ReactElement<any, any> | null;
  }

  /**
   * {@link VFC} から`propTypes`と`defaultProps`を無くしたもの
   */
  export type MFC<P = {}> = MiidasFunctionComponent<P>;
}
/* eslint-enable @typescript-eslint/consistent-type-definitions, @typescript-eslint/ban-types, @typescript-eslint/no-explicit-any */
