# 白凪うた歌唱ポーズ候補 — 2026-07-26

> **位置づけ:** Godot 2Dライブ演出を検証するためのプロトタイプ候補。  
> キャラクターの確定原画、レイヤー分け原画、公開用素材ではない。

## 生成情報

| 項目 | 内容 |
|---|---|
| 作成日 | 2026-07-26 |
| 使用ツール | Codex組み込み imagegen |
| 使用モデル | 組み込みツールから個別のモデル識別子は公開されていない |
| 入力画像 | `references/uta-shiranagi/turnaround.png` |
| 生成方式 | 入力ターンアラウンドを同一性の基準にしたポーズ差分生成 |
| 中間条件 | 単色 `#00ff00` 背景、マイクなどの小物なし |
| 後処理 | Godotスクリプトでクロマキーをアルファへ変換し、緑の回り込みを抑制 |
| 採用範囲 | ローカル映像・リグ検証のみ |

## 生成物

- `godot/assets/character/uta_pose_verse_v1.png`
- `godot/assets/character/uta_pose_chorus_v1.png`
- `godot/assets/character/uta_pose_reach_v1.png`

## 生成条件

### Verse / 胸に手を置くポーズ

```text
Use case: identity-preserving character pose variation
Asset type: full-body anime performance pose for a Godot 2D live scene
Input image: the supplied Uta Shiranagi turnaround is the authoritative identity and costume reference
Primary request: create one clean full-body pose of the same character singing the first verse with quiet confidence; character-right hand (viewer left) rests over her chest, character-left hand (viewer right) opens gently outward, one knee is slightly bent, mouth open in a natural singing shape
Scene/backdrop: perfectly flat solid #00ff00 chroma-key background for removal
Composition: entire body, hair tuft, hands, and boots visible; centered with generous padding; no cropping
Style: polished original anime character art matching the reference
Identity invariants: pale gray shoulder-length hair with faint blue tips; character-left eye (viewer right) pale blue; character-right eye (viewer left) light gray; unfinished white idol dress; same silhouette, proportions, boots, necklace, and costume structure
Constraints: one character only; no microphone or props; anatomically coherent hands; no extra fingers or limbs; no cast shadow; uniform green background
Avoid: audience, stage scenery, text, logo, watermark, elaborate costume additions, imitation of an existing anime or idol
```

### Chorus / 腕を大きく開くポーズ

```text
Use case: identity-preserving character pose variation
Asset type: full-body anime performance pose for a Godot 2D live scene
Input image: the supplied Uta Shiranagi turnaround is the authoritative identity and costume reference
Primary request: create one energetic chorus pose of the same character singing confidently; character-left arm (viewer right) reaches diagonally upward with an open hand, character-right arm (viewer left) opens outward near waist height, feet set in a wider stable stance, bright singing expression
Scene/backdrop: perfectly flat solid #00ff00 chroma-key background for removal
Composition: entire body, raised hand, hair tuft, and boots visible; centered with generous padding; no cropping
Style: polished original anime character art matching the reference
Identity invariants: pale gray shoulder-length hair with faint blue tips; character-left eye (viewer right) pale blue; character-right eye (viewer left) light gray; unfinished white idol dress; same silhouette, proportions, boots, necklace, and costume structure
Constraints: one character only; no microphone or props; anatomically coherent hands; no extra fingers or limbs; no cast shadow; uniform green background
Avoid: audience, stage scenery, text, logo, watermark, elaborate costume additions, imitation of an existing anime or idol
```

### Reach / 正面へ届けるポーズ

```text
Use case: identity-preserving character pose variation
Asset type: full-body anime performance pose for a Godot 2D live scene
Input image: the supplied Uta Shiranagi turnaround is the authoritative identity and costume reference
Primary request: create one emotional final-refrain pose of the same character; she leans slightly toward the viewer while singing, both arms reach forward and outward at chest height with open palms, expression earnest and hopeful
Scene/backdrop: perfectly flat solid #00ff00 chroma-key background for removal
Composition: entire body, both hands, hair tuft, and boots visible; centered with generous padding; no cropping
Style: polished original anime character art matching the reference
Identity invariants: pale gray shoulder-length hair with faint blue tips; character-left eye (viewer right) pale blue; character-right eye (viewer left) light gray; unfinished white idol dress; same silhouette, proportions, boots, necklace, and costume structure
Constraints: one character only; no microphone or props; anatomically coherent hands; no extra fingers or limbs; no cast shadow; uniform green background
Avoid: audience, stage scenery, text, logo, watermark, elaborate costume additions, imitation of an existing anime or idol
```

## 連続性への影響

- 髪色、左右の瞳色、白い未完成衣装、年齢感、世界の進行度は変更していない。
- 歌唱時に堂々とする既存設定を、胸に手を置く、腕を開く、正面へ手を伸ばす
  3種類の一時的な姿勢・表情として追加した。
- 衣装の細部は生成画像間で完全一致していない可能性がある。確定原画化する際は
  ターンアラウンドを正本として修正する。
- 世界に観客や舞台設備は追加していない。淡青の光はライブ中だけの映像演出候補。

## 権利・採用前確認

組み込み画像生成サービスの利用条件、出力物の権利、デザインの独自性、
手指と衣装の整合性を確認するまで公開用映像へ採用しない。
最終制作では、承認済み原画をレイヤー分けして置き換える。
