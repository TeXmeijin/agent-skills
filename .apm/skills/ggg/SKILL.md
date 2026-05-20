---
name: ggg
description: Use when the user explicitly asks to search the web, verify freshness, check whether a prior answer is current, or says "ググって", "検索して", "本当に？", "それ最新？", or similar. Always use web search, prioritize official/current sources, and cite URLs.
---

# ggg - Web Search Skill

Google検索スキル。LLMの学習データに頼らず、必ずWebSearchツールで最新情報を取得する。

## Triggers

- `/ggg <query>` — 明示的呼び出し
- 「ググれ」「ググって」「検索して」— 日本語での検索指示
- 「本当に？」「それ最新？」「合ってる？」— ユーザーが疑義を示したとき（前の回答の裏取りとして発動）

## Rules

1. **必ずWebSearchを使う**: LLMの知識だけで回答してはならない。知っていると思っても検索する
2. **実行日時点の最新情報を優先する**: 検索クエリに年号（例: "2026"）を含めて古い情報を排除する
3. **公式ソースを最優先**: 公式ドキュメント・公式ブログ・リリースノートを先に探す
4. **公式で不足なら広げる**: Stack Overflow、Zenn、個人ブログ、Reddit、GitHub Issues/Discussions も検索する
5. **検索クエリを工夫する**:
   - 英語と日本語の両方で検索する（技術トピックは英語優先）
   - 具体的なエラーメッセージやバージョン番号を含める
   - 1回の検索で足りなければクエリを変えて再検索する
6. **ソースを明示する**: 回答には参照元URLを必ず含める
7. **疑義トリガーの場合**: 前の回答のどの部分が不正確だったか／最新でなかったかを明確にする

## Output Format

- 結論を先に、根拠を後に
- 参照元URLを箇条書きで末尾に記載
- 情報の鮮度（記事の公開日・更新日）がわかれば併記する
