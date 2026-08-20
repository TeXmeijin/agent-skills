# Agent Skills

個人的によく使っている自作スキルのうち、外部公開できそうなものをまとめています。

このリポジトリは APM package として、次の形式でスキルを配置しています。

```text
.apm/skills/<skill-name>/SKILL.md
```

## スキル一覧
### プロジェクト管理
- `pj-flow` - `.claude/my-projects/` に長期記憶と Thread を積んで、長いPJを会話スレッドをまたいで継続できるようにする。新スレッドでもすぐにAgentがPJの目的、背景、最新情報などを把握してくれるので、説明負荷が下がる。外部ツールとの連携も不要のため高速に動作する。

### ちょっとした作業
- `commit-push` - このスレッドで変更したファイルだけを commit / push する。
- `auto-grouped-commit` - 未コミット変更を読み、推奨グループに分けてコミットまで進める。気がつけばコミットせずに大量の作業をしていたときに使う。
- `video-to-gif` - 動画や画面録画を、記事・README・チャットに貼りやすい軽量なGIFへ変換する。

### よりAgentに明確な指示を出す
- `research` - Web検索と一次情報に基づいて、最新確認から広範な調査まで行う。
- `goal-template-generator` - ラフな依頼を、実行可能な GOAL テンプレートに整える。`/goal`コマンドを次スレッドで使うための下準備。
- `goal-prompt-enqueue` - 依頼を記憶ゼロの自律実行エージェント向けの自己完結GOALファイルに変換し、ホーム直下のキュー(`~/.goal-prompt-queue/inbox/`)に積む。夜間・長時間などの無人実行枠に作業を委譲したいときに使う。実行中に質問できない前提で、配置前に不確実性を潰し切る。
- `goal-prompt-dispatch` - `goal-prompt-enqueue` が積んだGOALを1回の起動につき最大1件取り出し、記憶ゼロ前提で自律実行するランナー。定時トリガーから発火する想定で、`inbox → inprogress → done/error` の4フォルダで競合を避ける。Claude / Codex どちらからでも実行できる。
- `isis` - Issue やチケットを実装前の仮説として調査・整理する。
- `harness-creator` - Red/Green を機械判定できる検証ハーネスを作る。
- `prompt-refiner` - 雑な coding 依頼を、別の agent に渡せる prompt に整える。goalの下位互換かも...

### Claude CodeからCodexに連携
- `codex-exec` - Codex CLI に rescue / review タスクを委譲する。
- `codex-collab-review` - Claude Code と Codex CLI で協働レビューを行う。

### UIデザイン
- `centering-judge` - 画像の整列 (中央揃え / 左端揃え / 間隔均等 等) を画素単位で判定するスクリプトを、 命題ごとに新規実装して走らせる skill。LLM の主観で「揃ってる」と誤判定するのを防ぐためのメタ手法。 固定スクリプトは持たず、 共通道具箱 (背景マスク / content profile / debug overlay 等) と参考実装を提供する。
- `image-redaction` - 社内情報や固有情報を含むスクリーンショットを、公開方針に合わせてピンポイントにマスクする。画像ごとに専用スクリプトで文字行座標を計算し、ffmpeg/ImageMagickで公開用画像を生成する。

### 文章・執筆
- `clean-ai-writing-style` - 日本語AI文章の徹底批評ループ。論理飛躍・知識飛躍・AIっぽい表現・構成の悪さを、読者知識→セクション→段落→表現の順に構造から直す。k16shikano氏の [japanese-tech-writing](https://gist.github.com/k16shikano/fd287c3133457c4fd8f5601d34aa817d) / [cognitive-rhythm-writing](https://gist.github.com/k16shikano/eb2929f13ed19c97188393d297be8432) と併用する前提。

### 特定のタスク
- `ghostty-applescript` - Ghostty 対応のレイアウトを AppleScript で実装する。
- `cloudwatch-logs-insights-query` - CloudWatch Logs Insights QL のクエリを作成・検証する。
- `yarn-classic-to-pnpm` - Yarn Classic から pnpm v11+ への移行をしつつ、依存バージョン差分を監査して、Patch Versionに至るまでバージョン差異を報告する。

## APM でインストール

```sh
apm install TeXmeijin/agent-skills --target agent-skills,claude,codex
```

ユーザースコープにインストールする場合:

```sh
apm install -g TeXmeijin/agent-skills --target agent-skills,claude,codex
```

個別のスキルだけをインストールする場合:

```sh
apm install -g TeXmeijin/agent-skills --skill pj-flow --target agent-skills,claude,codex
```

複数のスキルを選ぶ場合:

```sh
apm install -g TeXmeijin/agent-skills \
  --skill pj-flow \
  --skill codex-exec \
  --target agent-skills,claude,codex
```

すべてのスキルに戻す場合:

```sh
apm install -g TeXmeijin/agent-skills --skill '*' --target agent-skills,claude,codex
```

## ローカル開発

ローカルで編集する場合は、このリポジトリを source of truth にして、各実行環境のスキル配置先へ symlink します。

```sh
./scripts/link-local.sh
```

このスクリプトは、既存の実ディレクトリをバックアップしてから symlink に置き換えます。
