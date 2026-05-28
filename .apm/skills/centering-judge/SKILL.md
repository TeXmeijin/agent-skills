---
name: centering-judge
description: 画像（PNG）からUI要素の整列（縦中央揃い / 左端揃い / 間隔均等 等）を画素単位で静的判定するスクリプトを、命題ごとに新規実装してから走らせる skill。LLM の主観で「揃ってる」と誤判定するのを防ぐためのメタ手法。固定スクリプトを呼ぶのではなく、検証したい命題ごとに ROI / 判定式 / debug overlay を設計し直す。scripts/ にケース別の参考実装（中央揃い / 左端揃い）を同梱。トリガー：「中央寄せ判定」「縦揃え確認」「左端揃え判定」「centering check」「alignment check」「画像で揃ってるか確認して」
---

# Centering Judge

## このスキルの本質

LLMは画像の「微妙なズレ」を主観で判断しがちで、自分に都合よく「揃っている」と誤判定してしまう。 このskillの本質は **「画素単位で客観的に判定するスクリプトを毎回新規実装する」** というメタ手法。

汎用判定スクリプトは存在しない。整列の命題はレイアウトによって変わるため、 毎回以下を回す:

1. **命題を言語化**: 何と何の、何 (中心 y / 左端 x / 間隔 / etc) を比べるか
2. **ROI を設計**: 画像内のどの範囲を見るか、 自動検出か人手指定か
3. **判定アルゴリズムを選ぶ**: content profile / 連結成分 / 行ごと profile / etc
4. **実装する**: 共通道具箱 (後述) を組み合わせて短いスクリプトを書く
5. **数値で結論を出す**: 「ほぼ揃ってる」「微妙だが許容範囲」を禁じ、 px 単位で言い切る

## 絶対ルール

> 「✅ 揃ってる」と返答する前に、 必ず命題に応じた判定スクリプトを書いて実行する。 検出されたずれを曖昧表現で濁さず、 px 数値で言い切る。 LLM の目視判定のみで「揃った」と答えてはいけない。

## 標準フロー

### 1. 命題を言語化する

例:
- 「画像左の円形アイコンと、 その右に並ぶ要素群の縦中心 y が揃っているか」
- 「縦に並ぶ 3 行で、 各行のアイコン直後のテキスト左端 x が揃っているか」
- 「カード内のボタン群の縦中心 y が同一直線上か」
- 「サイドバー項目の縦間隔 (gap) が等間隔か」

「揃ってるか確認して」だけで実装に入らない。 何と何の何かを必ず明示してから着手する。

### 2. ROI と比較対象を設計する

- **自動検出 vs 人手指定**: 全自動は誤検出しやすい。 `--row label y_top y_bot` 形式で ROI を人手指定する方が堅実。 自動検出を入れるのは「同じレイアウトを大量に検証する」ときだけ
- **要素境界の閾値**: 隣接 content の gap が N px 未満なら同要素として統合 / N px 以上で別要素として分離。 N は引数化して命題ごとに調整
- **基準点の決め方**: 中央揃いなら「基準要素 1 つ vs その他」、 左端揃いなら「全行で同じ x が取れるか」、 間隔均等なら「連続要素間の gap」

### 3. 判定アルゴリズムを選ぶ

整列判定の共通パターン:

| 命題 | 主要アルゴリズム |
|---|---|
| 縦中央揃い (行内) | 各要素の bbox 中心 y を計測、 基準要素との差を比較 |
| 左端揃い (複数行) | 各行で content 最左 x を計測、 max - min を delta_max とする |
| 右端揃い (複数行) | 同上で最右 x |
| 間隔均等 (縦/横) | 連続要素の bbox 間 gap を計測、 max - min を delta_max とする |
| 中央寄せ (コンテナ内) | コンテナ bbox 中心と中身 bbox 中心の差を計測 |

### 4. 実装の共通道具箱

毎回ゼロから書くのではなく、 以下のパーツを再利用する。

#### 4.1 画像読み込み + 背景マスク

```python
from PIL import Image
import numpy as np

img = Image.open(image_path).convert("RGB")
arr = np.array(img)
is_content = arr.min(axis=2) < 230  # 白背景: RGB 最小値 < 230 を content とみなす
```

dark mode の画像なら閾値を逆転 (`arr.max(axis=2) > 30` 等)。

#### 4.2 content profile

- 各行の content 数: `is_content.sum(axis=1)` → 行に何かが描かれているか
- 各列の content 数: `is_content.sum(axis=0)` → 列に何かが描かれているか
- 必ず ROI に絞ってから profile を取る

#### 4.3 連続 run 抽出 + gap 統合

profile を bool 化 (> 閾値) してから、 連続する True 区間を抽出。 隣接 run の gap が `merge_gap_threshold` 未満なら統合する後処理を入れる。 この閾値が要素境界の感度を決める。

#### 4.4 debug overlay PNG

検出結果を**必ず**画像に重ねて保存する。 数値だけだと読者は信用しないので、 視覚的証拠を添える:

- 検出 bbox を色付き矩形で
- 基準線 (中心 y / 左端 x) を色付き直線で
- 判定 NG の要素は赤、 OK は青/緑等で色分け

```python
from PIL import ImageDraw

overlay = img.copy()
draw = ImageDraw.Draw(overlay)
draw.rectangle([l, t, r, b], outline=(255, 0, 0), width=2)
draw.line([(0, center_y), (w, center_y)], fill=(255, 0, 0), width=1)
overlay.save(debug_out)
```

#### 4.5 出力 + 終了コード

```python
print(json.dumps(result, indent=2, ensure_ascii=False))  # 再現性のため JSON も
print(f"\n=== VERDICT: {verdict} ===")
for d in details:
    print(d)
sys.exit(0 if verdict == "PASS" else 1 if verdict.startswith("SOME") else 2)
```

終了コード規約: `0` = ALL OK / `1` = SOME FAIL / `2` = ERROR (検出不能等)。

### 5. 実行と報告のルール

1. **delta は実換算する**: retina @2x なら `実換算 = delta / device_pixel_ratio`. 両方の数値を提示
2. **debug overlay を必ず生成**: ユーザーに視覚的裏付けを提示できるように
3. **threshold ぎりぎりに注目**: 「PASS (threshold内)」と出ても 2-3px ずれているなら「テクニカルには PASS だが N px ずれている」と報告
4. **「ほぼ揃ってる」と濁さない**: FAIL が出たら原因の CSS / SVG を特定して修正案まで出す
5. **検出失敗時はパラメータを調整**: `--vertical-margin`, `--cluster-merge-x-gap`, `--max-avatar-height` 等を変えてリトライ

## 参考実装 (scripts/)

`scripts/` 配下のスクリプトは **参考実装**。 そのまま呼んで「揃ってる/揃ってない」を返すための固定ツールではない。 「こういう命題にはこう書いた」例として読み、 別命題なら別スクリプトを書く。

### scripts/left_circle_vs_right_row_center_y.py — 中央揃い判定の例

**命題**: 「画像左の円形アイコンと、 その右に並ぶ要素群の縦中心 y が揃っているか」

**主要仮定**:
- 画像幅の左 8-20% に 1 つだけ円形要素 (aspect 0.7-1.4, circularity ≥ 1.2) がある
- その右側 20-95% に揃えるべき要素群が縦 1 行で並ぶ

**アルゴリズム**: avatar 自動検出 → 縦範囲を基準に右側を縦方向 profile で分割 → 各要素の bbox 中心 y を avatar 中心 y と比較 → `|delta| > threshold` で FAIL

**踏襲できる部分**:
- 背景マスク / content profile / 連続 run / `cluster_merge_x_gap` での要素分割 / debug overlay / 終了コード規約

**踏襲できない部分**:
- 「左に円形 + 右に要素群」前提のレイアウト依存。 他レイアウト (ボタン内アイコン+テキスト、 ヘッダーロゴ+ナビ等) では破綻する。 そのときは avatar 自動検出を捨てて ROI 人手指定方式に書き換える

### scripts/multi_row_text_left_x_after_icon.py — 左端揃い判定の例

**命題**: 「縦に並ぶ複数行 (各行が左にアイコン + 右にテキスト) で、 テキスト左端 x が揃っているか」

**主要仮定**:
- 行ごとの ROI (y_top, y_bot) を人手指定する
- 各行が「アイコン + 1 つ以上のテキスト塊」の 2 ブロック以上を含む
- 1 番目のブロック = アイコン、 2 番目以降 = テキスト塊として扱う

**アルゴリズム**: 行 ROI ごとに各列の content profile → 連続 True ブロック抽出 (gap < `gap_threshold` で統合) → 各行で 2 番目のブロックの左端 x を比較 → `delta_max > threshold` で FAIL

**踏襲できる部分**:
- ROI 人手指定方式 / 行内 content profile / ブロック抽出 / gap 統合 / debug overlay

**踏襲できない部分**:
- 「アイコン + テキスト」の 2 ブロック前提。 3 ブロック以上が当然のレイアウト (例: アイコン + ラベル + 値) では「テキスト左端」の定義から見直す

## ケーススタディ (命題と判定スクリプトの記録)

### Case 1: 外側 flex に `items-center` 抜け

**命題**: 「左アイコンと右側要素群の縦中心 y が揃っているか」 → `left_circle_vs_right_row_center_y.py` 型

**検出結果**: 左アイコンと右側要素群の中心が 9px (@2x) = 4.5px (@1x) ずれていた

**原因**:
```jsx
<div className={'flex'}>  {/* items-center 抜け! */}
  <div className={'mr-2'}>...左アイコン 40px固定...</div>
  <div className={'flex items-center ...'}>...内側はOK だが...</div>
</div>
```
- 外側 flex のデフォルト `align-items: stretch` で、 隣接する縦長要素 (バッジ等) の高さに引っ張られて内側 div が 50px に拡張
- 左アイコン div も 50px に拡張されるが、 アイコン自体は 40px 固定で top-align → アイコン中心 = 20px
- 内側 div は items-center で 50px の中央 = 25px → **5px ずれ**

**修正**: 外側 div に `items-center` 追加

### Case 2: SVG バッジの幾何中心 ≠ 視覚的中心

**命題**: 「行内に並ぶバッジ群の縦中心 y が、 基準要素の中心 y と揃っているか」 → `left_circle_vs_right_row_center_y.py` 型

**検出結果**:
- バッジA: 2.0px (@2x) = 1px (@1x) 上にずれ
- バッジB: **6.5px (@2x) = 3.25px (@1x) 上にずれ** → FAIL

**原因**: SVG 内部に「アイコン本体 + 下方向に伸びるラベル/リボン」があり、 SVG 画像の幾何中心は視覚的な「アイコン本体の中心」より下に位置. `flex items-center` で SVG 幾何中心を揃えると、 視覚的にはアイコン本体が上に見える

**修正**: SVG 自体は触らず (影響範囲が広い)、 呼び出し側で wrap して下にオフセット:

```jsx
{showBadgeA && (
  <span className={'relative top-px'}>           {/* +1px 下に */}
    <BadgeA />
  </span>
)}
{showBadgeB && (
  <span className={'ml-1 relative top-[3px]'}>   {/* +3px 下に */}
    <BadgeB />
  </span>
)}
```

オフセット値は **(@1x換算ずれ量) を四捨五入** して `top-[Npx]` で指定。 呼び出し側の特定ページだけ補正できる。

### Case 3: 縦に並ぶ複数行の文字左端揃い

**命題**: 「3 行 (各行が左にアイコン + 右にテキスト) で、 テキスト左端 x が揃っているか」 → `multi_row_text_left_x_after_icon.py` 型

**検出結果**:
- row1: text_left=97px (アイコン直後、 ml なし)
- row2: text_left=92px (アイコンの後 ml-1 で隙間あり)
- row3: text_left=95px (アイコン直後、 ml なし)
- delta_max = 5px → FAIL

**修正**: 全行のテキストwrapper に `ml-1` を統一して隙間を揃える:
```jsx
<IconA size={24} className={'text-gray'} />
<div className={'ml-1'}><ContentA ... /></div>
<IconB size={24} className={'text-gray'} />
<Text className={'ml-1 inline-block ...'}>...</Text>
```

**修正後**: text_left=224px で 3 行完全一致 (delta_max=0px → PASS)

## アンチパターン

- **目視で「揃ってる」と即答**: 必ずスクリプトを書いて数値で確認。 これは絶対ルール
- **既存スクリプトをそのまま呼んで命題に合わせない**: 「`left_circle_vs_right_row_center_y.py` がエラーで動かない」「結果が直感と合わない」となったら、 命題とスクリプトの仮定が合っていない。 新規スクリプトを書く
- **threshold を緩めて PASS にする**: 「3px だと FAIL なので 6px にしたら PASS でした」は不正。 threshold は命題ごとに事前に決め、 結果に合わせて変えない
- **debug overlay を省略**: 数値だけ提示しても説得力がない。 必ず PNG 出力する
- **「ほぼ揃ってる」と濁す**: FAIL は FAIL。 修正案まで出す

## 依存

- Python 3.10+ (型ヒント `list | None` を使う)
- numpy
- Pillow (PIL)
- scipy (連結成分が必要なときのみ)
