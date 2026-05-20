# Agent Skills

個人的によく使っている自作スキルのうち、外部公開できそうなものをまとめています。

このリポジトリは APM package として、次の形式でスキルを配置しています。

```text
.apm/skills/<skill-name>/SKILL.md
```

## スキル一覧
### ちょっとした作業
- `commit-push` - このスレッドで変更したファイルだけを commit / push する。
- `non-committed-analyzer` - 未コミット変更を読み、コミット分割案や検証手順を出す。気がつけばコミットせずに大量の作業をしていたときに使う。
- `pj-flow` - `.claude/my-projects/` に長期記憶と Thread を積んで、長いPJを会話スレッドをまたいで継続できるようにする。

### よりAgentに明確な指示を出す
- `ggg` - 最新性が重要な質問で Web 検索に基づいて回答するように強制する。Web検索をサボってきたときに使う。
- `goal-template-generator` - ラフな依頼を、実行可能な GOAL テンプレートに整える。`/goal`コマンドを次スレッドで使うための下準備。
- `isis` - Issue やチケットを実装前の仮説として調査・整理する。
- `harness-creator` - Red/Green を機械判定できる検証ハーネスを作る。
- `prompt-refiner` - 雑な coding 依頼を、別の agent に渡せる prompt に整える。goalの下位互換かも...

### Claude CodeからCodexに連携
- `codex-exec` - Codex CLI に rescue / review タスクを委譲する。
- `codex-collab-review` - Claude Code と Codex CLI で協働レビューを行う。

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

## ローカル開発

ローカルで編集する場合は、このリポジトリを source of truth にして、各実行環境のスキル配置先へ symlink します。

```sh
./scripts/link-local.sh
```

このスクリプトは、既存の実ディレクトリをバックアップしてから symlink に置き換えます。
