# 001. 既存認証済み CLI による前後 RED/GREEN 判定型ハーネス [system]

このパターンは **system harness**（REPF 全要件を備える）に分類される。unit harness で済むケース（hook 一発で完結する自動検証など）には過剰なので、適用領域を確認のうえ採用すること。

## 形質（このパターンが効く問題）

- ある作業について、**着手前の状態（RED）と完了後の状態（GREEN）を機械的に判定**したい
- 判定に必要な情報が、マシン内に**既に認証済みの CLI**（クラウドプロバイダ CLI、リポジトリホスティング CLI、データベースクライアント、SaaS CLI など）から **読み取り権限のみで取得可能**である
- 作業内容は同形でも非同形でもよく、対象数は **1 個でも、複数でも適用可能**（同形作業の反復は必須要件ではない）
- 人間の目視確認や Web Console での画面確認に依存したくない（再現性・冪等性が欲しい）
- 作業途中で中断・再開しても、`check.sh` 一発で **現在地** が分かる状態にしたい

## 前提

- 必要な CLI（任意の組み合わせ：例えば クラウド A の CLI、SaaS B の CLI、コードホスティング C の CLI、DB クライアントなど）が **読み取り権限で認証済み**である
- CLI が走らせるコマンドは **list / get / describe / show / inspect 系のみ**（破壊的操作なし、副作用なし、冪等）
- 着手前にスクリプト先頭で **認証チェック** を行い、いずれか 1 つでも失敗したら fail-fast する

## アウトプットの形

| ファイル / 構造          | 役割                              | 形                                                                                                |
| ------------------------ | --------------------------------- | ------------------------------------------------------------------------------------------------- |
| `check.sh`               | R: 状態観測スクリプト             | bash。観測領域ごとにサブモードを切る（`bash check.sh`, `bash check.sh <subset>`）。表形式 + Summary |
| `baseline-YYYY-MM-DD.*`  | R: 着手時点の RED スナップショット | `check.sh` の初回出力をリダイレクトしただけのテキスト                                              |
| 作成用リソースファイル群 | E: 必要に応じて                  | 構造化テキスト（JSON / YAML 等）。各プロバイダの作成系 CLI に `--file://` で直接食わせられる形    |
| 差分パッチ・完成版設定   | E: 必要に応じて                  | 既存設定への差分 / 置換用ファイル                                                                 |
| `PROGRESS.md`            | P: 進捗表                         | Markdown。Phase × Item × Owner × 状態                                                            |
| `README.md`              | F: 使用者向けフロー               | 認証要件 / 使い方 / トラブルシュート / Owner 明示                                                |

対象数 = 1 のケースでも、`check.sh` と `README.md` と `PROGRESS.md` は最低限必要（REPF を満たすため）。リソースファイルや差分パッチは作業内容次第で省略可能。

## check.sh の設計判断

- **サブモード分割**：観測領域が複数あるなら（例：プロバイダごと、レイヤーごと、対象種別ごと）、領域単位で部分実行できるようにする。引数なしで全実行。フィードバックループを短く保つため。観測対象が 1 つしかなければサブモードは不要
- **表形式 + 固定幅出力**：`CATEGORY / ITEM / STATUS / DETAIL` の 4 列を `printf` で揃える。`grep RED` で未達だけ抽出する用途に強い
- **STATUS は 3 値**：`✅ GREEN` / `⚠️ WARN` / `❌ RED`。WARN は「ファイルは存在するが中身が古い」「リソースは存在するが設定値が不完全」のような中間状態に必須。これがないと進捗観測が二値になりすぎて使い物にならない
- **Summary 行**：末尾に `Summary: GREEN=X WARN=Y RED=Z / TOTAL=N` を出す。これが PR description や進捗共有のスナップショットとして使える
- **冪等**：何度走らせても副作用ゼロ。観測専用
- **fail-fast**：認証失敗を無音 RED にしない。スクリプト先頭で各 CLI の認証確認を行い、失敗したら exit する。RED が「設定未完」なのか「観測不能」なのかが混ざると進捗が破綻する

## 学び・落とし穴

- **設定ファイルの記述と実態の乖離**：参照する既存ポリシー/設定ファイルに書かれているリソース ID 名と、実際にクラウド側に存在する ID が**ずれている**ケースがある。観測時は **CLI で実態を取って ID を確定**し、設定ファイル側を実態に合わせる。設定ファイル盲信は本番障害の温床
- **既存環境の GREEN 実証の前提化**：参照元となる類似環境（例：開発／ステージング）の最新ワークフロー実行が `failure` のまま放置されているケースがある。これを参照実装として使うと、塞いでいない問題を新環境で踏む。ハーネス着手前のチェック項目に **「参照元の GREEN 実証」** を入れる
- **シェル言語仕様の罠**：bash のスコープ（`local` をトップレベルで使うとエラー）や、相対パス計算のネスト段数ずれは、書いた瞬間は気付きにくい。**baseline 取得を着手の最初の儀式にする**と、これらの初期実装バグが初回で全部出る
- **観測軸の取りこぼし**：「リソース存在」「権限割当」「設定値内容」「依存リソース整合性」など、観測すべき軸が複数あるとき、最初に**全軸を表で列挙**してから `check.sh` を実装する。後から軸が増えると `PROGRESS.md` と `check.sh` の構造が破綻する
- **Owner 欄は必須**：権限を要する操作を人間が担当し、ファイル生成や下準備をエージェントが担当する、というように Owner が混在する場合、README と PROGRESS の両方に Owner を明示する。Owner なしの表は「誰の番か」が霧消する
- **中間状態の WARN は嘘をつかない設計に**：例えば「設定ファイルは存在するが、旧方式の参照がまだ残っている」のような状態は、ファイル存在チェックだけだと GREEN になるが、内容パターンも見ないと WARN にできない。観測ロジックは**達成条件の最終形をパターンで検査**するように書く
- **cheat sheet は併設してよい、ただし本体ではない**：人間が Web Console や対話シェルで叩くコマンド列を、コピーボタン付き HTML や Markdown でまとめておくのは UX として有効。ただしこれは**ハーネスの出力先 / アクセサリ**であって、ハーネス本体は `check.sh` + `PROGRESS.md` + リソースファイル群である。混同しない

## 再利用可能なテンプレ・スニペット

### check.sh のスケルトン（対象数=1 でも複数でも使える）

```bash
#!/usr/bin/env bash
set -euo pipefail

# 観測対象表（1 個でも複数でも可）
ITEMS_A=( ... )
ITEMS_B=( ... )

# 認証チェック（fail-fast）
require_authed() {
  local cli="$1" probe="$2"
  if ! eval "$probe" >/dev/null 2>&1; then
    echo "ERROR: $cli is not authenticated. Aborting." >&2
    exit 2
  fi
}
# 例: require_authed "<provider-cli>" "<provider-cli whoami>"

print_header() {
  printf "=== <Harness Name> Status (%s) ===\n" "$(date '+%Y-%m-%d %H:%M:%S')"
  printf "%-15s %-65s %-10s %s\n" "CATEGORY" "ITEM" "STATUS" "DETAIL"
  printf "%-15s %-65s %-10s %s\n" "--------" "----" "------" "------"
}

green=0; warn=0; red=0
emit() {
  local category="$1" item="$2" status="$3" detail="$4"
  printf "%-15s %-65s %-10s %s\n" "$category" "$item" "$status" "$detail"
  case "$status" in
    "✅ GREEN") green=$((green+1));;
    "⚠️ WARN")  warn=$((warn+1));;
    "❌ RED")   red=$((red+1));;
  esac
}

mode="${1:-all}"
print_header

if [[ "$mode" == "a" || "$mode" == "all" ]]; then
  for it in "${ITEMS_A[@]}"; do
    # ... read-only CLI で観測 → emit を呼ぶ
    :
  done
fi

if [[ "$mode" == "b" || "$mode" == "all" ]]; then
  for it in "${ITEMS_B[@]}"; do
    :
  done
fi

echo
printf "Summary:\tGREEN=%d  WARN=%d  RED=%d / TOTAL=%d\n" "$green" "$warn" "$red" "$((green+warn+red))"
[[ $red -eq 0 ]] || exit 1
```

### PROGRESS.md のテーブル

```
| Phase | Item | Owner | RED 観測 (check.sh の行) | GREEN 条件 | 状態 |
|---|---|---|---|---|---|
| 1 | item-a | 指示者 | Category-X / item-a / RED | check.sh が item-a GREEN | ⏳ |
| 1 | item-b | エージェント | Category-Y / item-b / RED | check.sh が item-b GREEN | ⏳ |
```

### README.md の最低構成

```
# <Harness Name>

## このハーネスのゴール
<1 段落で書く。何を、どの状態にすることがゴールか>

## 認証要件
- 使う CLI とその読み取り権限を列挙
- check.sh の冒頭で認証チェックが走り、失敗時は即終了する

## 使い方
1. `bash check.sh > baseline-YYYY-MM-DD.txt`：着手時点の RED スナップショット
2. PROGRESS.md を見て、Owner = 指示者 の Phase を消化
3. Owner = エージェント の Phase はエージェントが消化
4. 各 Phase 完了後に `bash check.sh <該当領域>` で GREEN 確認
5. Summary が `RED=0` になればハーネス完了

## トラブルシュート
- 認証失敗 → 各 CLI の再認証手順
- WARN が出た → 中間状態の解消手順
```

## 適用範囲の判定ガイド

このパターンを採用していいケース：

- 検証が必須（失敗が許されない、または前後の状態を厳密に確認したい）
- 検証に必要な情報が、既存の認証済み CLI から読み取り権限のみで取れる
- 観測対象が 1 つ以上（複数でも同形でも非同形でも可）
- 同じ作業を後日反復する可能性がある、または別の人が再現する可能性がある

このパターンを採用すべきでないケース：

- 観測対象の状態を CLI から取得する手段が存在しない（→Web Console 専用画面しかないなど。先に CLI 化 / API 化を検討）
- 観測が必要ない、目視で十分な単発作業（→ runbook で十分）
- 観測結果を機械的に二値化／三値化できない（→ハーネスではなく設計レビューや探索的調査）
