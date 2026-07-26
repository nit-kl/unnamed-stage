# まだ名前のないステージ

何もない世界で目覚めたアイドル・白凪うたが、歌によって失われた世界と
自分自身の記憶を取り戻していく、YouTube視聴者参加型ライブストーリー。

## 企画の現在地

現在はプリプロダクション段階です。最初の目標は `LIVE #001` の制作に必要な
設定、キャラクターデザイン、White World、楽曲、映像パイプラインを固めることです。

- 主人公: 白凪うた / Uta Shiranagi
- 仮タイトル: まだ名前のないステージ
- 第1曲（仮）: ここから、まだ
- 初期世界: 地面と一本のマイクしかない白い空間
- 中心テーマ: 誰かに覚えていてもらうこと
- 映像試作: [Godot 2Dプロトタイプ](godot/README.md)

## ドキュメント

- [AI向け共通コンテキスト](docs/AI_CONTEXT.md)
- [企画概要](docs/concept/overview.md)
- [世界設定](docs/concept/world.md)
- [長期ストーリー](docs/concept/story.md)
- [YouTubeフォーマット](docs/concept/youtube-format.md)
- [白凪うた](docs/characters/uta-shiranagi.md)
- [LIVE #001](docs/episodes/live-001.md)
- [制作パイプライン](docs/production/pipeline.md)
- [AI・MCP運用](docs/production/ai-tools.md)
- [制作ロードマップ](docs/production/roadmap.md)

## 基本方針

- キャラクター、楽曲、舞台、物語はオリジナルとして制作する。
- ライブ映像と連続ストーリーを分離せず、各動画を物語の1話として成立させる。
- 世界の復元状況を、背景だけでなく衣装、瞳、音、画面表示にも反映する。
- 映像はBlenderとLive2Dを使わず、Godotの標準2D機能を中心に制作する。
- AI生成物は完成品として無条件に採用せず、出典、権利、連続性を人が確認する。
- 大容量バイナリの管理方法は、実ファイルを追加する前にGit LFS等を決定する。

## 想定ディレクトリ

制作が進んだ段階で、以下を用途別に追加します。

```text
references/   キャラクター、衣装、舞台、撮影の参照資料
godot/        2Dリグ、舞台、アニメーション、エフェクト、シーン
audio/        楽曲、ボーカル、BGM、効果音
video/        エピソード、Shorts、レンダー
prompts/      画像、音楽、アニメーション、Codex用プロンプト
scripts/      Godotおよび制作自動化スクリプト
```
