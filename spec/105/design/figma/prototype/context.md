# Figma Make context: 推薦理由UIアイデア提案 (プロトタイプ)

- File key: `m7i7WoQwpbZEoab3g5PTFf`
- Node ID: `0:1` (root; Figma Make のプロトタイプは常に `0:1` をルートとして扱う)
- 取得元URL: https://www.figma.com/make/m7i7WoQwpbZEoab3g5PTFf/%E6%8E%A8%E8%96%A6%E7%90%86%E7%94%B1UI%E3%82%A2%E3%82%A4%E3%83%87%E3%82%A2%E6%8F%90%E6%A1%88--%E5%B2%A9%E7%94%B0-
- 用途: プロトタイプ / デザイン参照 (推薦理由UIの複数バリエーション検討用)
- 取得ツール: `mcp_figma_mcp_ser_get_design_context`

`mcp_figma_mcp_ser_get_design_context` が返した内容は以下の 2 種類で構成される。

1. プロトタイプのコードリソース (App.tsx を起点とする TypeScript / React プロジェクト一式)。
2. プロトタイプに含まれる画像アセット。

コード本体は `source/` 配下に相対パスを保って保存する。画像アセットは (Figma Make のガイドどおり `figma/download_assets` を使わず) `context.md` からリンク参照するに留める。

## コードリソース (mcp-resource:// URI) 一覧

以下は `get_design_context` が返した全リソースURIである。`source/` 配下の対応する相対パスへ本体を保存する (詳細は `source/` を参照)。

- src/app/App.tsx
- package.json
- ATTRIBUTIONS.md
- default_shadcn_theme.css
- guidelines/Guidelines.md
- pnpm-workspace.yaml
- postcss.config.mjs
- src/app/components/figma/ImageWithFallback.tsx
- src/app/components/RecommendAccordion.tsx
- src/app/components/RecommendBottomSheet.tsx
- src/app/components/RecommendBubble.tsx
- src/app/components/RecommendCard.tsx
- src/app/components/RecommendFAB.tsx
- src/app/components/RecommendFloatBanner.tsx
- src/app/components/RecommendMerged.tsx
- src/app/components/ui/*.tsx (shadcn/ui ベース)
- src/imports/04ここに注目モーダル表示開いている状態/*
- src/imports/05ここに注目モーダル表示閉じている状態/*
- src/imports/11求人詳細チャットモーダル/*
- src/imports/Aica.tsx
- src/imports/FooterButtons.tsx
- src/imports/svg-*.tsx / svg-*.ts
- src/imports/モーダル/モーダル.tsx
- src/imports/探すポジション詳細.tsx / 探すポジション詳細2.tsx
- src/imports/推薦理由open/推薦理由open.tsx
- src/styles/fonts.css
- src/styles/index.css
- src/styles/tailwind.css
- src/styles/theme.css
- vite.config.ts

## 主要な推薦理由 UI コンポーネント

Figma Make のプロトタイプは、ポジション詳細チャット上での推薦理由の表示方法を複数バリエーションで比較検討している。App.tsx がバリエーション切り替えの UI シェルであり、以下が候補コンポーネントとして並んでいる。

- **RecommendCard** — 求人カード内 (または直下) に推薦理由をカードとして常時表示。
- **RecommendAccordion** — アコーディオン形式で開閉できる推薦理由。
- **RecommendBottomSheet** — 画面下部のボトムシートに推薦理由を表示 (SP 想定)。
- **RecommendBubble** — チャット内の吹き出しとして推薦理由を挿入。
- **RecommendFAB** — フローティングアクションボタンから推薦理由モーダルを開く。
- **RecommendFloatBanner** — 画面上部/下部のフロートバナーで推薦理由を告知。
- **RecommendMerged** — 上記のうち複数を組み合わせた案。

Figma design の SP/PC 5 画面 (`01.あなただけの注目ポイントを準備中` → `02.ここに注目！（キラキラ表示）` → `03.ここに注目` → `04.ここに注目_モーダル表示(開いている状態)` → `05.ここに注目_モーダル表示(閉じている状態)`) と併せて、実装時のUI案の参照資料として利用する。

## 画像アセット (Figma Make が返した参照画像)

`get_design_context` の応答には、プロトタイプに使われている数十枚の画像アセット (会社/ユーザー画像、AICA キャラクター画像、UI サムネイル等) が含まれていた。これらは `figma/download_assets` を使わない方針に従い、本ファイルからはリンク参照にとどめる (必要になった段階で個別に `read_file` で取得する)。
