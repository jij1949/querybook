import re
from typing import List

import query_transpilation_plugin.eg_custom.constants.DateTimeRegexConstants as dc


sourceQuery = (
    "select trunc(cast(process_date  as date),'YY') as truncated_process_date from table1 where trunc("
    "'2020-05-03','YY') = '2020-05-01' "
)
truncParamDict = {
    "MM": "month",
    "MON": "month",
    "MONTH": "month",
    "YY": "year",
    "YYYY": "year",
    "YEAR": "year",
}

timestampRegex = r"[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1]) (2[0-3]|[01][0-9]):[0-5][0-9]:[0-5][0-9]:[0-9][0-9][0-9]"


def _converttrunc(queryStr):
    try:
        list = re.findall(dc.TRUNC_REGEX, queryStr, flags=re.IGNORECASE)
        for x in list:
            result = re.search(dc.TRUNC_REGEX, queryStr, flags=re.IGNORECASE)

            new_String = re.sub(
                dc.TRUNC_REGEX,
                "date_trunc('"
                + truncParamDict.get(result.group(4))
                + "',"
                + result.group(1)
                + ")",
                queryStr,
                1,
                flags=re.IGNORECASE,
            )
            queryStr = new_String
    except:
        queryStr = "Error while converting trunc function"
    return queryStr


# _converttrunc(sourceQuery)

sourceQuery = (
    "select * from table1 where months_between(date1,date2) > 3 and months_between(a,b) > 10"
    "and months_between(c,d) > 15"
)


def _convertmonthsbetween(queryStr):
    try:
        list = re.findall(dc.MONTHS_BETWEEN_REGEX, queryStr, flags=re.IGNORECASE)
        for x in list:
            result = re.search(dc.MONTHS_BETWEEN_REGEX, queryStr, flags=re.IGNORECASE)

            new_string = re.sub(
                dc.MONTHS_BETWEEN_REGEX,
                "date_diff('month'," + result.group(4) + "," + result.group(1) + ")",
                queryStr,
                1,
                flags=re.IGNORECASE,
            )
            queryStr = new_string
    except:
        queryStr = "Error while converting months_between"
    return queryStr


sourceQuery = "select * from table1 where extract(month from '2020-02-09') = 11"
extractParamDict = {
    "day": "DAY",
    "dayofweek": "DAY_OF_WEEK",
    "hour": "HOUR",
    "minute": "MINUTE",
    "month": "MONTH",
    "quarter": "QUARTER",
    "second": "SECOND",
    "week": "WEEK",
    "year": "YEAR",
}


def _convertextract(queryStr):
    try:
        list = re.findall(dc.EXTRACT_REGEX, queryStr, flags=re.IGNORECASE)

        for x in list:
            # two groups enclosed in separate ( and ) bracket
            result = re.search(dc.EXTRACT_REGEX, queryStr, flags=re.IGNORECASE)

            new_String = re.sub(
                dc.EXTRACT_REGEX,
                "extract("
                + extractParamDict.get(result.group(1))
                + " from "
                + result.group(2)
                + ")",
                queryStr,
                1,
                flags=re.IGNORECASE,
            )
            queryStr = new_String
    except:
        queryStr = "Error while converting extract"
    return queryStr


# _convertextract(sourceQuery)

sourceQuery = (
    "select * from table1 where date_sub(to_date(localstartdt),15) > to_date(localenddt) and "
    "date_sub(to_date(gloabalstart1),15) > to_date(globalend1)"
)


def _convertdatesub(queryStr):
    try:
        list = re.findall(dc.DATE_SUB_REGEX, queryStr, flags=re.IGNORECASE)
        for x in list:
            result = re.search(dc.DATE_SUB_REGEX, queryStr, flags=re.IGNORECASE)

            new_String = re.sub(
                dc.DATE_SUB_REGEX,
                "date_add('day',-" + result.group(4) + "," + result.group(1) + ")",
                queryStr,
                1,
                flags=re.IGNORECASE,
            )
            queryStr = new_String
    except:
        queryStr = "Error while converting date_sub"
    return queryStr


sourceQuery = (
    "select * from table1 where datediff( to_date(date1),to_date(date2) ) > 3 and datediff(cast(date3  as timestamp) "
    ", '2020-11-22 22:22:22:222' ) >  5 "
)


def _convertdatediff(queryStr):
    try:
        list = re.findall(dc.DATE_DIFF_REGEX, queryStr, flags=re.IGNORECASE)
        for x in list:
            result = re.search(dc.DATE_DIFF_REGEX, queryStr, flags=re.IGNORECASE)

            new_string = re.sub(
                dc.DATE_DIFF_REGEX,
                "date_diff('day'," + result.group(4) + "," + result.group(1) + ")",
                queryStr,
                1,
                flags=re.IGNORECASE,
            )
            queryStr = new_string
    except:
        queryStr = "Error while converting datediff"
    return queryStr


# _convertdatediff(sourceQuery)

sourceQuery = "select * from table1 where date_add(to_date(localstartdt),15) > to_date(localenddt)"


def _convertdateadd(queryStr):
    try:
        list = re.findall(dc.DATE_ADD_REGEX, queryStr, flags=re.IGNORECASE)

        for x in list:
            result = re.search(dc.DATE_ADD_REGEX, queryStr, flags=re.IGNORECASE)

            new_String = re.sub(
                dc.DATE_ADD_REGEX,
                "date_add('day'," + result.group(4) + "," + result.group(1) + ")",
                queryStr,
                1,
                flags=re.IGNORECASE,
            )
            queryStr = new_String
    except:
        queryStr = "Error while converting date_add"
    return queryStr


sourceQuery = "select * from table1 where add_months('2022-01-23 11:11:11',2) > to_date(localenddt)"


def _convertaddmonths(queryStr):
    try:
        list = re.findall(dc.ADD_MONTHS_REGEX, queryStr, flags=re.IGNORECASE)

        for x in list:
            # two groups enclosed in separate ( and ) bracket
            result = re.search(dc.ADD_MONTHS_REGEX, queryStr, flags=re.IGNORECASE)

            new_String = re.sub(
                dc.ADD_MONTHS_REGEX,
                "date_add('month'," + result.group(4) + "," + result.group(1) + ")",
                queryStr,
                1,
                flags=re.IGNORECASE,
            )
            queryStr = new_String
    except:
        queryStr = "Error while converting add_months"
    return queryStr


def _adddateparsefunction(result, groupnum):
    dateparsestr = result.group(groupnum - 2)
    if (
        (result is not None)
        and (result.group(groupnum) is not None)
        and (len(result.group(groupnum)) > 12)
    ):
        dateparsestr = (
            "date_parse("
            + result.group(groupnum)
            + ",'"
            + dc.TRINO_TIMESTAMP_FORMAT
            + "')"
        )
    elif (
        (result is not None)
        and (result.group(groupnum) is not None)
        and (len(result.group(groupnum)) <= 12)
    ):
        dateparsestr = (
            "date_parse(" + result.group(groupnum) + ",'" + dc.TRINO_DATE_FORMAT + "')"
        )
    return dateparsestr


# _convertaddmonths(sourceQuery)

sourceQuery = "select add_months('2017-12-31 14:15:16', 2, 'YYYY-MM-dd HH:mm:ss')"


def _convertaddmonthswithformat(queryStr):
    try:
        list = re.findall(
            dc.ADD_MONTHS_REGEX_WITH_FORMAT, queryStr, flags=re.IGNORECASE
        )

        for x in list:
            # two groups enclosed in separate ( and ) bracket
            result = re.search(
                dc.ADD_MONTHS_REGEX_WITH_FORMAT, queryStr, flags=re.IGNORECASE
            )

            new_String = re.sub(
                dc.ADD_MONTHS_REGEX_WITH_FORMAT,
                "date_add('month',"
                + result.group(4)
                + ","
                + _adddateparsefunction(result, 3)
                + ")",
                queryStr,
                1,
                flags=re.IGNORECASE,
            )
            queryStr = new_String
    except:
        queryStr = "Error while converting add_months with format"
    return queryStr


# _convertaddmonthswithformat(sourceQuery)

sourceQuery = "select * from table1 where to_date(localstartdt) > to_date(localenddt)"


def _converttodate(queryStr):
    try:
        list = re.findall(dc.TO_DATE_REGEX, queryStr, flags=re.IGNORECASE)

        for x in list:
            result = re.search(dc.TO_DATE_REGEX, queryStr, flags=re.IGNORECASE)

            new_String = re.sub(
                dc.TO_DATE_REGEX,
                "date(" + result.group(1) + ")",
                queryStr,
                1,
                flags=re.IGNORECASE,
            )
            queryStr = new_String
    except:
        queryStr = "Error while converting to_date"
    return queryStr


# _converttodate(sourceQuery)

sourceQuery = "select * from table1 where last_day(localstartdt) > to_date(localenddt)"


def _convertlastday(queryStr):
    try:
        list = re.findall(dc.LAST_DAY_REGEX, queryStr, flags=re.IGNORECASE)

        for x in list:
            result = re.search(dc.LAST_DAY_REGEX, queryStr, flags=re.IGNORECASE)

            new_String = re.sub(
                dc.LAST_DAY_REGEX,
                "last_day_of_month(" + result.group(1) + ")",
                queryStr,
                1,
                flags=re.IGNORECASE,
            )
            queryStr = new_String
    except:
        queryStr = "Error while converting lastday"
    return queryStr


# _convertlastday(sourceQuery)

sourceQuery = (
    "select * from table1 where dayofmonth(localstartdt) > to_date(localenddt)"
)


def _convertdayofmonth(queryStr):
    try:
        list = re.findall(dc.DAY_OF_MONTH_REGEX, queryStr, flags=re.IGNORECASE)

        for x in list:
            result = re.search(dc.DAY_OF_MONTH_REGEX, queryStr, flags=re.IGNORECASE)

            new_String = re.sub(
                dc.DAY_OF_MONTH_REGEX,
                "day_of_month(" + result.group(1) + ")",
                queryStr,
                1,
                flags=re.IGNORECASE,
            )
            queryStr = new_String
    except:
        queryStr = "Error while converting dayofmonth"
    return queryStr


# _convertdayofmonth(sourceQuery)

sourceQuery = "select * from table1 where weekofyear(localstartdt) > 50"


def _convertweekofyear(queryStr):
    try:
        list = re.findall(dc.WEEK_OF_YEAR_REGEX, queryStr, flags=re.IGNORECASE)

        for x in list:
            result = re.search(dc.WEEK_OF_YEAR_REGEX, queryStr, flags=re.IGNORECASE)

            new_String = re.sub(
                dc.WEEK_OF_YEAR_REGEX,
                "week_of_year(" + result.group(1) + ")",
                queryStr,
                1,
                flags=re.IGNORECASE,
            )
            queryStr = new_String
    except:
        queryStr = "Error while converting weekofyear"
    return queryStr


# _convertdayofmonth(sourceQuery)

sourceQuery = "select * from table1 where current_date() > 50"


def _convertcurrentdate(queryStr):
    try:
        list = re.findall(dc.CURRENT_DATE_REGEX, queryStr, flags=re.IGNORECASE)

        for x in list:
            new_String = re.sub(
                dc.CURRENT_DATE_REGEX, "current_date", queryStr, 1, flags=re.IGNORECASE
            )
            queryStr = new_String
    except:
        queryStr = "Error while converting current_date"
    return queryStr


# _convertcurrentdate(sourceQuery)

sourceQuery = "select * from table1 where current_timestamp() > 50"


def _convertcurrenttimestamp(queryStr):
    try:
        list = re.findall(dc.CURRENT_TIMESTAMP_REGEX, queryStr, flags=re.IGNORECASE)

        for x in list:
            new_String = re.sub(
                dc.CURRENT_TIMESTAMP_REGEX,
                "current_timestamp",
                queryStr,
                1,
                flags=re.IGNORECASE,
            )
            queryStr = new_String
    except:
        queryStr = "Error while converting current_timestamp"
    return queryStr


# _convertcurrenttimestamp(sourceQuery)

sourceQuery = "select cast(date1 as date), cast(date2 as timestamp), cast(abc  as DATE), CAST(abc2 AS TIMESTAMP) from table1 where current_timestamp() > 50"


def _convertcastdatetime(queryStr):
    try:
        list = re.findall(dc.CAST_REGEX, queryStr, flags=re.IGNORECASE)

        for x in list:
            result = re.search(dc.CAST_REGEX, queryStr, flags=re.IGNORECASE)
            new_String = re.sub(
                dc.CAST_REGEX,
                "try_cast(" + result.group(2) + " as " + result.group(4) + ")",
                queryStr,
                1,
                flags=re.IGNORECASE,
            )
            queryStr = new_String
    except:
        queryStr = "Error while converting castdatetime"

    return queryStr


# _convertcastdatetime(sourceQuery)


def checkexternaltableandreturn(queryStr):
    try:
        if re.search(dc.CREATE_EXTERNAL_TABLE_REGEX, queryStr, flags=re.IGNORECASE) is not None:
            return "external_location"
        else:
            return "location"
    except:
        queryStr = "Error while converting checkexternaltableandreturn"



def _convertrowformatpjsonroperties(queryStr):
    try:

        list = re.findall(dc.ROW_FORMAT_JSON_REGEX, queryStr, flags=re.IGNORECASE)
        location_str = checkexternaltableandreturn(queryStr)
        for x in list:
            result = re.search(dc.ROW_FORMAT_JSON_REGEX, queryStr, flags=re.IGNORECASE)
            new_String = re.sub(dc.ROW_FORMAT_JSON_REGEX,
                                "\nWITH\n( " + location_str + " = " + result.group(2) + ", \nformat ='JSON'\n)", queryStr,
                                1,
                                flags=re.IGNORECASE)
            queryStr = new_String
    except:
        queryStr = "Error while converting convertrowformatproperties"

    return queryStr


def _convertexternaltable(queryStr):
    try:
        list = re.findall(dc.CREATE_EXTERNAL_TABLE_REGEX, queryStr, flags=re.IGNORECASE)
        location_str = checkexternaltableandreturn(queryStr)
        for x in list:
            result = re.search(dc.CREATE_EXTERNAL_TABLE_REGEX, queryStr, flags=re.IGNORECASE)
            new_String = re.sub(dc.CREATE_EXTERNAL_TABLE_REGEX,
                                dc.CREATE_TABLE, queryStr,
                                1,
                                flags=re.IGNORECASE)
            queryStr = new_String
    except:
        queryStr = "Error while converting convertrowformatproperties"

    return queryStr


def _convertstring(queryStr):
    try:
        queryStr = re.sub(dc.STRING, dc.VARCHAR, queryStr, flags=re.IGNORECASE)
    except:
        queryStr = "Error while converting string type"

    return queryStr


def apply(f, value):
    return f(value)


def statements_to_query(statements: List[str]):
    return "\n".join(statement + ";" for statement in statements)


def _customtranspilehive(statements: List[str], rawSQLList: List[str]):
    transpiledListwithRowFormatProperties = []
    for index, statement in enumerate(statements):
        if rawSQLList is not None and rawSQLList[index] is not None and re.search(dc.CREATE_EXTERNAL_TABLE_REGEX, statement, flags=re.IGNORECASE) and re.search(dc.CREATE_EXTERNAL_TABLE_REGEX, rawSQLList[index], flags=re.IGNORECASE)  \
                    and re.search(dc.ROW_FORMAT_JSON_REGEX, rawSQLList[index], flags=re.IGNORECASE):
            rowformatproperties = _getrowformatsubstring(rawSQLList[index])
            transpiledListwithRowFormatProperties.append(_executecalls(statement + rowformatproperties))
            # if "..."
        else:
            transpiledListwithRowFormatProperties.append(_executecalls(statement))
    return transpiledListwithRowFormatProperties

def _customtranspilepresto(rawSQLList: List[str]):
    transpiledListwithRowFormatProperties = []
    for index, statement in enumerate(rawSQLList):
        transpiledListwithRowFormatProperties.append(_executecalls(statement))
    return transpiledListwithRowFormatProperties

def _splitqueries(sQueryStr):
    sqlsplitlist : list[str] = []
    for sql in str(sQueryStr).split(";"):
        if(sql and sql.strip()):
            sqlsplitlist.append(sql)
    return sqlsplitlist

def _executecalls(queryStr):
    for f in function_list:
        value = apply(f, queryStr)
        queryStr = value
    return queryStr


def _getrowformatsubstring(queryStr):
    resultantsql = queryStr
    if re.search(dc.ROW_FORMAT_JSON_REGEX, queryStr, flags=re.IGNORECASE) is not None:
        result = re.search(dc.ROW_FORMAT_JSON_REGEX, queryStr, flags=re.IGNORECASE)
        resultantsql = queryStr[int(result.span()[0]):int(result.span()[1])]
    else:
        resultantsql = None
    return resultantsql

function_list = [
    _convertdatediff,
    _convertdatesub,
    _convertmonthsbetween,
    _convertdateadd,
    _convertaddmonths,
    _convertcurrentdate,
    _convertcurrenttimestamp,
    _convertdayofmonth,
    _convertextract,
    _convertlastday,
    _converttodate,
    _converttrunc,
    _convertweekofyear,
    _convertcastdatetime,
    _convertaddmonthswithformat,
    _convertrowformatpjsonroperties,
    _convertexternaltable,
    _convertstring,
]
