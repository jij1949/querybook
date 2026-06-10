# Querybook Chart Cells

Chart cells visualize query results from a query cell or query execution. Create
them with `add_datadoc_cell(cell_type="chart")`. Chart cells usually have an
empty `context` string and store their configuration in `meta`.

## Minimal Chart Cell

```json
{
    "cell_type": "chart",
    "context": "",
    "meta": {
        "data": {
            "source_type": "cell_above",
            "limit": 1000,
            "transformations": {
                "format": {},
                "aggregate": false,
                "switch": false
            }
        },
        "chart": {
            "type": "line",
            "x_axis": {
                "label": "Date",
                "col_idx": 0,
                "scale": "date"
            },
            "y_axis": {
                "label": "Count",
                "scale": "linear",
                "stack": false,
                "series": {
                    "1": { "agg_type": "sum" }
                }
            }
        },
        "title": "Error Trend Over Time",
        "visual": {
            "size": "auto",
            "legend_display": true,
            "legend_position": "top",
            "connect_missing": false
        },
        "collapsed": false
    }
}
```

## `meta.data`

Use `meta.data` to choose where the chart gets rows from and how to transform
those rows before rendering.

| Field                       | Type       | Notes                                                                                 |
| --------------------------- | ---------- | ------------------------------------------------------------------------------------- |
| `source_type`               | string     | `cell_above`, `cell`, or `execution`.                                                 |
| `source_ids`                | array[int] | Required for `cell` and `execution`; contains source cell IDs or query execution IDs. |
| `limit`                     | int        | Maximum source rows to display.                                                       |
| `transformations.format`    | object     | Pivot/aggregation selectors.                                                          |
| `transformations.aggregate` | bool       | Aggregate using `format` and series `agg_type`.                                       |
| `transformations.switch`    | bool       | Transpose rows and columns after aggregation.                                         |

`format` can include:

-   `agg_col`: zero-based column index to aggregate by.
-   `series_col`: zero-based column index used to create separate series.
-   `value_cols`: zero-based column indexes containing values to aggregate.

## `meta.chart`

Use `meta.chart` to choose chart type and axes.

Supported chart types:

-   `line`
-   `bar`
-   `histogram`
-   `area`
-   `pie`
-   `doughnut`
-   `scatter`
-   `bubble`
-   `table`

### Axes

`x_axis` supports:

-   `label`: axis label.
-   `col_idx`: zero-based result column index.
-   `scale`: `time`, `date`, `category`, `linear`, or `logarithmic`.
-   `min` / `max`: numeric axis bounds.
-   `format`: `""`, `"$"`, or `"%"`.
-   `sort`: object with `idx` and `asc`.

`y_axis` supports:

-   `label`: axis label.
-   `scale`: `linear` or `logarithmic`.
-   `min` / `max`: numeric axis bounds.
-   `format`: `""`, `"$"`, or `"%"`.
-   `stack`: boolean.
-   `series`: object keyed by value column index as a string.

Each `series` entry can include:

-   `agg_type`: `avg`, `count`, `min`, `max`, `med`, or `sum`.
-   `color`: zero-based color palette index.
-   `hidden`: boolean.
-   `source`: data source index when multiple sources are configured.

`z_axis` is used by bubble charts and supports `col_idx` for bubble size.

## `meta.visual`

Visual settings are optional.

| Field              | Values                                                        |
| ------------------ | ------------------------------------------------------------- |
| `size`             | `sm`, `md`, `lg`, or `auto`                                   |
| `legend_display`   | boolean                                                       |
| `legend_position`  | `top`, `right`, `bottom`, or `left`                           |
| `connect_missing`  | boolean for line/area gaps                                    |
| `values.source`    | `0` for value, `1` for label                                  |
| `values.display`   | `0` never, `1` always, `2` automatic                          |
| `values.position`  | `center`, `start`, or `end`                                   |
| `values.alignment` | `center`, `start`, `end`, `right`, `left`, `top`, or `bottom` |

## Color Palette

The `series.*.color` field uses this palette and cycles after index 16.

| Index | Name                | Hex       |
| ----- | ------------------- | --------- |
| 0     | blue                | `#35B5BB` |
| 1     | pink                | `#ff3975` |
| 2     | grey                | `#bfbfbf` |
| 3     | gold                | `#ffca00` |
| 4     | picton blue         | `#529dce` |
| 5     | orange              | `#ff9f42` |
| 6     | creamy forest green | `#6ba097` |
| 7     | chartreuse          | `#aee800` |
| 8     | baby pink           | `#ff91c8` |
| 9     | icy blue            | `#85d0ce` |
| 10    | fuscia              | `#eb37ce` |
| 11    | light purple        | `#C792EA` |
| 12    | salmon              | `#ec7f77` |
| 13    | olive               | `#989801` |
| 14    | beige               | `#ecd1af` |
| 15    | choco               | `#b7652b` |
| 16    | darkGrey            | `#6d6d6d` |

## MCP Example

```python
add_datadoc_cell(
    datadoc_id=123,
    cell_type="chart",
    context="",
    meta={
        "data": {
            "source_type": "cell_above",
            "limit": 1000,
            "transformations": {"format": {}, "aggregate": False, "switch": False},
        },
        "chart": {
            "type": "bar",
            "x_axis": {"label": "Category", "col_idx": 0, "scale": "category"},
            "y_axis": {
                "label": "Count",
                "scale": "linear",
                "series": {"1": {"agg_type": "sum"}},
            },
        },
        "title": "Count by Category",
        "visual": {"legend_display": True, "legend_position": "top"},
        "collapsed": False,
    },
)
```

## Chart-Specific Notes

-   `cell_above` is simplest when the chart immediately follows its query cell.
-   Use `source_type: "cell"` with `source_ids` when referencing non-adjacent query cells.
-   Use `source_type: "execution"` with `source_ids` for a query execution source.
-   `col_idx` values are zero-based.
-   Pie and doughnut charts still require `x_axis.col_idx` and `y_axis.series: {}`.
-   Bubble charts require `z_axis.col_idx`; the UI may default to column 2.
-   Histogram charts invert the axes and render as horizontal bars.
-   Area charts default to stacked behavior.
-   If no explicit sort is configured, date, datetime, and number x-axis columns are sorted ascending.
