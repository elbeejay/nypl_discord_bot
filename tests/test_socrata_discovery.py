import json
import unittest
from unittest.mock import patch, AsyncMock, MagicMock
import httpx
from app.tools.socrata import (
    search_nyc_datasets,
    query_dynamic_dataset,
    query_socrata_dataset,
)
from app.agents.nyc_data_agent import nyc_data_agent, NYC_DATA_SYSTEM_INSTRUCTION


class TestSocrataDiscovery(unittest.IsolatedAsyncioTestCase):
    @patch("httpx.AsyncClient.get")
    async def test_search_nyc_datasets_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "resource": {
                        "name": "LinkNYC Kiosk Status",
                        "id": "n6c5-95xh",
                        "description": "Current listing of LinkNYC Kiosks and their status.",
                        "columns_field_name": ["site_id", "address", "boro", "status", "wifi_status"],
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        result_str = await search_nyc_datasets("wifi", limit=3)
        data = json.loads(result_str)

        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["dataset_name"], "LinkNYC Kiosk Status")
        self.assertEqual(data[0]["four_by_four_id"], "n6c5-95xh")
        self.assertIn("wifi_status", data[0]["columns"])

    @patch("httpx.AsyncClient.get")
    async def test_search_nyc_datasets_empty(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response

        result_str = await search_nyc_datasets("nonexistent_term_xyz_123")
        self.assertIn("No NYC Open Data catalog entries found", result_str)

    @patch("httpx.AsyncClient.get")
    async def test_search_nyc_datasets_error_status(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        result_str = await search_nyc_datasets("wifi")
        data = json.loads(result_str)
        self.assertIsInstance(data, list)
        self.assertIn("error", data[0])

    @patch("httpx.AsyncClient.get")
    async def test_search_nyc_datasets_network_exception(self, mock_get):
        mock_get.side_effect = httpx.ConnectError("Connection failed")

        result_str = await search_nyc_datasets("wifi")
        data = json.loads(result_str)
        self.assertIsInstance(data, list)
        self.assertIn("error", data[0])

    @patch("app.tools.socrata.query_socrata_dataset")
    async def test_query_dynamic_dataset_success(self, mock_query):
        mock_query.return_value = [
            {"site_id": "qu-01", "address": "123 Main St", "status": "Active"}
        ]

        result_str = await query_dynamic_dataset(
            four_by_four_id="n6c5-95xh",
            query_filter="status = 'Active'",
            limit=2,
        )
        data = json.loads(result_str)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["site_id"], "qu-01")

        mock_query.assert_called_once_with(
            dataset_id="n6c5-95xh",
            where="status = 'Active'",
            select=None,
            order=None,
            limit=2,
        )

    @patch("app.tools.socrata.query_socrata_dataset")
    async def test_query_dynamic_dataset_soql_where_alias(self, mock_query):
        mock_query.return_value = [{"col": "val"}]

        await query_dynamic_dataset(
            four_by_four_id="abcd-1234",
            soql_where="col = 'val'",
            limit=5,
        )
        mock_query.assert_called_once_with(
            dataset_id="abcd-1234",
            where="col = 'val'",
            select=None,
            order=None,
            limit=5,
        )

    @patch("app.tools.socrata.query_socrata_dataset")
    async def test_query_dynamic_dataset_empty(self, mock_query):
        mock_query.return_value = []

        result_str = await query_dynamic_dataset(
            four_by_four_id="n6c5-95xh",
            query_filter="status = 'Invalid'",
        )
        self.assertIn("No records found in dataset 'n6c5-95xh'", result_str)

    def test_nyc_data_agent_instructions_and_tools(self):
        self.assertIn("search_nyc_datasets", NYC_DATA_SYSTEM_INSTRUCTION)
        self.assertIn("query_dynamic_dataset", NYC_DATA_SYSTEM_INSTRUCTION)
