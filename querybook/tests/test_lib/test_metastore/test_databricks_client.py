import sys
from types import ModuleType
from unittest import TestCase
from unittest.mock import MagicMock, patch

# The CI runner doesn't install databricks-sdk. Stub the package so the module
# can be imported and the @patch decorators can resolve their targets.
_databricks_stub = ModuleType("databricks")
_databricks_stub.sdk = ModuleType("databricks.sdk")
_databricks_stub.sdk.WorkspaceClient = MagicMock()
_databricks_stub.sdk.core = ModuleType("databricks.sdk.core")
_databricks_stub.sdk.core.Config = MagicMock()
_databricks_stub.sdk.service = ModuleType("databricks.sdk.service")
_databricks_stub.sdk.service.catalog = ModuleType("databricks.sdk.service.catalog")
_databricks_stub.sdk.service.catalog.TableInfo = MagicMock()
sys.modules.setdefault("databricks", _databricks_stub)
sys.modules.setdefault("databricks.sdk", _databricks_stub.sdk)
sys.modules.setdefault("databricks.sdk.core", _databricks_stub.sdk.core)
sys.modules.setdefault("databricks.sdk.service", _databricks_stub.sdk.service)
sys.modules.setdefault("databricks.sdk.service.catalog", _databricks_stub.sdk.service.catalog)


class TestDatabricksClientAuthSelection(TestCase):

    @patch("clients.databricks_client.WorkspaceClient")
    @patch("clients.databricks_client.Config")
    def test_token_auth_uses_token_config(self, mock_config, mock_ws):
        from clients.databricks_client import DatabricksUnityCatalogClient

        DatabricksUnityCatalogClient(
            workspace_url="https://example.databricks.com",
            token="dapi-test-token",
        )

        mock_config.assert_called_once_with(
            host="https://example.databricks.com",
            token="dapi-test-token",
        )

    @patch("clients.databricks_client.WorkspaceClient")
    @patch("clients.databricks_client.Config")
    def test_oidc_auth_uses_file_oidc_config(self, mock_config, mock_ws):
        from clients.databricks_client import DatabricksUnityCatalogClient

        DatabricksUnityCatalogClient(
            workspace_url="https://example.databricks.com",
            client_id="test-sp-application-id",
        )

        mock_config.assert_called_once_with(
            host="https://example.databricks.com",
            client_id="test-sp-application-id",
            auth_type="file-oidc",
            oidc_token_filepath="/var/run/secrets/databricks/token",
        )

    @patch("clients.databricks_client.WorkspaceClient")
    @patch("clients.databricks_client.Config")
    def test_token_takes_precedence_over_client_id(self, mock_config, mock_ws):
        from clients.databricks_client import DatabricksUnityCatalogClient

        DatabricksUnityCatalogClient(
            workspace_url="https://example.databricks.com",
            token="dapi-test-token",
            client_id="test-sp-application-id",
        )

        mock_config.assert_called_once_with(
            host="https://example.databricks.com",
            token="dapi-test-token",
        )

    @patch("clients.databricks_client.WorkspaceClient")
    @patch("clients.databricks_client.Config")
    def test_neither_token_nor_client_id_raises(self, mock_config, mock_ws):
        from clients.databricks_client import DatabricksUnityCatalogClient

        with self.assertRaises(ValueError):
            DatabricksUnityCatalogClient(
                workspace_url="https://example.databricks.com",
            )
