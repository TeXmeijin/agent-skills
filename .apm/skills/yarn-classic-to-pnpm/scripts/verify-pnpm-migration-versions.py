#!/usr/bin/env python3
"""Compare Yarn Classic and pnpm resolved package versions.

This tool intentionally has no third-party dependencies. It supports three
evidence sources:

1. lockfile: yarn.lock v1 vs pnpm-lock.yaml
2. node-modules: installed node_modules package.json files
3. list-json: `yarn list --json` vs `pnpm list --json --depth Infinity`

All comparisons use the same `(package name, version)` set as the unit. The
lockfile mode additionally detects npm alias false positives where Yarn records
the alias name but pnpm records the real package name.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

PackageSet = set[tuple[str, str]]
AliasMap = dict[str, set[tuple[str, str]]]
PROJECTS = (
    ("server", "server"),
    ("global-app/server", "global-app/server"),
    ("global-app", "global-app"),
)

YARN_ALIAS_SPEC = re.compile(r"^(@?[^@]+(?:/[^@]+)?)@npm:(@?[^@]+(?:/[^@]+)?)@(.+)$")
PNPM_PACKAGE_KEY = re.compile(r"^  (['\"]?)([^ '\"].+?)\1:\s*$")
PNPM_ALIAS_LINE = re.compile(
    r"^\s+'?([@A-Za-z][^':]*?)'?:\s+'(@[A-Za-z][^/@']*/[^@']+|[A-Za-z][^@']*)@([^']+)'\s*$"
)


def split_package_at_version(value: str) -> tuple[str, str] | None:
    """Split `name@version`, preserving scoped package names."""
    if value.startswith("@"):
        index = value.find("@", 1)
    else:
        index = value.rfind("@")
    if index <= 0:
        return None
    name = value[:index]
    version = value[index + 1 :]
    if not name or not version:
        return None
    return name, version


def semver_major(version: str) -> int | None:
    match = re.match(r"^(\d+)\.", version)
    if not match:
        return None
    return int(match.group(1))


def parse_yarn_lock(path: Path) -> tuple[PackageSet, AliasMap]:
    seen: PackageSet = set()
    aliases: AliasMap = defaultdict(set)
    content = path.read_text()

    for raw_block in re.split(r"\n\n+", content):
        block = raw_block.strip()
        if not block or block.startswith("#"):
            continue
        first = block.split("\n", 1)[0].rstrip(":").strip()
        keys = [key.strip().strip('"') for key in first.split(",")]
        names_in_block: set[str] = set()
        version_match = re.search(r'\n  version "([^"]+)"', "\n" + block)
        if not version_match:
            continue
        version = version_match.group(1)

        for key in keys:
            if not key:
                continue
            alias_match = YARN_ALIAS_SPEC.match(key)
            if alias_match:
                alias_name, real_name, _real_spec = alias_match.groups()
                names_in_block.add(alias_name)
                aliases[alias_name].add((real_name, version))
                continue
            parsed = split_package_at_version(key)
            if parsed:
                names_in_block.add(parsed[0])

        for name in names_in_block:
            seen.add((name, version))

    return seen, aliases


def parse_pnpm_lock(path: Path) -> tuple[PackageSet, AliasMap]:
    seen: PackageSet = set()
    aliases: AliasMap = defaultdict(set)
    in_packages = False

    with path.open() as file:
        for line in file:
            if line.startswith("packages:"):
                in_packages = True
                continue
            if line.rstrip() and line[0].isalpha() and in_packages:
                in_packages = False

            if in_packages:
                match = PNPM_PACKAGE_KEY.match(line)
                if match:
                    key = re.sub(r"\([^)]+\)+$", "", match.group(2))
                    parsed = split_package_at_version(key)
                    if parsed:
                        seen.add(parsed)

            alias_match = PNPM_ALIAS_LINE.match(line)
            if alias_match:
                left, right_name, right_version = alias_match.groups()
                if left != right_name:
                    clean_version = re.sub(r"\([^)]+\)+$", "", right_version).strip()
                    aliases[left].add((right_name, clean_version))

    return seen, aliases


def package_json_set_from_node_modules(node_modules: Path) -> PackageSet:
    seen: PackageSet = set()
    skip_dirs = {".bin", ".cache"}

    for root, dirs, files in os.walk(node_modules):
        dirs[:] = [directory for directory in dirs if directory not in skip_dirs]
        if "package.json" not in files:
            continue
        package_json = Path(root) / "package.json"
        try:
            data = json.loads(package_json.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        name = data.get("name")
        version = data.get("version")
        if isinstance(name, str) and isinstance(version, str):
            seen.add((name, version))

    return seen


def yarn_list_set(path: Path) -> PackageSet:
    seen: PackageSet = set()
    payload = None
    for line in path.read_text().splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("type") == "tree":
            payload = item.get("data")
            break
    if not isinstance(payload, dict):
        return seen

    def visit(nodes: Iterable[object]) -> None:
        for node in nodes:
            if not isinstance(node, dict):
                continue
            if node.get("shadow") is True:
                continue
            node_name = node.get("name")
            if isinstance(node_name, str):
                parsed = split_package_at_version(node_name)
                if parsed:
                    seen.add(parsed)
            children = node.get("children")
            if isinstance(children, list):
                visit(children)

    trees = payload.get("trees")
    if isinstance(trees, list):
        visit(trees)
    return seen


def pnpm_list_set(path: Path) -> PackageSet:
    seen: PackageSet = set()
    data = json.loads(path.read_text())

    def visit(node: object, fallback_name: str | None = None) -> None:
        if not isinstance(node, dict):
            return
        name = node.get("name") or node.get("from") or fallback_name
        version = node.get("version")
        if isinstance(name, str) and isinstance(version, str):
            seen.add((name, version))
        for key in ("dependencies", "devDependencies", "optionalDependencies"):
            deps = node.get(key)
            if isinstance(deps, dict):
                for dep_name, child in deps.items():
                    visit(child, dep_name)

    if isinstance(data, list):
        for root in data:
            visit(root)
    else:
        visit(data)
    return seen


def resolve_aliases(
    yarn_only: PackageSet,
    yarn_aliases: AliasMap,
    pnpm_aliases: AliasMap,
    pnpm_set: PackageSet,
) -> tuple[list[tuple[str, str, str]], list[tuple[str, str]]]:
    resolved: list[tuple[str, str, str]] = []
    missing: list[tuple[str, str]] = []
    for name, version in sorted(yarn_only):
        candidates = yarn_aliases.get(name) or pnpm_aliases.get(name) or set()
        if not candidates:
            missing.append((name, version))
            continue
        for real_name, real_version in sorted(candidates):
            if (real_name, real_version) in pnpm_set:
                resolved.append((name, version, f"ALIAS_TO {real_name}@{real_version}"))
                break
        else:
            note = " ALIAS_DECLARED_BUT_REAL_MISSING " + ",".join(
                f"{real_name}@{real_version}" for real_name, real_version in sorted(candidates)
            )
            missing.append((name, version + note))
    return resolved, missing


def diff_stats(
    left: PackageSet,
    right: PackageSet,
    yarn_aliases: AliasMap | None = None,
    pnpm_aliases: AliasMap | None = None,
) -> dict[str, int]:
    left_only = left - right
    right_only = right - left
    resolved: list[tuple[str, str, str]] = []
    missing = sorted(left_only)
    if yarn_aliases is not None and pnpm_aliases is not None:
        resolved, missing = resolve_aliases(left_only, yarn_aliases, pnpm_aliases, right)
    return {
        "left_unique": len(left),
        "right_unique": len(right),
        "both": len(left & right),
        "left_only": len(left_only),
        "right_only": len(right_only),
        "alias_covered": len(resolved),
        "true_left_drift": len(missing),
    }


def print_diff(
    left_label: str,
    left: PackageSet,
    right_label: str,
    right: PackageSet,
    yarn_aliases: AliasMap | None = None,
    pnpm_aliases: AliasMap | None = None,
) -> int:
    left_only = left - right
    right_only = right - left
    both = left & right
    left_names = {name for name, _version in left}
    right_names = {name for name, _version in right}

    print("# Summary")
    print(f"{left_label} unique (name, version): {len(left)}")
    print(f"{right_label} unique (name, version): {len(right)}")
    print(f"{left_label} unique names          : {len(left_names)}")
    print(f"{right_label} unique names          : {len(right_names)}")
    print(f"both                              : {len(both)}")
    print(f"{left_label}_only                       : {len(left_only)}")
    print(f"{right_label}_only                       : {len(right_only)}")
    print()

    resolved: list[tuple[str, str, str]] = []
    missing = sorted(left_only)
    if yarn_aliases is not None and pnpm_aliases is not None:
        resolved, missing = resolve_aliases(left_only, yarn_aliases, pnpm_aliases, right)
        print("## left_only resolved through npm alias")
        if resolved:
            for name, version, note in resolved:
                print(f"{name} : {left_label}={version}  {note}")
        else:
            print("(none)")
        print()

    versions_by_name: dict[str, list[str]] = defaultdict(list)
    for name, version in right:
        versions_by_name[name].append(version)
    left_versions_by_name: dict[str, list[str]] = defaultdict(list)
    for name, version in left:
        left_versions_by_name[name].append(version)

    print("## left_only not covered")
    if missing:
        for name, version in missing:
            left_versions = "/".join(sorted(left_versions_by_name.get(name, [])))
            right_versions_list = sorted(versions_by_name.get(name, []))
            if right_versions_list:
                right_versions = "/".join(right_versions_list)
                missing_major = semver_major(version)
                right_majors = {semver_major(right_version) for right_version in right_versions_list}
                if missing_major is not None and missing_major not in right_majors:
                    status = "MAJOR_COLLAPSED"
                    risk = "CHECK_REQUIRED"
                    note = "same package remains, but this major line is no longer present on the right side"
                else:
                    status = "VERSION_SET_CHANGED"
                    risk = "REVIEW"
                    note = "same package remains with a different version set"
            else:
                right_versions = "NOT_PRESENT"
                status = "MISSING_NAME"
                risk = "CHECK_REQUIRED"
                note = "package name is not present on the right side"
            print(
                f"{name} : status={status}  missing_{left_label}_version={version}  "
                f"all_{left_label}_versions={left_versions}  all_{right_label}_versions={right_versions}  "
                f"risk={risk}  note={note}"
            )
    else:
        print("(none)")
    print()

    print("## right_only name-level sample")
    name_only = sorted(right_names - left_names)
    if name_only:
        for name in name_only[:20]:
            print(name)
        if len(name_only) > 20:
            print(f"... and {len(name_only) - 20} more")
    else:
        print("(none)")
    return 0 if not missing else 1


def command_lock(args: argparse.Namespace) -> int:
    yarn_set, yarn_aliases = parse_yarn_lock(Path(args.yarn_lock))
    pnpm_set, pnpm_aliases = parse_pnpm_lock(Path(args.pnpm_lock))
    return print_diff("yarn", yarn_set, "pnpm", pnpm_set, yarn_aliases, pnpm_aliases)


def command_node_modules(args: argparse.Namespace) -> int:
    yarn_set = package_json_set_from_node_modules(Path(args.yarn_node_modules))
    pnpm_set = package_json_set_from_node_modules(Path(args.pnpm_node_modules))
    return print_diff("yarn_nm", yarn_set, "pnpm_nm", pnpm_set)


def command_list_json(args: argparse.Namespace) -> int:
    yarn_set = yarn_list_set(Path(args.yarn_list_json))
    pnpm_set = pnpm_list_set(Path(args.pnpm_list_json))
    return print_diff("yarn_list", yarn_set, "pnpm_list", pnpm_set)


def command_all_locks(args: argparse.Namespace) -> int:
    yarn_root = Path(args.yarn_root)
    pnpm_root = Path(args.pnpm_root)
    rows: list[tuple[str, dict[str, int]]] = []

    for label, subdir in PROJECTS:
        yarn_set, yarn_aliases = parse_yarn_lock(yarn_root / subdir / "yarn.lock")
        pnpm_set, pnpm_aliases = parse_pnpm_lock(pnpm_root / subdir / "pnpm-lock.yaml")
        rows.append((label, diff_stats(yarn_set, pnpm_set, yarn_aliases, pnpm_aliases)))

    print("| Subdir | yarn unique | pnpm unique | both | yarn_only | pnpm_only | alias covered | true yarn drift |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    for label, stats in rows:
        print(
            f"| `{label}/` | {stats['left_unique']} | {stats['right_unique']} | "
            f"{stats['both']} | {stats['left_only']} | {stats['right_only']} | "
            f"{stats['alias_covered']} | {stats['true_left_drift']} |"
        )
    return 1 if args.fail_on_drift and any(stats["true_left_drift"] for _label, stats in rows) else 0


def command_all_node_modules(args: argparse.Namespace) -> int:
    yarn_root = Path(args.yarn_root)
    pnpm_root = Path(args.pnpm_root)
    rows: list[tuple[str, dict[str, int]]] = []

    for label, subdir in PROJECTS:
        yarn_set = package_json_set_from_node_modules(yarn_root / subdir / "node_modules")
        pnpm_set = package_json_set_from_node_modules(pnpm_root / subdir / "node_modules")
        rows.append((label, diff_stats(yarn_set, pnpm_set)))

    print("| Subdir | yarn node_modules unique | pnpm node_modules unique | both | yarn_nm_only | pnpm_nm_only |")
    print("|---|---:|---:|---:|---:|---:|")
    for label, stats in rows:
        print(
            f"| `{label}/` | {stats['left_unique']} | {stats['right_unique']} | "
            f"{stats['both']} | {stats['left_only']} | {stats['right_only']} |"
        )
    return 1 if args.fail_on_drift and any(stats["true_left_drift"] for _label, stats in rows) else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(required=True)

    lock_parser = subparsers.add_parser("lock")
    lock_parser.add_argument("yarn_lock")
    lock_parser.add_argument("pnpm_lock")
    lock_parser.set_defaults(func=command_lock)

    node_modules_parser = subparsers.add_parser("node-modules")
    node_modules_parser.add_argument("yarn_node_modules")
    node_modules_parser.add_argument("pnpm_node_modules")
    node_modules_parser.set_defaults(func=command_node_modules)

    list_parser = subparsers.add_parser("list-json")
    list_parser.add_argument("yarn_list_json")
    list_parser.add_argument("pnpm_list_json")
    list_parser.set_defaults(func=command_list_json)

    all_locks_parser = subparsers.add_parser("all-locks")
    all_locks_parser.add_argument("--yarn-root", default="/private/tmp/yarn-modules")
    all_locks_parser.add_argument("--pnpm-root", default=".")
    all_locks_parser.add_argument("--fail-on-drift", action="store_true")
    all_locks_parser.set_defaults(func=command_all_locks)

    all_node_modules_parser = subparsers.add_parser("all-node-modules")
    all_node_modules_parser.add_argument("--yarn-root", default="/private/tmp/yarn-modules")
    all_node_modules_parser.add_argument("--pnpm-root", default=".")
    all_node_modules_parser.add_argument("--fail-on-drift", action="store_true")
    all_node_modules_parser.set_defaults(func=command_all_node_modules)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
