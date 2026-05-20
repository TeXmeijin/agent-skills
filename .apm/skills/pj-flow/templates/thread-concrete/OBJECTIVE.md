# OBJECTIVE — Concrete系 Thread

> 情報収集・仕様具体化を主眼とするThread。purposeは `concrete` / `reconcrete` / `spike` など。

## 参照Thread(s)

このThreadが成果を受け継ぐThread（空でもOK。起点concreteなら空）:

- `<PROJECTS_ROOT>/<slug>/threads/<ref-thread>/OUTPUT.md`

## 上書き対象（前提が覆った場合のみ）

- `<PROJECTS_ROOT>/<slug>/threads/<old-thread>/OUTPUT.md`
- 上書き理由: （なぜ旧OUTPUTが古くなったか。Project長期記憶の `updated_at` も更新すること）

空でよい。空なら「上書き対象なし」と宣言して削除/維持のどちらでも。

## 施策概要

（`<slug>/CLAUDE.md` の要約をコピペでOK。Thread開始時点の認識を固定する）

## このThreadの目的

以下を明らかにする（実装は行わない）:

- （明らかにしたい項目 1）
- （明らかにしたい項目 2）
- （明らかにしたい項目 3）

## 調査観点

- [ ] コードベース
  - 対象repo: （server / client / app 等）
  - 推定パス:
- [ ] 過去Issue / PR
- [ ] Git履歴
- [ ] DB構造（Migration → Model の順）
- [ ] 実データ（local / staging / production SQL, Firestore, BigQuery）
- [ ] AWS / インフラ
- [ ] Sentry / 運用ログ

## Done定義

- [ ] OUTPUT.md に詳細仕様（要件・制約・実装方針・影響範囲）が書かれている
- [ ] Open Questions が列挙されている（空ならその旨を明記）
- [ ] 次Threadが着手に必要な前提を全て持っている状態

## 留意事項

- 実装コードは書かない（検証用のちいさなスニペットは除く）
- Assets（スクショ・CSV・SQL結果・メモ）は本フォルダに自由配置
