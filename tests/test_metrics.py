import unittest
import time
import os
import json
from unittest.mock import patch, MagicMock
from metrics_collector import metrics_collector

# Try to import Azure functions, but make it optional for testing
try:
    from latestocr.__init__ import main, compose_response, read
    AZURE_FUNCTIONS_AVAILABLE = True
except ImportError:
    AZURE_FUNCTIONS_AVAILABLE = False
    print("Warning: Azure Functions not available, some tests will be skipped")

class TestMetrics(unittest.TestCase):

    def setUp(self):
        # Use real Azure credentials if available, otherwise use mocks for testing
        self.endpoint = os.environ.get("FR_ENDPOINT", "https://test.openai.azure.com/")
        self.key = os.environ.get("FR_ENDPOINT_KEY", "test-key")

        # Set environment variables for the function to use
        os.environ["FR_ENDPOINT"] = self.endpoint
        os.environ["FR_ENDPOINT_KEY"] = self.key

        # Track if we're using real Azure services
        self.use_real_azure = os.environ.get("USE_REAL_AZURE", "false").lower() == "true"

        print(f"Test setup - USE_REAL_AZURE: {self.use_real_azure}")
        print(f"Test setup - FR_ENDPOINT: {self.endpoint[:50]}...")
        print(f"Test setup - FR_ENDPOINT_KEY: {'[SET]' if self.key != 'test-key' else '[DEFAULT]'}")

    @unittest.skipUnless(AZURE_FUNCTIONS_AVAILABLE, "Azure Functions not available")
    def test_function_execution_time(self):
        if not self.use_real_azure:
            # Use mocks for testing without real Azure calls
            with patch('latestocr.__init__.DocumentAnalysisClient') as mock_client:
                mock_poller = MagicMock()
                mock_result = MagicMock()
                mock_result.content = "Extracted text content"
                mock_poller.result.return_value = mock_result
                mock_client.return_value.begin_analyze_document_from_url.return_value = mock_poller

                # Create a mock request
                mock_req = MagicMock()
                mock_req.get_json.return_value = {
                    "values": [
                        {
                            "recordId": "1",
                            "data": {
                                "Url": "dGVzdC11cmw=",  # base64 for "test-url"
                                "SasToken": "?sas=token"
                            }
                        }
                    ]
                }


                # Measure execution time
                start_time = time.time()
                response = main(mock_req)
                end_time = time.time()

                execution_time = end_time - start_time
                metrics_collector.record_execution_time(start_time, end_time)
                metrics_collector.increment_request_count()

                # Assert response is successful
                self.assertEqual(response.status_code, 200)

                # Check that metrics can be logged or returned
                self.assertGreater(execution_time, 0)
        else:
            # Skip this test when using real Azure to avoid costs
            self.skipTest("Skipping execution time test with real Azure credentials")

    @unittest.skipUnless(AZURE_FUNCTIONS_AVAILABLE, "Azure Functions not available")
    def test_request_count(self):
        # Test with multiple records
        json_data = {
            "values": [
                {"recordId": "1", "data": {"Url": "dGVzdC11cmw=", "SasToken": "?sas=token"}},
                {"recordId": "2", "data": {"Url": "dGVzdC11cmw=", "SasToken": "?sas=token"}},
                {"recordId": "3", "data": {"Url": "dGVzdC11cmw=", "SasToken": "?sas=token"}}
            ]
        }

        if not self.use_real_azure:
            with patch('latestocr.__init__.DocumentAnalysisClient') as mock_client:
                mock_poller = MagicMock()
                mock_result = MagicMock()
                mock_result.content = "Test content"
                mock_poller.result.return_value = mock_result
                mock_client.return_value.begin_analyze_document_from_url.return_value = mock_poller

                start_time = time.time()
                result = compose_response(json.dumps(json_data))
                end_time = time.time()

                execution_time = end_time - start_time
                request_count = len(json_data["values"])

                metrics_collector.record_execution_time(start_time, end_time)
                for _ in range(request_count):
                    metrics_collector.increment_request_count()

                print(f"Processed {request_count} requests in {execution_time:.4f} seconds")
                print(f"Average time per request: {execution_time/request_count:.4f} seconds")

                # Parse result to verify
                parsed_result = json.loads(result)
                self.assertEqual(len(parsed_result["values"]), request_count)
        else:
            # Skip this test when using real Azure to avoid costs
            self.skipTest("Skipping request count test with real Azure credentials")

    @unittest.skipUnless(AZURE_FUNCTIONS_AVAILABLE, "Azure Functions not available")
    def test_latency_measurement(self):
        if not self.use_real_azure:
            # Use mocks for safe testing
            with patch('latestocr.__init__.DocumentAnalysisClient') as mock_client:
                mock_poller = MagicMock()
                mock_result = MagicMock()
                mock_result.content = "Latency test content"
                mock_poller.result.return_value = mock_result
                mock_client.return_value.begin_analyze_document_from_url.return_value = mock_poller

                start_time = time.time()
                output = read(self.endpoint, self.key, "test-id", {"Url": "dGVzdC11cmw=", "SasToken": "?sas=token"})
                end_time = time.time()

                latency = end_time - start_time
                metrics_collector.record_api_latency(latency)
                metrics_collector.increment_request_count()

                self.assertIn("text", output["data"])
                self.assertEqual(output["recordId"], "test-id")
        else:
            # For real Azure, use a simple text document or skip this test
            # The API expects a real document URL, so we'll create a simple test
            self.skipTest("Skipping latency test with real Azure - requires valid document URL")

    def test_cost_calculation(self):
        # Clear previous metrics to start fresh
        metrics_collector.metrics["execution_times"].clear()
        metrics_collector.metrics["api_latencies"].clear()
        metrics_collector.metrics["request_count"] = 0
        metrics_collector.metrics["total_cost"] = 0.0

        # Add some test data to the metrics collector
        metrics_collector.record_execution_time(1.0, 2.5)  # 1.5 seconds
        metrics_collector.record_execution_time(2.0, 4.0)  # 2.0 seconds
        metrics_collector.record_api_latency(1.2)
        metrics_collector.record_api_latency(0.8)
        metrics_collector.increment_request_count()
        metrics_collector.increment_request_count()

        # Test cost calculation based on request count
        pages_per_request = 5  # Assume average 5 pages per document
        total_pages = metrics_collector.metrics["request_count"] * pages_per_request

        cost = metrics_collector.calculate_cost(total_pages)

        # Verify cost is calculated correctly
        expected_cost = (total_pages / 1000) * 1.50
        self.assertEqual(cost, expected_cost)
        self.assertGreater(cost, 0)  # Cost should be greater than 0

        # Verify metrics are recorded
        self.assertEqual(metrics_collector.metrics["request_count"], 2)
        self.assertEqual(len(metrics_collector.metrics["execution_times"]), 2)
        self.assertEqual(len(metrics_collector.metrics["api_latencies"]), 2)

    def test_azure_usage_cost_query(self):
        # Test Azure usage query (will return 0.0 without proper credentials)
        cost = metrics_collector.get_azure_usage_cost()
        self.assertGreaterEqual(cost, 0)

if __name__ == '__main__':
    # Clear metrics before running tests to start fresh
    print("Clearing previous metrics...")
    metrics_collector.metrics["execution_times"].clear()
    metrics_collector.metrics["api_latencies"].clear()
    metrics_collector.metrics["request_count"] = 0
    metrics_collector.metrics["total_cost"] = 0.0

    # Run tests and collect metrics
    unittest.main(verbosity=2)

    # After all tests, save metrics summary
    print("\n=== METRICS SUMMARY ===")
    summary = metrics_collector.get_summary()
    print(json.dumps(summary, indent=2))

    # Save to file for GitHub workflow (relative to tests directory)
    import os
    metrics_file = os.path.join(os.path.dirname(__file__), "test_metrics.json")
    metrics_collector.save_to_file(metrics_file)