---
name: cloudwatch-logs-insights-query
description: Write and validate AWS CloudWatch Logs Insights (Logs Insights QL) queries. Use when asked to turn raw log samples/JSON into working queries, build filters/aggregations/statistics, or troubleshoot query errors. Ensure syntax correctness, field parsing, and log class compatibility.
---

# CloudWatch Logs Insights Query

## Overview
Build correct, runnable Logs Insights QL queries from raw log samples and requirements, with strict validation against AWS syntax rules.

## Workflow
1. Collect inputs.
   - Log sample(s) including `@message`.
   - Log class: Standard or Infrequent Access.
   - Time range and desired output (table, trend, top-N, etc.).
   - Required metrics, group-by keys, and time bin size.
2. Map fields.
   - If fields already exist, use them directly.
   - If fields must be extracted, use `parse` (glob or regex).
   - Wrap fields with special characters in backticks.
3. Build the query skeleton.
   - `fields` (select/compute fields)
   - `parse` (only if needed)
   - `filter` (reduce rows)
   - `stats` (aggregate)
   - `sort` and `limit` (final ordering and size)
4. Validate.
   - Check `stats` limits and ordering rules.
   - Check log class constraints.
   - Ensure field names are valid and referenced after creation.
5. Output the final query and assumptions.

## Validation checklist (never skip)
- Use `|` to chain commands; use `#` for comments.
- Backtick any field name with special characters (except `@` or `.`).
- `parse` uses glob or regex; use regex for nested JSON.
- No more than two `stats` commands; if two, `sort` and `limit` must be after the second `stats`.
- After the first `stats`, only fields from that `stats` exist.
- Avoid `pattern`, `diff`, `filterIndex`, or `unmask` on Infrequent Access logs.

## Output format
- Provide the query in a single fenced code block.
- Follow with "Assumptions / open questions" bullets (log class, field mapping, time bin, etc.).
- If you inferred field names, list the mapping explicitly.

## References
- `references/aws-logs-insights-syntax.md`
- `references/query-patterns.md`
