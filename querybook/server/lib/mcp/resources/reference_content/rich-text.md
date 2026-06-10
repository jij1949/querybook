# Querybook Rich Text Cells

Text cells store rich text as HTML fragments, not Markdown. When creating or
updating a text cell, pass the HTML fragment in the `context` parameter.

## Supported Elements

-   Paragraphs: `<p>Text content</p>`
-   Headers: `<h1>`, `<h2>`, `<h3>`, etc.
-   Bold: `<strong>Bold text</strong>`
-   Italic: `<em>Italic text</em>`
-   Strikethrough: `<del>Strikethrough text</del>`
-   Underline: `<u>Underlined text</u>`
-   Unordered lists: `<ul><li>Item 1</li><li>Item 2</li></ul>`
-   Ordered lists: `<ol><li>First</li><li>Second</li></ol>`
-   Block quotes: `<blockquote>Quoted text</blockquote>`
-   Links: `<a href="https://example.com">Link text</a>`
-   Blank lines: `<p><br></p>`
-   Non-breaking space: `&nbsp;`

## Simple Example

```python
add_datadoc_cell(
    datadoc_id=123,
    cell_type="text",
    context="<p>This is a simple paragraph.</p>",
)
```

## Rich Example

```python
add_datadoc_cell(
    datadoc_id=123,
    cell_type="text",
    context=(
        "<h1>Analysis Overview</h1>"
        "<p><br></p>"
        "<p>This analysis covers <strong>three key areas</strong>:</p>"
        "<ul>"
        "<li>Revenue trends</li>"
        "<li>User engagement</li>"
        "<li>Performance metrics</li>"
        "</ul>"
        "<p>See the <a href=\"https://example.com/docs\">documentation</a>.</p>"
    ),
)
```

## Best Practices

-   Use semantic HTML such as `<strong>` and `<em>`.
-   Use headers to create a clear document hierarchy.
-   Use `<p><br></p>` for blank lines between sections.
-   Use `<ul>` and `<ol>` to make findings scannable.
-   Use links for related DataDocs, dashboards, tickets, and docs.
-   Do not include `<html>`, `<head>`, or `<body>` tags.
-   Avoid custom CSS classes and inline styles; the editor may not preserve them.
