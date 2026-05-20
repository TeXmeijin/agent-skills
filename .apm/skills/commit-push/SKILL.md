---
name: commit-push
description: このスレッドで変更したファイルだけをコミット、プッシュ
disable-model-invocation: true
---

# commit-push

このスレッドで変更したファイルだけをコミット、プッシュして。
ブランチがDevelopなど関係ないブランチの場合は大事故なので先にブランチ確認する。

## 注意点：直列実行

コミット時、lint-staged等のGitHookが実行されるケースがあるので、コミットが確実に成功したことを確認してからプッシュすること。並列に実行してはならない。

## PR作成

Push後、当該ブランチでまだPRが未作成の場合、ユーザーにAskしたうえで、
ghコマンドを利用してPRを作成する。
```sh
gh pr create --base develop --title "commitzen style title in Japanese" --body "body in Japanese"
```

## [重要]保護ブランチでの実行ルール
main/productionブランチの場合、必ず確認: 「{branch}ブランチです。新しいブランチを切りますか？それとも{branch}に直接コミットしますか？」
明示的に「{branch}に直接コミット」と言われた場合のみ実行する。

### 例外: developブランチ
ユーザーが引数で `develop` を指定した場合は、確認不要でダイレクトにコミット＆プッシュしてよい。
