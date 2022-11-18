from datetime import datetime
from typing import Dict

import requests
import os
from pathlib import Path
from env import QuerybookSettings

from lib.engine_status_checker.base_checker import BaseEngineStatusChecker, EngineStatus
from const.query_execution import QueryEngineStatus
from lib.query_executor.base_executor import QueryExecutorBaseClass
from lib.utils.utils import Timeout


class TrinoConnectionChecker(BaseEngineStatusChecker):
    @classmethod
    def NAME(cls) -> str:
        return "TrinoConnectionChecker"

    @classmethod
    def perform_check_with_executor(
        cls, executor: QueryExecutorBaseClass, executor_params: Dict, _engine_dict: Dict
    ) -> EngineStatus:
        return check_connection(executor_params)


def check_connection(
    client_settings: Dict
) -> EngineStatus:
    result: EngineStatus = {"status": QueryEngineStatus.GOOD.value, "messages": []}

    utc_now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") 

    ranger_response_code_list = []
    try:
        with Timeout(20, "Connection took too long"):
            # Check response from trino API
            trino_conn_str = Path(client_settings["connection_string"])
            trino_url = os.path.join('https://', trino_conn_str.parts[1], "v1/info/state")
            trino_response = requests.get(url=trino_url, timeout=10)
            trino_response_data = trino_response.json()

            if trino_response_data == "ACTIVE":
                result["messages"].append(f"Trino connection ACTIVE at {utc_now_str} UTC")
            else:
                result["status"] = QueryEngineStatus.ERROR.value
                result["messages"].append(f"Trino connection returned {trino_response_data} at {utc_now_str} UTC")

            # Check ranger instance for response
            ranger_response = requests.get(url=QuerybookSettings.RANGER_URL, timeout=10)
            ranger_response_code = ranger_response.status_code
            ranger_response_code_list.append(ranger_response_code)

            if all(x == 200 for x in ranger_response_code_list):
                result["messages"].append(f"Ranger connection ACTIVE at {utc_now_str} UTC")
            else:
                result["status"] = QueryEngineStatus.ERROR.value
                result["messages"].append(f"Ranger connection INACTIVE at {utc_now_str} UTC")

    except Exception as e:
        result["status"] = QueryEngineStatus.ERROR.value
        result["messages"].append(f"Connection INACTIVE at {utc_now_str} UTC: {str(e)}")
         
    return result
 