# # Example use:
# # import the TrinoBulkInsert class
# from trino_bulk_insert import TrinoBulkInsert
#
# # Create a TrinoBulkInsert instance
# tbi = TrinoBulkInsert()
#
# # Set a specific max row batch size if desired
# # The default is 1 million rows which will never be reached before the statement max length
# # tbi.setBatchSize(batchSize=10000)
#
# # Must set the SEP connection configuration. This connection is used to fetch the table DDL when setTableName is called, so it must be done first.
# tbi.setConnection(host="my.sep.cluster.com", port=8443, username="myusername", password="mypassword", catalog="hive", schema="myschema", https=True)
#
# # Must set the table name, it can be the fully qualified name catalog.schema.table or just the
# # table name in which case the table must be in catalog and schema used for the connection
# tbi.setTableName(tableName="mytable")
#
# # If verbose is enabled the class will print some info system output (optional)
# tbi.setVerbose(True)
#
# # Here is where the logic for adding rows goes
# # All you have to do is call the addRow with the data for each row
# for x in range(100000):
#     tbi.addRow('test'+str(x), x, '2022-01-01')
# # End - logic for adding rows goes
#
# # *** Must flush the connection *** This will write any rows that did not trigger an insert by either reaching
# # the max batch size or the max insert statement length of 1 million characters
# tbi.flushConnection()

import trino
from lib.logger import get_logger

LOG = get_logger(__file__)


class TrinoBulkInsert():

    def __init__(self) -> None:
        self.maxStringLength = 1000000
        self.batchSize = 1000000
        self.values = ""
        self.conn = None
        self.rowCounter = 0
        self.verbose = False
        self.retries = 2
        self.__resetRetries()

    def setRetries(self, n):
        self.retries = n

    def __resetRetries(self):
        self.remaining_retries = self.retries
        self.remaining_create_retries = self.retries

    def setBatchSize(self, batchSize: int):
        self.batchSize = batchSize

    def createTable(self, tableName: str, tableExists: bool, ifExists: str, createStatement: str):
        LOG.info('*** Creating Table ***')
        self.tableName = tableName
        cur = self.__getConnection().cursor()

        # Handle if exists
        try:
            if tableExists:
                if ifExists == "replace":
                    LOG.info(f'Replace - Dropping table {tableName}')
                    cur.execute(f'drop table {tableName}')
                elif ifExists == "fail":
                    raise Exception(f'Table {tableName} already exists')
                elif ifExists == "append":
                    return True

            cur.execute(createStatement)
            cur.fetchall()
            return True
        except Exception as e:
            LOG.info('Encountered {0} when creating table [{1}]. {2} retries remaining.'.format(
                e, tableName, self.remaining_create_retries))
            if self.remaining_create_retries > 0:
                self.remaining_create_retries -= 1
                self.createTable(tableName, tableExists, ifExists, createStatement)
            else:
                LOG.info('Aborting load - too many errors')
                self.__resetRetries()
                raise



            LOG.info(f'Encountered Error while creating table: {e}')
            # check re-try if failure
            raise

    def setTableName(self, tableName: str):
        self.tableName = tableName
        cur = self.__getConnection().cursor()
        cur.execute('SELECT * from ' + tableName + ' limit 0')
        cur.fetchall()
        self.columns = {}
        for col in cur.description:
            self.columns[col[0]] = col[1]
        self.datatypes = [t.split('(')[0] for t in list(self.columns.values())]
        # This string manipulation removes any type parameters, e.g. DECIMAL(10,5) >> DECIMAL,
        # since they cannot be used in a literal

    def setTableColumns(self, columns: dict):
        self.columns = columns
        self.datatypes = [self.__convertType(t.split('(')[0]) for t in list(self.columns.values())]

    def setVerbose(self, verbose: bool):
        self.verbose = verbose

    def __getInsertStatement(self):
        insertStatement = "insert into " + self.tableName + " ("

        for col in self.columns:
            insertStatement = insertStatement + \
                ("" if list(self.columns.keys())[0] == col else ",") + col

        insertStatement = insertStatement + ") values \n" + self.values

        return insertStatement

    def __getCreateStatement(self):
        createStatement = "create table " + self.tableName + " ("
        index = 0
        for col in self.columns:
            createStatement += ("" if index == 0 else ",")
            createStatement += col + " " + self.datatypes[index]
            index += 1
        createStatement = createStatement + ")"
        return createStatement

    def __exceedsMaxLength(self, row: str):
        return len(self.__getInsertStatement() + "," + row) > self.maxStringLength

    def __setConnectionFromParameters(self, host: str, port: int, username: str, password: str = None, impersonate_user: str = None, catalog: str = 'system', schema: str = 'runtime', https: bool = False):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.impersonate_user = impersonate_user
        self.catalog = catalog
        self.schema = schema
        self.http_scheme = 'https' if https else 'http'

    def __setFromConnection(self, connection):
        self.conn = connection

    def setConnection(self, *args, **kwargs):
        if len(args) + len(kwargs.items()) == 1:
            if len(args) == 1:
                self.__setFromConnection(*args)
            else:
                self.__setFromConnection(kwargs.items()[1])
        else:
            self.__setConnectionFromParameters(*args, **kwargs)

    def __getConnection(self):
        if self.conn == None:
            if self.password != None:
                self.conn = trino.dbapi.connect(
                    host=self.host,
                    port=self.port,
                    user=self.impersonate_user,
                    catalog=self.catalog,
                    schema=self.schema,
                    http_scheme=self.http_scheme,
                    source='querybook',
                    auth=trino.auth.BasicAuthentication(self.username, self.password))
            else:
                self.conn = trino.dbapi.connect(
                    host=self.host,
                    port=self.port,
                    user=self.username,
                    catalog=self.catalog,
                    schema=self.schema,
                    http_scheme=self.http_scheme,
                    source='querybook')
        return self.conn

    def addRow(self, values = []):
        row = "("
        index = 0
        for arg in values:
            row += ("" if index == 0 else ",")
            row += self.datatypes[index] + \
                " '{0}'".format(str(arg).replace("'", "''").strip())
            index += 1
        row = row + ")"

        if self.__exceedsMaxLength(row):
            LOG.info("Max statement length reached ("
                       + str(len(self.__getInsertStatement())) + ")")
            self.__insertRows()

            self.values = row
            self.rowCounter = 1
        else:
            if self.values != "":
                self.values = self.values + ",\n"

            self.values = self.values + row
            self.rowCounter += 1

            if self.rowCounter == self.batchSize:
                LOG.info("Max batch size reached")
                self.__insertRows()

                self.values = ""
                self.rowCounter = 0

    def flushConnection(self):
        LOG.info("Flushing connection")
        if self.rowCounter > 0:
            success = self.__insertRows()
            while not success:
                success = self.__insertRows()
        self.__getConnection().close()

    def __insertRows(self):
        LOG.info("Inserting " + str(self.rowCounter) + " rows")

        cur = self.__getConnection().cursor()
        try:
            cur.execute(self.__getInsertStatement())
            cur.fetchall()
            return True
        except Exception as e:
            LOG.info('Encountered {0} inserting rows. {1} retries remaining.'.format(
                e, self.remaining_retries))
            if self.remaining_retries > 0:
                self.remaining_retries -= 1
                return False
            else:
                LOG.info('Aborting load - too many errors')
                self.__resetRetries()
                raise

    def __convertType(self, data_type):
        if data_type == 'float':
            return 'DOUBLE'
        elif data_type == 'integer':
            return 'INTEGER'
        elif data_type == 'string':
            return 'VARCHAR'
        elif data_type == 'datetime':
            return 'TIMESTAMP'
        elif data_type == 'boolean':
            return 'BOOLEAN'
        else:
            # default to varchar
            return 'VARCHAR'
