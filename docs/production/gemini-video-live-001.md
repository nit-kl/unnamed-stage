# LIVE #001 Gemini動画制作ガイド（候補）

> **位置づけ:** 候補方針。Blender本制作を置き換える確定決定ではない。  
> Gemini（Veo系）の短尺生成を前提に、LIVE #001を分割クリップで作り、編集で一本化する手順書。

関連正本:

- [LIVE #001](../episodes/live-001.md)
- [AI_CONTEXT](../AI_CONTEXT.md)
- [白凪うた](../characters/uta-shiranagi.md)
- [AI・MCP運用](ai-tools.md)

## 1. 方針の要約

| 項目 | 内容 |
|---|---|
| 生成ツール | Geminiアプリ / Google AI Studio / Flow などの Veo 動画生成（候補） |
| 1クリップ尺 | 約4〜8秒（UI上は「10秒前後」と見なす）。長尺は分割＋編集 |
| 基本方式 | **画像→動画（Image-to-Video）** を主、テキストのみは補助 |
| 連続性の鍵 | 同一キャラ参照画像＋シーン別キーフレームを固定して渡す |
| 音声 | 歌・台詞は別制作。生成動画の自動音声は原則オフ／差し替え前提 |
| 本編の完成 | クリップ連結 → 音同期 → フラッシュ挿入 → UIテキスト → 書き出し |

Gemini単体で「完成した3分動画」を一度に作らない。  
**キー画像を先に固め、8秒単位の芝居を並べ、編集ソフトで物語にする。**

## 2. 全体フロー

```text
A. キー画像を確定（キャラ・空間・小物）
→ B. シーンを8秒クリップに割る
→ C. 各クリップ用の「開始画像＋プロンプト」を用意
→ D. Geminiで動画生成（同シーンは複数テイク）
→ E. 採用クリップを編集で連結
→ F. 楽曲・台詞・SE・字幕・WORLD表示を載せる
→ G. 権利・連続性・完成条件チェック
```

推奨の編集ソフト（候補）: DaVinci Resolve / Premiere / CapCut など。  
0.1秒フラッシュと `WORLD 0.01%` は、生成AI任せにせず編集で正確に入れる。

## 3. 渡すべき画像素材

動画生成の前に、次を「ロック済み参照」として用意する。  
ファイル名は例。実際の置き場は `references/` または制作用作業フォルダ（Git LFS方針確定後）。

### 3.1 必須セット（キャラ連続性）

| ID | 素材 | 用途 | 仕様メモ |
|---|---|---|---|
| `U-01` | 正面キーアート | ほぼ全クリップの主参照 | 淡灰髪・毛先淡青・左青/右灰の瞳・未完成白衣装 |
| `U-02` | 3/4キーアート | 歩行・振り返り | `U-01` と同デザイン固定 |
| `U-03` | クローズアップ顔 | 目覚め・台詞・「懐かしい」 | 表情はニュートラル〜困惑 |
| `U-04` | 歌唱ポーズ | ライブ各クリップ | 堂々とした姿勢。豪華照明なし |
| `U-05` | 表情差分シート | 生成前の指示用 | 不安 / 驚き / 歌唱笑顔 / 困惑 |

### 3.2 空間・小物

| ID | 素材 | 用途 |
|---|---|---|
| `W-01` | White World空景 | 背景のみ。床の水平線が弱い無限白空間 |
| `W-02` | マイク＋スタンド単体 | 遠景〜中景の配置合わせ |
| `W-03` | うた＋マイク（接触直前） | フラッシュ直前クリップの開始／終了フレーム |
| `F-01` | 青い花クローズアップ | 花出現・接触クリップ |
| `F-02` | 足元に花が一輪あるワイド | クライマックス確定画 |
| `X-01` | 満員ライブ会場静止画 | **編集で0.1秒挿入**用。動画生成に頼らない |

### 3.3 クリップごとの開始フレーム（推奨）

Veo系は「開始画像を動かして動画にする」のが安定しやすい。  
各クリップ `Cxx` ごとに、開始静止画 `Cxx_start.png` を用意する。

作り方（候補）:

1. 画像生成または手描き／3Dレンダーでキーポーズを作る
2. 直前クリップの最終フレームを切り出して次の開始画像にする（つなぎ重視）
3. 必要なら「開始フレーム＋終了フレーム」指定があるUIを使う

### 3.4 画像プロンプト共通制約（参照生成用）

キー画像をGemini画像生成や他ツールで作るときの共通文（候補）:

```text
Anime style original character, teenage idol about 16, height impression 157cm.
Near-white pale gray medium hair, very faint light-blue tips.
Heterochromia: left eye pale blue, right eye light gray (subtle).
Unfinished white sleeveless idol dress, minimal decoration, soft sheer accents, tiny pale blue details.
Empty infinite white void stage floor, soft diffused lighting, quiet atmosphere.
No audience, no fancy stage lights, no logos, no existing franchise lookalike.
```

禁止（プロンプトにも入れない）:

- 既存アニメ／アイドル／楽曲名の模倣指定
- 豪華な完成衣装、ドーム会場、大量観客（フラッシュ静止画 `X-01` 以外）
- 真相説明テキスト（「記憶の復元」などを画面に出す指示）

## 4. クリップ分割表

仮の本編尺を **約2分30秒〜3分**（歌パート仮90秒）と置く。  
歌の確定尺に合わせて `C10` 以降を増減する。

表記: `尺` は目標。生成は4/6/8秒で取り、編集でトリムする。

| ID | 秒目安 | シーン | 画面の仕事 | 開始画像 | 音声 |
|---|---|---|---|---|---|
| C01 | 0:00–0:08 | 目覚め | 白空間。うたが横たわる／まぶたを開ける | `W-01`＋うた臥位 | 無音〜環境ほぼゼロ |
| C02 | 0:08–0:16 | 目覚め | 起き上がり、周囲を見回す | C01最終フレーム | 台詞前半の余白 |
| C03 | 0:16–0:24 | 目覚め | バストアップ。「ここ、どこ？」「私……。」 | `U-03` 困惑寄り | 台詞 |
| C04 | 0:24–0:32 | 目覚め | 「白凪、うた。」名前を確かめる | `U-03` | 台詞 |
| C05 | 0:32–0:40 | マイク発見 | ワイド。遠くにマイク一本。うたが立つ | `W-02` 遠景 | 無音寄り |
| C06 | 0:40–0:48 | 接近 | マイクへ歩く（ゆっくり） | C05最終 | 足音は控えめor無 |
| C07 | 0:48–0:56 | 接触直前 | 手を伸ばす。緊張 | `W-03` | 無音 |
| C08 | 0:56–1:00 | フラッシュ | **編集専用:** `X-01` を約0.1秒挿入 | （生成しない） | ノイズ一瞬（任意） |
| C09 | 1:00–1:08 | 接触後 | 白空間に戻る。驚きの表情 | `W-03` 驚き版 | 息を飲む程度 |
| C10 | 1:08–1:16 | ライブ導入 | マイク前。表情が切り替わり始める | `U-04` | 曲イントロ開始 |
| C11〜 | 各8秒 | ライブ本編 | 歌唱・最小限の動き・カメラ変化 | `U-04`系を連続 | 「ここから、まだ」 |
| C20 | 曲終了直後 | 余韻 | 「……届いた？」 | 歌唱後バストアップ | 台詞 |
| C21 | +8秒 | 花出現 | 足元に青い花が一輪 | `F-02` へ向かう開始画 | 無音〜微SE |
| C22 | +8秒 | 接触 | 花に触れる。「懐かしい。」 | `F-01` | 台詞 |
| C23 | +8秒 | 自己への驚き | 「今、私……なんて言った？」 | `U-03` 強い困惑 | 台詞 |
| C24 | +6〜8秒 | 終了 | 暗転 → `WORLD 0.01%`（テキストは編集） | 暗転用黒orフェード | 無音 |

### 歌パート（C11〜）の割り方

歌詞・尺が未確定のため、次のテンプレで分割する。

| ブロック | 内容 | クリップ数の目安 |
|---|---|---|
| イントロ | 立ち姿、息を吸う、最初のフレーズ | 1〜2 |
| Aメロ | 控えめなカメラ、表情中心 | 2〜3 |
| Bメロ／サビ | 少し大きなジェスチャー、顔アップと全身を交互 | 3〜5 |
| アウトロ | 最後の音が消えるまで静止に近い演技 | 1 |

同一ポーズの連番は、**前クリップ最終フレームを次の開始画像**にしてドリフトを抑える。

## 5. プロンプトの書き方

### 5.1 基本型

各クリップは次の型で書く（英語推奨。日本語UIなら日本語でも可）。

```text
[Style] + [Subject lock] + [Action in this 8s] + [Camera] + [Environment] + [Constraints]
```

共通の Subject lock（毎回ほぼ同じ文を付ける）:

```text
Same girl as the reference image: Uta, pale gray medium hair with faint blue tips,
subtle heterochromia (left pale blue, right light gray), unfinished white idol dress.
Maintain exact face, hair length, and costume from the reference. Anime look.
```

### 5.2 やること／やらないこと

やること:

- **この8秒で起きる動作を1つ**に絞る（歩く、触る、歌う、驚く、など）
- カメラを1種類に固定（slow push-in / static / gentle orbit のいずれか）
- 「白い無限空間」「観客なし」「豪華照明なし」を毎回明示
- 表情の変化を動詞で書く（eyes widen, hesitant smile）

やらないこと:

- 1プロンプトにシーン全体の物語を詰め込む
- 長い台詞全文をリップシンクさせようとする（口形は編集／別工程）
- フラッシュ満員会場を「0.1秒で出せ」と動画生成に頼る
- 真相（記憶復元など）をナレーションさせる

### 5.3 音声まわり

候補運用:

1. 動画生成時は **無音／環境音のみ** を指示する
2. 歌・台詞は Suno 等＋収録／TTS で別トラック
3. 編集で口の動きにラフ同期（完璧なリップシンクは後工程でも可）

無音指示の例:

```text
No dialogue audio, no music, near-silent atmosphere.
```

## 6. クリップ別プロンプト例（コピー用）

以下は候補。参照画像を添付したうえで使う。

### C01 目覚め（開始）

添付: `U-01` または臥位開始画、`W-01`

```text
Anime style. Same girl as reference: pale gray medium hair with faint blue tips,
subtle heterochromia, unfinished white sleeveless idol dress.
She lies on an infinite seamless white floor in a white void, soft diffused light.
Over 8 seconds: she slowly opens her eyes, breathes once, barely moves.
Camera: static wide shot, lots of empty negative space, quiet and still.
No audience, no props except white space, no text, no music, near silence.
```

### C03 名前の困惑（バストアップ）

添付: `U-03`

```text
Anime close-up, same girl as reference. Soft white void background.
She looks confused and gentle, eyes shifting slightly as if searching her memory.
Subtle mouth movement as if whispering; keep expression readable and soft.
Camera: slow push-in from medium close-up to close-up.
No flashy lights, no crowd, no text overlays, near silence.
```

### C06 マイクへ歩く

添付: ワイド開始画（遠くにマイク）

```text
Anime wide shot, same girl as reference walking slowly across infinite white floor
toward a single microphone on a stand in the distance.
Quiet, hesitant footsteps, arms slightly tense, curious but uneasy.
Camera: gentle tracking from side-front, keep mic visible ahead.
Minimal soft shadow only. No audience, no stage truss, no colorful lights, near silence.
```

### C07 手を伸ばす

添付: `W-03`

```text
Anime medium shot, same girl as reference. She stands before a lone microphone stand
in a white void and slowly reaches her right hand toward the mic.
Tension in fingers, breath held, eyes focused on the mic.
Camera: static, slight shallow depth feel, calm framing.
No crowd flash, no glitch yet, no text, near silence.
```

### C08 について

動画生成しない。編集タイムラインで:

1. C07 の末尾
2. `X-01` を **2〜3フレーム（約0.08〜0.12秒 @24fps）**
3. C09 へカット戻し

`X-01` 用静止画プロンプト（候補）:

```text
Brief memory fragment still: packed indoor idol live venue, dense audience glow sticks,
stage spotlight haze, anime still frame look. Not a finished polished PV;
slightly overexposed, dreamlike. No readable logos, no real celebrity faces.
```

### C09 フラッシュ後

```text
Anime medium shot, same girl as reference beside the microphone in white void.
She flinches as if something flashed, eyes wide, hand pulled back a little.
After the startle, she looks at her hand and the mic, confused.
Camera: subtle handheld micro-shake then settle to static.
White empty world again. No crowd remains. Near silence.
```

### C11 歌唱開始（ギャップ）

添付: `U-04`

```text
Anime performance shot, same girl as reference at the microphone in white void.
Her posture changes from hesitant to confident idol presence as she begins to sing.
Minimal soft key light only; no concert rig, no audience, no particles yet.
Camera: slow orbit from front-left to front, elegant and simple.
Mouth moves with singing rhythm but keep face consistent with reference.
No text, no logos.
```

歌唱クリップ共通の追加文（毎回末尾に付ける）:

```text
Keep costume unfinished white, hair pale gray with faint blue tips,
heterochromia unchanged. White void only. Calm cinematic anime motion.
```

### C21 青い花の出現

添付: 足元ワイド開始画（花なし）→ 終了で花あり、が理想

```text
Anime wide shot, same girl as reference standing still in infinite white void
after singing. Silence. At her feet, a single small blue flower gently appears
and blooms, the only color accent in the white world.
Camera: slow tilt down from her face to the flower, then hold.
No garden, no field of flowers, just one bloom. Near silence. No text.
```

### C22 「懐かしい」

添付: `F-01` または手と花の開始画

```text
Anime close shot, same girl's hand gently touches one small blue flower on white floor.
Her expression softens into unconscious nostalgia, then a faint surprise at her own feeling.
Camera: static close-up, delicate motion only.
Keep flower small and simple, pale-to-vivid blue, not oversized. Near silence.
```

### C24 暗転（映像のみ）

```text
Anime shot of the girl and the single blue flower in white void fades to black
over 6 seconds. Soft, quiet fade. No new objects. No text in frame.
```

`WORLD 0.01%` と次回の問いは **編集のテキストレイヤ** で入れる（生成文字は崩れるため）。

## 7. 生成時の操作チェックリスト

各クリップで:

1. 参照画像（キャラ）を添付したか
2. 開始フレーム画像を添付したか
3. 動作は1つか
4. White World制約を書いたか
5. 無音／音楽なしを書いたか
6. テイクを2〜4本出し、表情・手足・髪の破綻が少ないものを選んだか
7. 採用ファイル名を `live001_C07_t03.mp4` のように残したか

採用時に記録するメタデータ（[ai-tools.md](ai-tools.md) 準拠）:

- 作成日
- ツール／モデル名（例: Veo 3.1）
- プロンプト全文
- 入力画像パス
- 採用／不採用理由
- 対応クリップID

## 8. 編集での組み立て

### 8.1 タイムライン順

```text
C01–C07 →（X-01 を0.1秒）→ C09 → C10–歌クリップ → C20–C23 → 暗転 → WORLD 0.01% → 次回の問い
```

### 8.2 つなぎのコツ

- カットつなぎが基本。無理なモーフィングはキャラ崩壊しやすい
- 白フラッシュや短いディゾルブは、視線誘導があるときだけ
- 歌パートはビートに合わせてクリップを切ると「ライブ感」が出る
- 普段パートはカットを少なめ、間を残す（余白と静寂）

### 8.3 必須の人手作業

| 要素 | 理由 |
|---|---|
| 0.1秒ライブ会場 | 生成AIは長さ制御が粗い |
| 台詞タイミング | 口形と音の一致 |
| 歌詞字幕 | 任意。読みやすさ優先 |
| `WORLD 0.01%` | タイポの安定 |
| 次回投票の問い | 文言は制作側が確定 |

## 9. 品質ゲート（LIVE #001）

生成・編集後に [完成条件](../episodes/live-001.md#完成条件) を確認する。

追加のGemini特有チェック:

- [ ] クリップ間で髪色・瞳左右・衣装が破綻していない
- [ ] 白背景で輪郭が消えていない
- [ ] 歌唱時だけ堂々としている
- [ ] 青い花が一輪だけのクライマックスになっている
- [ ] 満員会場が長すぎない（見落としうる短さ）
- [ ] 真相を説明しすぎる字幕やナレが入っていない
- [ ] 既存作品に見える固有デザインが混入していない

## 10. 素材フォルダ案（候補）

Gitへ全部は入れない。採用キー画像とプロンプト記録を優先する。

```text
production/live-001-gemini/          … 作業ルート（Git外またはLFS検討）
  references/
    U-01_uta_front.png
    U-02_uta_threequarter.png
    U-03_uta_face.png
    U-04_uta_sing.png
    W-01_whiteworld.png
    W-02_mic.png
    W-03_touch.png
    F-01_flower_cu.png
    F-02_flower_wide.png
    X-01_venue_flash.png
  starts/                            … 各クリップ開始フレーム
    C01_start.png
    ...
  clips/
    live001_C01_t02.mp4
    ...
  prompts/
    C01.txt …（または本ドキュメントを正本）
  edit/
    live001_timeline.md              … 採用テイク対応表
  exports/
    （書き出しはGit外）
```

## 11. 未確定・次に決めること

- 使用する具体UI（Geminiアプリ / AI Studio / Flow など）
- 本編アスペクト比（16:9本編、Shorts用9:16の切り出し有無）
- 楽曲の確定尺と、歌クリップの最終分割数
- キー画像を画像生成で作るか、3Dレンダーで作るか
- リップシンクをどの精度まで初回公開で求めるか
- 商用利用・YouTube公開条件（利用規約の都度確認）

## 12. 最短の始め方（今日やること）

1. `U-01` `U-03` `U-04` `W-01` `W-02` `F-01` の6枚を先に作ってロックする  
2. C01 → C03 → C07 → C21 の4本だけ試験生成する  
3. キャラ一致と白空間の出方を見てから、残りクリップを量産する  
4. 編集で仮組みし、歌は無音のまま尺感だけ確認する  
```
