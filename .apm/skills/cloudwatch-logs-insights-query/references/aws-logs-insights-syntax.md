# CloudWatch Logs Insights QL quick reference

## Core commands
- fields: select or create fields used later in the query.
- filter: keep events that match conditions.
- parse: extract values from a log field into new fields (glob or regex).
- stats: aggregate values; supports grouping and time bins.
- sort: order results (asc/desc).
- limit: cap result count.
- dedup: remove duplicate records by field(s).
- display: show fields (use when you do not need fields to create/modify data).
- pattern: cluster log lines into patterns (not supported in Infrequent Access).
- diff: compare current period vs previous period (not supported in Infrequent Access).
- filterIndex: force use of field indexes (not supported in Infrequent Access).
- unmask: show masked content (not supported in Infrequent Access).
- unnest: flatten list fields to multiple records.
- SOURCE: specify log groups in CLI or programmatic queries only.
- anomaly: detect unusual patterns with ML.

## Query structure rules
- Chain commands with `|`.
- Use `#` for comments.
- Use `as` for aliases in `fields`, `parse`, `sort`, and `stats`.

## Fields with special characters
- If a field name contains non-alphanumeric characters other than `@` or `.`, wrap it in backticks.
  - Example: `foo-bar` -> ``foo-bar``

## filter essentials
- Operators: `=`, `!=`, `<`, `<=`, `>`, `>=`, `and`, `or`, `not`.
- `in` checks set membership (array on the right).
- `like` / `not like` match substrings; can use quoted strings or `/regex/`.
- `=~` matches a regex; put the pattern between `/`.
- `filter field = ...` and `filter field IN [...]` can use field indexes; `like` does not.

## parse essentials
- Supports glob and regex.
- Named capture regex: `parse @message /(?<FieldName>pattern)/`.
- Nested JSON parsing requires regex; glob does not support nested JSON.
- JSON is flattened during ingestion; nested JSON parsing has limits (max 200 fields).

## stats essentials
- Aggregations: `count()`, `count(field)`, `count_distinct(field)`, `avg`, `min`, `max`, `sum`, `pct(field, p)`, `stddev`.
- Non-aggregation helpers: `earliest`, `latest`, `sortsFirst`, `sortsLast`.
- `bin()` groups by time; valid units: ms, s, m, h, d, w, mo, q, y (and plural forms).
- At most two `stats` commands per query.
- If two `stats` are used: `sort`/`limit` must be after the second `stats`.
- After the first `stats`, only fields defined in that `stats` are available.
- `bin()` uses `@timestamp`; if you need `bin()` in the second `stats`, carry a timestamp field from the first.

## Log class constraints
- Standard: all commands supported.
- Infrequent Access: `pattern`, `diff`, `filterIndex`, and `unmask` are not supported.
