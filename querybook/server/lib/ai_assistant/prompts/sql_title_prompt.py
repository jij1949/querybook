from langchain.prompts import PromptTemplate


prompt_template = """
You are a senior business analyst who is an expert with SQL queries.

Generate a clear and accurate title for the SQL query below. Try to infer the purpose of the query rather than a literal explanation of the SQL.
Keep it concise and informative, and fewer than 10 words.

===Query
{query}

===Response Format
Please respond in below JSON format:
{{
    "title": "This is a title"
}}
"""

SQL_TITLE_PROMPT = PromptTemplate.from_template(prompt_template)
