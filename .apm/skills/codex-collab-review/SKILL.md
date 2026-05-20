---
name: codex-collab-review
description: Claude Code と Codex CLI が tmux ペインで協働してコードレビューを行う。独立レビュー→突き合わせ→議論・説得→合意形成の4段階。片方だけの指摘はもう片方に問い、同意が得られたもののみ最終指摘に掲載する。PR URL、ブランチ名、またはファイルパスを指定して使用する。トリガー：「Codexと一緒にレビュー」「協働レビュー」「Wチェックレビュー」「codex collab review」「ダブルチェックレビュー」
---

# Codex 協働レビュー

Claude と Codex が同じ差分を独立レビューし、議論・説得を経て**両者が合意した指摘のみ**最終レビューに掲載する。

## 核心原則

**合意形成型レビュー。** 片方だけの指摘は最終レビューに載せない。
片方が見つけた指摘は、もう片方に「この指摘についてどう思う？」と問い、説得して同意を得たもののみ掲載する。逆に、もう片方が「それは問題ではない」と反論し、指摘側が納得した場合は取り下げる。

## 前提条件

- tmux セッション内で実行されていること
- `codex` CLI がインストール済みであること
- GitHub CLI (`gh`) でPR情報を取得できること

## ワークフロー

### Phase 1: 差分の取得

1. PR URLまたはブランチから差分を取得
   ```
   gh pr diff <number> > $TMPDIR/pr_review.diff
   # 差分が大きすぎる場合(20K行超)はgit diffで取得
   git fetch origin <branch> <base> && git diff origin/<base>...FETCH_HEAD > $TMPDIR/pr_review.diff
   ```
2. PR本文と変更ファイル一覧を取得して全体像を把握
3. 変更規模に応じてレビュー観点を3-5個設定する

### Phase 2: 独立レビュー（Claude と Codex が並行）

複数ペイン並列で観点を分散する。

```bash
# ペイン作成
tmux split-window -h -t <session>:<window>

# Codex起動: 必ず「テキスト送信」と「Enter送信」を分離する
# NG: tmux send-keys -t <pane_id> "codex '...'" Enter  ← Enterが届かないことがある
# OK: 以下の2ステップで送る
tmux send-keys -t <pane_id> "codex '...レビュープロンプト...'"
tmux send-keys -t <pane_id> Enter
```

**重要: `tmux send-keys` の Enter 送信ルール**
- `tmux send-keys` でテキストと `Enter` を同じコマンドに含めると、Codex のインタラクティブプロンプトに Enter が届かないケースがある
- **必ずテキスト送信と Enter 送信を別々の `tmux send-keys` 呼び出しに分ける**
- Codex 起動後のプロンプト入力でも同様:
  ```bash
  # Step 1: テキストを入力
  tmux send-keys -t <pane_id> "質問テキスト"
  # Step 2: Enter を送信
  tmux send-keys -t <pane_id> Enter
  ```
- 送信後は `tmux capture-pane` で `Working` 表示が出ているか確認し、出ていなければ再度 `Enter` を送る

Claude は Codex と**同じ差分・同じ観点**を独立にレビューする。観点の重複は意図的。

### Phase 3: 突き合わせ

Codex 完了後、`tmux capture-pane -t <pane_id> -p -S -300` で結果を回収。

Claude は自身の指摘リストと Codex の指摘リストを突き合わせ、3カテゴリに分類する:

| カテゴリ | 内容 | 次のアクション |
|---------|------|--------------|
| **一致** | 両者が同じ問題を指摘 | → そのまま最終指摘へ |
| **Claude単独** | Claude のみ指摘 | → Phase 4 で Codex に問う |
| **Codex単独** | Codex のみ指摘 | → Phase 4 で Claude が検証 |

### Phase 4: 議論・説得（このフェーズが最重要）

#### Claude 単独指摘 → Codex に問う

Codex ペインに、Claude の指摘を提示して意見を求める。**質問が長い場合はファイル経由で渡す:**

```bash
# 方法1: 短い質問 → 直接入力（2ステップ必須）
tmux send-keys -t <pane_id> "質問テキスト"
tmux send-keys -t <pane_id> Enter

# 方法2: 長い質問 → ファイル経由（推奨）
cat > $TMPDIR/codex_question.txt << 'PROMPT'
I found the following issue in the PR diff at $TMPDIR/pr_review.diff.
Do you agree this is a real problem? If not, explain why.

Issue: <Claudeの指摘内容>
File: <ファイルパス:行番号>
Reasoning: <Claudeの根拠>

Answer with AGREE (and why) or DISAGREE (and why).
PROMPT

tmux send-keys -t <pane_id> "Read $TMPDIR/codex_question.txt and answer the questions inside."
tmux send-keys -t <pane_id> Enter
```

**送信後の確認手順:**
1. `sleep 3 && tmux capture-pane -t <pane_id> -p -S -5` で状態を確認
2. `Working` が表示されていれば処理中 → 待機
3. プロンプト `›` のままテキストだけ表示されていたら Enter が届いていない → `tmux send-keys -t <pane_id> Enter` を再送

#### Codex 単独指摘 → Claude が検証

Claude 自身が該当コードを読み直し、Codex の指摘が妥当か判断する。
- 妥当なら AGREE（見落としを認める）
- 妥当でないなら DISAGREE の根拠を Codex に返し、再度 Codex に判断を問う

#### 議論ルール

- 各指摘について最大 **2往復** まで。2往復で合意できなければ「未合意」として最終レビューの付録に回す
- 「AGREE」は「たしかにこれは対応すべき問題だ」の意味。「指摘の存在は認めるが対応不要」は DISAGREE
- 説得する側は**コードの具体的な箇所**を根拠にする。「一般的に良くない」は根拠にならない

### Phase 5: 最終レビュー作成

**合意した指摘のみ** 掲載する。

```markdown
# PR #<number> 協働レビュー結果
**Claude + Codex CLI 合意形成型レビュー**

## Critical（マージ前に対応必須）

### C-1. <指摘タイトル>
- **内容**: ...
- **該当箇所**: file:line
- **合意過程**: 両者独立に検出 / Claude指摘→Codex同意 / Codex指摘→Claude同意

## Warning（マージ可だが早期修正推奨）
### W-1. ...

## Info（改善推奨）
### I-1. ...

---

## 付録: 未合意の指摘（参考）
> 以下は議論の結果、合意に至らなかった指摘。判断はPR作成者に委ねる。

### X-1. <指摘タイトル>
- **主張側**: Claude / Codex
- **主張**: ...
- **反論**: ...
- **不合意理由**: ...
```

### Phase 6: クリーンアップ（完了時に必ず実行）

レビュー完了後、以下の手順でリソースを片付ける:

```bash
# 1. Codex セッションを終了
tmux send-keys -t <pane_id> "/exit"
tmux send-keys -t <pane_id> Enter

# 2. 少し待ってから Codex ペインを閉じる
sleep 2 && tmux kill-pane -t <pane_id>

# 3. 一時ファイルを削除
rm $TMPDIR/pr_review.diff $TMPDIR/codex_question.txt $TMPDIR/codex_*.txt 2>/dev/null
```

## ペイン数の目安

| 差分規模 | Codexペイン数 | reasoning | 備考 |
|---------|-------------|-----------|------|
| ~500行  | 1           | high      | 議論フェーズも同じペインで |
| 500-3000行 | 2        | medium    | 観点を分散 |
| 3000行~ | 2-3         | medium    | 観点を分散、議論は1ペインに集約 |

## 注意事項

- Codex の出力はtmuxバッファサイズに制限がある。長い出力は `-S -300` 等で広く取得する
- Codex セッションが残っている場合は `/exit` してから新しいプロンプトを送る
- 差分ファイルは `$TMPDIR` に保存する
- 議論フェーズでは Codex に前回の出力のコンテキストがないため、指摘内容と根拠を毎回完全に伝える
- `--reasoning` フラグは Codex のバージョンによって使えない場合がある。エラーが出たらフラグなしで再実行する

## tmux send-keys の鉄則

Codex のインタラクティブプロンプトにテキストを送る際は、**必ず以下の2ステップで行う:**

```bash
# Step 1: テキストを送信（Enter は含めない）
tmux send-keys -t <pane_id> "テキスト"

# Step 2: Enter を別コマンドで送信
tmux send-keys -t <pane_id> Enter
```

**やってはいけないこと:**
```bash
# NG: テキストとEnterを同じコマンドで送る → Enterが届かないことがある
tmux send-keys -t <pane_id> "テキスト" Enter
```

**送信確認の手順:**
```bash
# 3秒後にペインを確認
sleep 3 && tmux capture-pane -t <pane_id> -p -S -5

# 「Working」が見えたら → 処理中、待つ
# プロンプト「›」のままテキストだけ見えたら → Enter未到達、再送する
tmux send-keys -t <pane_id> Enter
```
