# Godot 2Dプロトタイプ

BlenderとLive2Dを使わず、Godot標準2D機能だけで `LIVE #001` の演出を検証する。

## 起動

Godot 4でリポジトリ直下の `project.godot` を開いて実行する。

コマンドライン例:

```powershell
godot --path . --editor
godot --path .
```

操作:

- `Space`: 一時停止／再開
- `R`: 冒頭へ戻る
- `Esc`: 終了

## 現在の範囲

- 導入・歌唱・余韻を含む86秒の演出プロトタイプ
- White World、マイク、短い記憶フラッシュ、歌唱中の光、青い花、終了表示
- 112 BPMに同期した重心移動、ステップ、ポーズ切り替え、カメラ、照明
- 歌詞候補「ここから、まだ」LIVE #001 edit v2の字幕タイムライン
- 正面・Aメロ・サビ・正面へ手を伸ばす4枚の全身ポーズ候補
- 完成リグ、口形、楽曲音源、台詞音声は未実装

各スプライトはパイプライン検証用の候補であり、公開用確定素材ではない。
レイヤー分け原画が完成したら、髪、顔、腕、衣装を個別ノードへ置き換える。

歌詞・BPM・尺も未採用の候補。正本候補は
[koko-kara-mada-v2](../prompts/music/koko-kara-mada-v2.md)を参照する。

## プレビュー画像

次のコマンドはサビ中のタイムライン44秒地点を `C:\tmp` に保存する。
描画バッファが必要なため、`--headless` は付けない。

```powershell
godot --path . --quit-after 10 -- --capture
```

## 映像書き出し

GodotのMovie Makerモードを使う場合:

```powershell
godot --path . --write-movie C:\tmp\live001-prototype-v2.ogv --fixed-fps 30 -- --movie
```

本編用の動画書き出しはGitへ追加しない。
