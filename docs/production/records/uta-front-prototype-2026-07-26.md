# 白凪うた正面スプライト候補 — 2026-07-26

> **位置づけ:** Godot 2D映像パイプラインを検証するためのプロトタイプ用候補。
> キャラクターの確定原画、レイヤー分け原画、公開用素材ではない。

## 生成情報

| 項目 | 内容 |
|---|---|
| 作成日 | 2026-07-26 |
| 使用ツール | Codex組み込み imagegen |
| 使用モデル | 組み込みツールから個別のモデル識別子は公開されていない |
| 入力画像 | `references/uta-shiranagi/turnaround.png` |
| 生成元 | 入力ターンアラウンド左端の正面像 |
| 中間条件 | 単色 `#00ff00` 背景で生成 |
| 後処理 | Godotスクリプトでクロマキーをアルファへ変換し、半透明部をデスピル |
| 採用範囲 | ローカルの映像・リグ検証のみ |

プロジェクト内候補ファイル:
`godot/assets/character/uta_front_prototype_v4.png`

## 生成プロンプト

```text
Use case: background-extraction
Asset type: prototype full-body 2D character sprite for a Godot anime live scene
Input image: the supplied turnaround sheet is the edit target and authoritative design reference
Primary request: isolate and recreate only the leftmost front-view figure of Uta Shiranagi as one clean full-body sprite, preserving her face, pale gray shoulder-length hair with faint blue tips, subtle heterochromia (character-left eye pale blue, character-right eye light gray), white unfinished idol dress, proportions, boots, and neutral front-facing pose from the reference
Scene/backdrop: perfectly flat solid #00ff00 chroma-key background for removal
Composition: entire body including hair tuft and boots visible, centered, generous padding, no cropping
Style: polished original anime character art matching the reference
Constraints: one character only; exact front view; arms slightly away from torso; preserve the established costume and silhouette; background must be one uniform #00ff00 with no shadows, gradients, texture, floor plane, reflections, or lighting variation; no cast shadow; do not use #00ff00 in the character
Avoid: other turnaround views, guide lines, labels, title, measurements, logos, watermark, added props, microphone, audience, elaborate new costume details
```

## 連続性確認

- キャラクター左目（画面右）: 淡い青
- キャラクター右目（画面左）: 薄い灰色
- 髪: 白に近い淡灰色、毛先に淡い青
- 衣装: 白主体。プロトタイプでは参照画像の形状を継承
- 世界進行度: `LIVE #001`、`WORLD 0.01%`より前

## 公開前の扱い

生成画像は、権利、利用規約、デザインの独自性、設定連続性を改めて確認するまで
公開用映像へ採用しない。最終制作では、承認済み原画をレイヤー分けして置き換える。
