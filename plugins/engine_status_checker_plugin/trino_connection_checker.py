from datetime import datetime
from typing import Dict

import requests
import os
from pathlib import Path

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

    try:
        with Timeout(20, "Connection took too long"):
            conn_str = Path(client_settings["connection_string"])
            url = os.path.join('https://', conn_str.parts[1], "v1/info/state")
            response = requests.get(url=url, timeout=10)
            data = response.json()
            if data == "ACTIVE":
                result["messages"].append(f"Connection ACTIVE at {utc_now_str} UTC")
            else:
                result["status"] = QueryEngineStatus.ERROR.value
                result["messages"].append(f"Connection returned {data} at {utc_now_str} UTC")
    except Exception as e:
        result["status"] = QueryEngineStatus.ERROR.value
        result["messages"].append(f"Connection INACTIVE at {utc_now_str} UTC: {str(e)}")
         
    return result
 