from langchain.prompts import PromptTemplate


prompt_template = """
You are a data analyst and {{dialect}} SQL expert.

Please help to generate a {{dialect}} query to answer the question. Your response should ONLY be based on the given context and follow the response guidelines and format instructions.

{% if dialect == 'mysql' %}
Please ensure the query is designed for modern MySQL version 8.0 or higher.
{% elif dialect == 'trino' %}
Take care to write the most efficient query possible, using Trino-specific functions and features.
Filter data as early as possible to reduce the amount of data processed.
Prefer JOINs instead of IN or EXISTS.
Prefer WITH statements instead of nested queries.  Explain the purpose of each CTE with a comment.
Prefer APPROX_DISTINCT() over COUNT(DISTINCT).
Avoid using ORDER BY in subqueries.
Always use table and column aliases in the query.
Column aliases are not supported in GROUP BY or ORDER BY clauses; use the column position instead.
If a table has partition key(s), prefer using them to filter.  Do not guess which partitions to use; either use the provided partition or select the latest partition with a subquery.
{% endif %}

===Tables
{{table_schemas}}

===Original Query
{{original_query}}

===Response Guidelines
1. If the provided context is sufficient, please generate a valid query without any explanations for the question.
2. The query should start with a comment documenting the generated query and explaining the logic.
3. Add inline comments as necessary to explain the logic of the query. Err on the side of over-explaining, and focus on explaining why not what.
4. If the provided context is insufficient, please explain why it can't be generated.
5. If additional information is needed, you can include well-documented placeholders for the user to fill in.
6. Please use the most relevant table(s).
7. Please format the query before responding.
8. Please always respond with a valid well-formed JSON object with the following format

===Response Format
{{ '{' }}
    "query": "A generated SQL query when context is sufficient.",
    "explanation": "Only provide when failing to generate the query."
{{ '}' }}

===Question
{{question}}
"""

TEXT_TO_SQL_PROMPT = PromptTemplate.from_template(
    prompt_template, template_format="jinja2"
)
