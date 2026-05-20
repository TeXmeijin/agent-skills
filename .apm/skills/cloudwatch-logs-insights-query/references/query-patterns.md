# Query patterns (adapt with real field names)

## Recent errors with raw messages
```
fields @timestamp, @message, status
| filter status >= 500
| sort @timestamp desc
| limit 100
```

## Top endpoints by error count
```
fields request_uri, status
| filter status >= 500
| stats count(*) as error_count by request_uri
| sort error_count desc
| limit 20
```

## p95 latency by route
```
fields request_uri, latency_ms
| stats pct(latency_ms, 95) as p95_ms, avg(latency_ms) as avg_ms by request_uri
| sort p95_ms desc
| limit 50
```

## Error trend per 5 minutes
```
fields status
| filter status >= 500
| stats count(*) as errors by bin(5m) as t
| sort t asc
```

## Parse with glob
```
fields @message
| parse @message "user=* method=* latency=*" as user, method, latency_ms
| stats avg(latency_ms) as avg_ms by method
| sort avg_ms desc
```

## Parse with regex (named capture)
```
fields @message
| parse @message /status=(?<status>\d{3})/
| filter status >= 500
| stats count(*) as errors
```

## Deduplicate by request ID (keep most recent)
```
fields request_id, @timestamp, @message
| sort @timestamp desc
| dedup request_id
| limit 100
```

## Two stats commands (rollup a time series)
```
fields bytes
| stats sum(bytes) as bytes_5m by bin(5m) as t
| stats max(bytes_5m) as peak_bytes, min(bytes_5m) as min_bytes, avg(bytes_5m) as avg_bytes
```
