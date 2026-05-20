# pbcopy-prompts — Thread終了時の次Threadキックオフプロンプト

pj-flow ではThreadを閉じる（OUTPUT.md を書き切る）瞬間に、**次Thread1通目用のプロンプトを pbcopy** する。`/new` 直後に Cmd+V で貼り付けるだけで再開できる状態を作る。

**プロンプト本文に前ThreadのOUTPUT要旨を埋め込まない**（ドリフト防止）。参照先パスだけを正確に列挙する。
**「直前Thread」を自動的に参照先にしない**（旧Ground Rule踏襲）。どのThreadの成果を受け継ぐかは新Thread側で意識的に選ぶ。

---

## A. 標準テンプレ（次Thread を切る場合）

```bash
pbcopy << 'EOF'
# 新Thread: <slug> / <purpose>

## 参照必須
- スキル: pj-flow
- Project長期記憶: <PROJECTS_ROOT>/<slug>/CLAUDE.md
- 参照Thread(s):
  - <PROJECTS_ROOT>/<slug>/threads/<ref-thread-A>/OUTPUT.md
  - <PROJECTS_ROOT>/<slug>/threads/<ref-thread-B>/OUTPUT.md  # 複数可
- 当Thread OBJECTIVE: <PROJECTS_ROOT>/<slug>/threads/<new-thread>/OBJECTIVE.md

## 役割
<purpose> — <1〜2行の要約>

## 前提の取り扱い
- 前提変更がある場合、上書き対象: <PROJECTS_ROOT>/<slug>/threads/<old-thread>/OUTPUT.md
  （理由は新Thread OBJECTIVEに記載済み）

## 最初にやること
1. 上記参照先を全て読む
2. OBJECTIVE.md の Done定義 と照らし合わせて作業に着手
EOF
```

---

## B. PJ再開テンプレ（Threadは切らず既存Threadの続きをやる場合）

```bash
pbcopy << 'EOF'
# PJ再開: <slug>

## 参照必須
- スキル: pj-flow
- Project長期記憶: <PROJECTS_ROOT>/<slug>/CLAUDE.md
- 最新Thread: <PROJECTS_ROOT>/<slug>/threads/<latest-thread>/

## 続きから
最新Threadの OBJECTIVE.md / OUTPUT.md を読み、未完了タスク・残作業から再開する。
EOF
```

---

## C. PJ Close 後のお知らせテンプレ（任意）

```bash
pbcopy << 'EOF'
PJ Close: <slug> をクローズしました。
- PR: <pr_url>
- merged_at: YYYY-MM-DD
- 長期記憶: <PROJECTS_ROOT>/<slug>/CLAUDE.md（status=closed）

長期参照不要になったら手動で status: archived へ。
EOF
```

---

## 実装ノート

- `pbcopy` は macOS 標準。Linux なら `xclip -selection clipboard` / `wl-copy` 等に置換
- ヒアドキュメントは `<< 'EOF'`（シングルクォート付き）でシェル変数展開を抑止する
- 同じ Prompt 本文を会話にも **fenced code block** で出す（ユーザーがレビューできるように）
