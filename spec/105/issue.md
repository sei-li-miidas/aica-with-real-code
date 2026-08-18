# Issue #105: ユーザーがポジション詳細チャットを開いたら、推薦理由文が表示されるように機能追加

- Tracker/Project: 機能追加・改善 / ワークフロー検証
- 取得日時: 2026-08-18T02:17:18Z

## 説明(Issue description 原文)

## 要件
サイエンスチームは引き続きルーブリックの研究を継続されていますが、我々の方で単純に推薦理由が効果があるかどうか軽く検証したいと思います。

現状セッション数が少なくABテストするほどの母数がないためABテストはせず、一律推薦理由を生成して表示する。


推薦理由表示方法：
ポジション詳細エージェントを開いた際に生成する。

推薦理由の生成方法：
求人側のデータと求職者側のデータをLLMに渡して魅力的に要約してもらう。

求人側のデータ：

* ポジション情報の
  * 年収
  * 残業時間
  * 労働環境の特徴

* 企業情報の
  * アピールポイント
  * 実績のある福利厚生
  * 福利厚生（休日休暇）

求職者側のデータ：
転職軸の診断をしている場合はその転職軸。
転職軸の診断をしていない場合、一般的な転職理由。

## Figma

### デザイン

 - [SPデザイン](https://www.figma.com/design/ii4SCd0DSWJFFMiMH62DHu/AICA?node-id=682-29044&t=ivFXflawOdNQ2PcY-4) 
 - [PCデザイン](https://www.figma.com/design/ii4SCd0DSWJFFMiMH62DHu/AICA?node-id=682-29045&t=ivFXflawOdNQ2PcY-4) 
 - [プロトタイプ](https://www.figma.com/make/m7i7WoQwpbZEoab3g5PTFf/%E6%8E%A8%E8%96%A6%E7%90%86%E7%94%B1UI%E3%82%A2%E3%82%A4%E3%83%87%E3%82%A2%E6%8F%90%E6%A1%88--%E5%B2%A9%E7%94%B0-?p=f&t=z1LGlM4B2HrXRVig-0&fullscreen=1) 

## デザイン資料

- [SPデザイン](design/figma/sp-design/context.md)
- [PCデザイン](design/figma/pc-design/context.md)
- [プロトタイプ](design/figma/prototype/context.md)
