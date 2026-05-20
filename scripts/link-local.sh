#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
backup_root="${HOME}/.agent-skills-backup/$(date +%Y%m%d%H%M%S)"

skills=(
  ghostty-applescript
  cloudwatch-logs-insights-query
  goal-template-generator
  prompt-refiner
  non-committed-analyzer
  yarn-classic-to-pnpm
  isis
  codex-exec
  codex-collab-review
  commit-push
  harness-creator
  ggg
  pj-flow
)

link_one() {
  local target_dir="$1"
  local skill="$2"
  local src="${repo_root}/.apm/skills/${skill}"
  local dst="${target_dir}/${skill}"

  mkdir -p "$target_dir"

  if [[ -L "$dst" ]]; then
    rm "$dst"
  elif [[ -e "$dst" ]]; then
    mkdir -p "${backup_root}${target_dir}"
    mv "$dst" "${backup_root}${target_dir}/${skill}"
  fi

  ln -s "$src" "$dst"
}

for skill in "${skills[@]}"; do
  link_one "${HOME}/.agents/skills" "$skill"
done

for skill in "${skills[@]}"; do
  link_one "${HOME}/.claude/skills" "$skill"
done

for skill in cloudwatch-logs-insights-query goal-template-generator yarn-classic-to-pnpm; do
  link_one "${HOME}/.codex/skills" "$skill"
done

if [[ -d "$backup_root" ]]; then
  echo "Backed up replaced directories under: $backup_root"
fi

echo "Linked ${#skills[@]} skills from: $repo_root"
