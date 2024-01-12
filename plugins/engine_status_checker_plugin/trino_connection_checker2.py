from datetime import datetime
from typing import Dict

import requests
import os
import socket
from pathlib import Path
from env import QuerybookSettings

from lib.engine_status_checker.base_checker import BaseEngineStatusChecker, EngineStatus
from const.query_execution import QueryEngineStatus
from lib.logger import get_logger
from lib.query_executor.base_executor import QueryExecutorBaseClass
from lib.utils.utils import Timeout
from logic.admin import get_query_metastore_by_id
from models.admin import QueryMetastore

LOG = get_logger(__name__)


def get_utc_now_str() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


class TrinoConnectionChecker2(BaseEngineStatusChecker):
    @classmethod
    def NAME(cls) -> str:
        return "TrinoConnectionChecker2"

    @classmethod
    def perform_check_with_executor(
        cls, executor: QueryExecutorBaseClass, executor_params: Dict, _engine_dict: Dict
    ) -> EngineStatus:
        # Load metastore related to this engine, if any
        metastore_id = _engine_dict.get("metastore_id")
        metastore = (
            None if metastore_id is None else get_query_metastore_by_id(metastore_id)
        )

        # Connection checks
        trino_result = check_trino_connection(executor_params)
        metastore_result = check_metastore_connection(metastore)
        ranger_result = check_ranger_connection()

        result: EngineStatus = {
            "status": QueryEngineStatus.GOOD.value,
            "messages": [],
        }

        if any(
            result["status"] == QueryEngineStatus.ERROR.value
            for result in [trino_result, metastore_result, ranger_result]
        ):
            result["status"] = QueryEngineStatus.ERROR.value

        result["messages"].extend(trino_result["messages"])
        result["messages"].extend(metastore_result["messages"])
        result["messages"].extend(ranger_result["messages"])

        return result


def check_trino_connection(client_settings: Dict) -> Dict:
    result: Dict = {"status": QueryEngineStatus.GOOD.value, "messages": []}

    try:
        with Timeout(20, "Connection check took too long"):
            trino_conn_str = Path(client_settings["connection_string"])
            trino_url = os.path.join(
                "https://", trino_conn_str.parts[1], "v1/info/state"
            )
            trino_response = requests.get(url=trino_url, timeout=10)
            trino_response_data = trino_response.json()

            if trino_response_data == "ACTIVE":
                result["messages"].append(
                    f"Trino connection ACTIVE at {get_utc_now_str()} UTC"
                )
            else:
                result["status"] = QueryEngineStatus.ERROR.value
                result["messages"].append(
                    f"Trino connection returned {trino_response_data} at {get_utc_now_str()} UTC"
                )

    except Exception as e:
        result["status"] = QueryEngineStatus.ERROR.value
        result["messages"].append(
            f"Error retrieving Trino connection status at {get_utc_now_str()} UTC: {str(e)}"
        )

    return result


def check_metastore_connection(metastore: QueryMetastore) -> Dict:
    result: Dict = {"status": QueryEngineStatus.GOOD.value, "messages": []}

    if metastore is not None and metastore.loader == "EgHMSMetastoreLoader":
        try:
            with Timeout(20, "Connection check took too long"):
                hms_connection = metastore.metastore_params.get("hms_connection")[0]
                hms_server, hms_port = hms_connection.split(":")

                try:
                    with socket.create_connection((hms_server, hms_port), timeout=10):
                        result["messages"].append(
                            f"Metastore connection ACTIVE at {get_utc_now_str()} UTC"
                        )
                except:
                    result["status"] = QueryEngineStatus.ERROR.value
                    result["messages"].append(
                        f"Metastore connection INACTIVE at {get_utc_now_str()} UTC"
                    )
        except Exception as e:
            result["status"] = QueryEngineStatus.ERROR.value
            result["messages"].append(
                f"Error retrieving metastore connection status at {get_utc_now_str()} UTC: {str(e)}"
            )

    return result


def check_ranger_connection() -> Dict:
    result: Dict = {"status": QueryEngineStatus.GOOD.value, "messages": []}

    # Note: this is a global ranger url, not per engine
    # At some point this might need to be changed
    if QuerybookSettings.RANGER_URL:
        try:
            with Timeout(20, "Connection check took too long"):
                ranger_response = requests.get(
                    url=QuerybookSettings.RANGER_URL, timeout=10
                )
                ranger_response_code = ranger_response.status_code

                if ranger_response_code == 200:
                    result["messages"].append(
                        f"Ranger connection ACTIVE at {get_utc_now_str()} UTC"
                    )
                else:
                    result["status"] = QueryEngineStatus.ERROR.value
                    result["messages"].append(
                        f"Ranger connection INACTIVE at {get_utc_now_str()} UTC"
                    )
        except Exception as e:
            result["status"] = QueryEngineStatus.ERROR.value
            result["messages"].append(
                f"Error retrieving Ranger connection status at {get_utc_now_str()} UTC: {str(e)}"
            )

    return result
