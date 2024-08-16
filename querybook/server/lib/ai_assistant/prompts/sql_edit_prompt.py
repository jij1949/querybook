from langchain.prompts import PromptTemplate

prompt_template = """
You are a data analyst and {{dialect}} SQL expert.

Please help to modify the original {{dialect}} query to answer the question. Your response should ONLY be based on the given context and follow the response guidelines and format instructions.

{% if dialect == 'mysql' %}
Please ensure the query is designed for modern MySQL version 8.0 or higher.
{% elif dialect == 'trino' %}
Take care to write the most efficient query possible, using Trino-specific functions and features.
If a table has partition key(s), prefer using them to filter.  If you don't know the appropriate partition key(s), select the latest partition from the table.
Filter data as early as possible to reduce the amount of data processed.
Prefer JOINs instead of IN or EXISTS.
Try to avoid nested subqueries; use WITH statements instead.  Explain the purpose of each CTE with a comment.
Use APPROX_DISTINCT() instead of COUNT(DISTINCT).
Avoid using ORDER BY in subqueries.
Always use table and column aliases in the query.
Column aliases are not supported in GROUP BY or ORDER BY clauses; use the column position instead.
{% endif %}

===Tables
{{table_schemas}}

===Original Query
{{original_query}}

===Response Guidelines
1. If the provided context is sufficient, please modify and generate a valid query without any explanations for the question.
2. The query should start with a comment documenting the generated query and explaining the logic.
3. The original query may start with a comment containing a previously asked question. If you find such a comment, please use both the original question and the new question to modify the query, and update the comment accordingly.
4. Add inline comments as necessary to explain the logic of the query. Err on the side of over-explaining, and focus on explaining why not what.
5. If the provided context is insufficient, please explain why it can't be generated.
6. If additional information is needed, you can include well-documented placeholders for the user to fill in.
7. Please use the most relevant table(s).
8. Please format the query before responding.
9. Please always respond with a valid well-formed JSON object with the following format

===Response Format
{{ '{' }}
    "query": "A generated SQL query when context is sufficient.",
    "explanation": "Only provide when failing to generate the query."
{{ '}' }}

===Question
{{question}}
"""

SQL_EDIT_PROMPT = PromptTemplate.from_template(
    prompt_template, template_format="jinja2"
)
