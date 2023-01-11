import re

DATE_TIMESTAMP_REGEX = r"(([\w ()]+)|(\s*\'[\w\s\-\:]*\'\s*))"

TRUNC_REGEX = r"trunc\((([\w ()]+)|(\s*\'[\w\s\-\:]*\'\s*)),\s*'(MONTH|MON|MM|YEAR|YYYY|YY)\'\s*\)"
MONTHS_BETWEEN_REGEX = r"months_between\((([\w ()]+)|(\s*\'[\w\s\-\:]*\'\s*)),(([\w ()]+)|(\s*\'[\w\s\-\:]*\'\s*))\)"
DATE_DIFF_REGEX = r"datediff\((([\w ()]+)|(\s*\'[\w\s\-\:]*\'\s*)),(([\w ()]+)|(\s*\'[\w\s\-\:]*\'\s*))\)"
# DATE_DIFF_REGEX = r"datediff\(((\s*\S+\s*)|(\'[\w\s\-\:]*\')),((\s*\S+\s*)|(\'[\w\s\-\:]*\'))\)"
EXTRACT_REGEX = (
    r"extract\(\s*(day|dayofweek|hour|minute|month|quarter|second|week|year)\s* from (([\w ()]+)|(\s*\'["
    r"\w\s\-\:]*\'\s*))\) "
)
DATE_SUB_REGEX = r"date_sub\((([\w ()]+)|(\s*\'[\w\s\-\:]*\'\s*)),\s*(\d{2})\s*\)"
DATE_ADD_REGEX = r"date_add\((([\w ()]+)|(\s*\'[\w\s\-\:]*\'\s*)),\s*(\d{2})\s*\)"
ADD_MONTHS_REGEX = r"add_months\((([\w ()]+)|(\s*\'[\w\s\-\:]*\'\s*)),\s*(\d+)\s*\)"
ADD_MONTHS_REGEX_WITH_FORMAT = r"add_months\((([\w ()]+)|(\s*\'[\w\s\-\:]*\'\s*)),\s*(\d+)\s*,(([\w ()]+)|(\s*\'[\w\s\-\:]*\'\s*))*\)"
TO_DATE_REGEX = r"to_date\((([\w ()]+)|(\s*\'[\w\s\-\:]*\'\s*))\)"
LAST_DAY_REGEX = r"last_day\((([\w ()]+)|(\s*\'[\w\s\-\:]*\'\s*))\)"
DAY_OF_MONTH_REGEX = r"dayofmonth\((([\w ()]+)|(\s*\'[\w\s\-\:]*\'\s*))\)"
WEEK_OF_YEAR_REGEX = r"weekofyear\((([\w ()]+)|(\s*\'[\w\s\-\:]*\'\s*))\)"
CURRENT_DATE_REGEX = r"current_date\(\)"
CURRENT_TIMESTAMP_REGEX = r"current_timestamp\(\)"
CAST_REGEX = r"\b(cast|CAST)\b\((\S+)\s*(AS|as)\s+(date|DATE|timestamp|TIMESTAMP)\)"

TRINO_TIMESTAMP_FORMAT = "%Y-%c-%d %H:%i:%s"
TRINO_DATE_FORMAT = "%Y-%c-%d"

ROW_FORMAT_JSON_REGEX = "(ROW\s+FORMAT\s+SERDE\s+'org.openx.data.jsonserde.JsonSerDe')\n*\s*LOCATION\s+(['\w\:\/\-]*)"
CREATE_EXTERNAL_TABLE_REGEX = "\s+CREATE\s+EXTERNAL\s+TABLE"
CREATE_TABLE = "CREATE TABLE"
STRING = "string"
VARCHAR = "varchar"
