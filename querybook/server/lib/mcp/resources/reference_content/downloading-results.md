# Downloading Query Results

Query execution results expose two result access paths:

-   `results_resource_uri`: MCP resource with JSON rows, best for small previews.
-   `results_download_url`: HTTP download URL, best for large result sets.

Prefer `results_download_url` when the result set is large, when you need all
rows, or when you plan to analyze the data with tools such as pandas or DuckDB.
This avoids loading large datasets into MCP context.

## Getting a Download URL

Query execution is asynchronous. Tools such as `execute_ad_hoc_query` and
`run_datadoc_cell` return immediately with a `query_execution_resource_uri`.
Poll that resource until the execution status is `DONE`.

Completed statement executions may include:

```json
{
    "id": 1023826,
    "status_name": "DONE",
    "result_row_count": 250000,
    "results_resource_uri": "querybook://statement-execution/1023826/results",
    "results_download_url": "https://.../result.csv?..."
}
```

If `results_download_url` is absent, the result store may not support direct
downloads. Use `results_resource_uri` with a row limit as a fallback.

## Download with curl

```bash
curl --progress-bar "$RESULTS_DOWNLOAD_URL" -o results.csv
head -5 results.csv
wc -l results.csv
```

## Download with Python

```python
import requests

def download_results(results_download_url, output_path):
    response = requests.get(results_download_url, stream=True)
    response.raise_for_status()
    with open(output_path, "wb") as output_file:
        for chunk in response.iter_content(chunk_size=8192):
            output_file.write(chunk)

download_results(stmt["results_download_url"], "results.csv")
```

## Load into pandas

```python
from io import StringIO
import pandas as pd
import requests

response = requests.get(stmt["results_download_url"])
response.raise_for_status()
df = pd.read_csv(StringIO(response.text))
```

## Query with DuckDB

```bash
duckdb -c "SELECT * FROM read_csv_auto('$RESULTS_DOWNLOAD_URL') LIMIT 10;"
```

For repeated analysis, download once and query the local file:

```bash
curl -sS "$RESULTS_DOWNLOAD_URL" -o /tmp/querybook_results.csv
duckdb -c "SELECT * FROM read_csv_auto('/tmp/querybook_results.csv') LIMIT 10;"
```

## Choosing the Right Access Path

| Feature          | `results_resource_uri`    | `results_download_url`        |
| ---------------- | ------------------------- | ----------------------------- |
| Format           | JSON columns/data         | CSV                           |
| Row count        | Limited by resource limit | Full result set               |
| MCP context cost | High for large data       | No large rows in context      |
| Authentication   | MCP handles it            | URL contains temporary access |
| Best for         | Small previews            | Large or offline analysis     |

## Expiration and Fallbacks

Download URLs are temporary. If a URL expires or returns `403`, fetch the query
execution resource again to get a fresh URL, then download immediately.

For file or database result stores, `results_download_url` may point to a
Querybook Flask endpoint instead of a cloud presigned URL. That endpoint may
require normal Querybook authentication. If direct download is unavailable, use
`querybook://statement-execution/{statement_execution_id}/results?limit=...`.
