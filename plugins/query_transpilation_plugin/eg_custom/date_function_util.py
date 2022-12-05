import re
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
        list = re.findall(dc.TRUNC_REGEX, queryStr)
        for x in list:
            result = re.search(dc.TRUNC_REGEX, queryStr)

            new_String = re.sub(
                dc.TRUNC_REGEX,
                "date_trunc('"
                + truncParamDict.get(result.group(4))
                + "',"
                + result.group(1)
                + ")",
                queryStr,
                1,
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
        list = re.findall(dc.MONTHS_BETWEEN_REGEX, queryStr)
        for x in list:
            result = re.search(dc.MONTHS_BETWEEN_REGEX, queryStr)

            new_string = re.sub(
                dc.MONTHS_BETWEEN_REGEX,
                "date_diff('month'," + result.group(4) + "," + result.group(1) + ")",
                queryStr,
                1,
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
        list = re.findall(dc.EXTRACT_REGEX, queryStr)

        for x in list:
            # two groups enclosed in separate ( and ) bracket
            result = re.search(dc.EXTRACT_REGEX, queryStr)

            new_String = re.sub(
                dc.EXTRACT_REGEX,
                "extract("
                + extractParamDict.get(result.group(1))
                + " from "
                + result.group(2)
                + ")",
                queryStr,
                1,
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
        list = re.findall(dc.DATE_SUB_REGEX, queryStr)
        for x in list:
            result = re.search(dc.DATE_SUB_REGEX, queryStr)

            new_String = re.sub(
                dc.DATE_SUB_REGEX,
                "date_add('day',-" + result.group(4) + "," + result.group(1) + ")",
                queryStr,
                1,
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
        list = re.findall(dc.DATE_DIFF_REGEX, queryStr)
        for x in list:
            result = re.search(dc.DATE_DIFF_REGEX, queryStr)

            new_string = re.sub(
                dc.DATE_DIFF_REGEX,
                "date_diff('day'," + result.group(4) + "," + result.group(1) + ")",
                queryStr,
                1,
            )
            queryStr = new_string
    except:
        queryStr = "Error while converting datediff"
    return queryStr


# _convertdatediff(sourceQuery)

sourceQuery = "select * from table1 where date_add(to_date(localstartdt),15) > to_date(localenddt)"


def _convertdateadd(queryStr):
    try:
        list = re.findall(dc.DATE_ADD_REGEX, queryStr)

        for x in list:
            result = re.search(dc.DATE_ADD_REGEX, queryStr)

            new_String = re.sub(
                dc.DATE_ADD_REGEX,
                "date_add('day'," + result.group(4) + "," + result.group(1) + ")",
                queryStr,
                1,
            )
            queryStr = new_String
    except:
        queryStr = "Error while converting date_add"
    return queryStr


sourceQuery = (
    "select * from table1 where add_months('2022-01-23',2) > to_date(localenddt)"
)


def _convertaddmonths(queryStr):
    try:
        list = re.findall(dc.ADD_MONTHS_REGEX, queryStr)

        for x in list:
            # two groups enclosed in separate ( and ) bracket
            result = re.search(dc.ADD_MONTHS_REGEX, queryStr)

            new_String = re.sub(
                dc.ADD_MONTHS_REGEX,
                "date_add('month'," + result.group(4) + "," + result.group(1) + ")",
                queryStr,
                1,
            )
            queryStr = new_String
    except:
        queryStr = "Error while converting add_months"
    return queryStr


# _convertaddmonths(sourceQuery)

sourceQuery = "select * from table1 where to_date(localstartdt) > to_date(localenddt)"


def _converttodate(queryStr):
    try:
        list = re.findall(dc.TO_DATE_REGEX, queryStr)

        for x in list:
            result = re.search(dc.TO_DATE_REGEX, queryStr)

            new_String = re.sub(
                dc.TO_DATE_REGEX, "date(" + result.group(1) + ")", queryStr, 1
            )
            queryStr = new_String
    except:
        queryStr = "Error while converting to_date"
    return queryStr


# _converttodate(sourceQuery)

sourceQuery = "select * from table1 where last_day(localstartdt) > to_date(localenddt)"


def _convertlastday(queryStr):
    try:
        list = re.findall(dc.LAST_DAY_REGEX, queryStr)

        for x in list:
            result = re.search(dc.LAST_DAY_REGEX, queryStr)

            new_String = re.sub(
                dc.LAST_DAY_REGEX,
                "last_day_of_month(" + result.group(1) + ")",
                queryStr,
                1,
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
        list = re.findall(dc.DAY_OF_MONTH_REGEX, queryStr)

        for x in list:
            result = re.search(dc.DAY_OF_MONTH_REGEX, queryStr)

            new_String = re.sub(
                dc.DAY_OF_MONTH_REGEX,
                "day_of_month(" + result.group(1) + ")",
                queryStr,
                1,
            )
            queryStr = new_String
    except:
        queryStr = "Error while converting dayofmonth"
    return queryStr


# _convertdayofmonth(sourceQuery)

sourceQuery = "select * from table1 where weekofyear(localstartdt) > 50"


def _convertweekofyear(queryStr):
    try:
        list = re.findall(dc.WEEK_OF_YEAR_REGEX, queryStr)

        for x in list:
            result = re.search(dc.WEEK_OF_YEAR_REGEX, queryStr)

            new_String = re.sub(
                dc.WEEK_OF_YEAR_REGEX,
                "week_of_year(" + result.group(1) + ")",
                queryStr,
                1,
            )
            queryStr = new_String
    except:
        queryStr = "Error while converting weekofyear"
    return queryStr


# _convertdayofmonth(sourceQuery)

sourceQuery = "select * from table1 where current_date() > 50"


def _convertcurrentdate(queryStr):
    try:
        list = re.findall(dc.CURRENT_DATE_REGEX, queryStr)

        for x in list:
            new_String = re.sub(dc.CURRENT_DATE_REGEX, "current_date", queryStr, 1)
            queryStr = new_String
    except:
        queryStr = "Error while converting current_date"
    return queryStr


# _convertcurrentdate(sourceQuery)

sourceQuery = "select * from table1 where current_timestamp() > 50"


def _convertcurrenttimestamp(queryStr):
    try:
        list = re.findall(dc.CURRENT_TIMESTAMP_REGEX, queryStr)

        for x in list:
            new_String = re.sub(
                dc.CURRENT_TIMESTAMP_REGEX, "current_timestamp", queryStr, 1
            )
            queryStr = new_String
    except:
        queryStr = "Error while converting current_timestamp"
    return queryStr


# _convertcurrenttimestamp(sourceQuery)

sourceQuery = "select cast(date1 as date), cast(date2 as timestamp), cast(abc  as DATE), CAST(abc2 AS TIMESTAMP) from table1 where current_timestamp() > 50"


def _convertcastdatetime(queryStr):
    try:
        list = re.findall(dc.CAST_REGEX, queryStr)

        for x in list:
            result = re.search(dc.CAST_REGEX, queryStr)
            new_String = re.sub(
                dc.CAST_REGEX,
                "try_cast(" + result.group(2) + " as " + result.group(4) + ")",
                queryStr,
                1,
            )
            queryStr = new_String
    except:
        queryStr = "Error while converting castdatetime"

    return queryStr


# _convertcastdatetime(sourceQuery)

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
]
