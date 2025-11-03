import unittest
import time
import os
import base64
from metrics_collector import metrics_collector

# Only import if Azure Functions are available
try:
    from latestocr.__init__ import read
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

class TestRealAzureMetrics(unittest.TestCase):
    """
    Tests that use real Azure Form Recognizer API.
    These tests will incur costs and require valid credentials.
    """

    def setUp(self):
        if not AZURE_AVAILABLE:
            self.skipTest("Azure Functions not available")

        self.endpoint = os.environ.get("FR_ENDPOINT")
        self.key = os.environ.get("FR_ENDPOINT_KEY")

        print(f"Real Azure test setup - FR_ENDPOINT: {self.endpoint}")
        print(f"Real Azure test setup - FR_ENDPOINT_KEY: {'[SET]' if self.key else '[NOT SET]'}")

        if not self.endpoint or not self.key:
            self.skipTest("Azure credentials not provided")

        # Test document - you need to replace this with a real accessible URL
        # Option 1: Upload a test PDF/image to Azure Blob Storage and get SAS URL
        # Option 2: Use a publicly accessible test document
        self.test_document_url = os.environ.get("TEST_DOCUMENT_URL")
        print(f"Real Azure test setup - TEST_DOCUMENT_URL: {'[SET]' if self.test_document_url else '[NOT SET]'}")

        if not self.test_document_url:
            self.skipTest("TEST_DOCUMENT_URL environment variable not set")

        # Encode the URL for the function (as it expects base64 + SAS token)
        url_bytes = self.test_document_url.encode('utf-8')
        self.encoded_url = base64.b64encode(url_bytes).decode('utf-8')
        self.sas_token = ""  # Add SAS token if needed

    def test_real_azure_latency(self):
        """Test actual Azure Form Recognizer API latency with real document."""
        start_time = time.time()
        output = read(self.endpoint, self.key, "real-test-1", {
            "Url": self.encoded_url,
            "SasToken": self.sas_token
        })
        end_time = time.time()

        latency = end_time - start_time
        metrics_collector.record_api_latency(latency)
        metrics_collector.increment_request_count()

        print(f"API latency: {latency:.4f} seconds")
        print(f"Real Azure API latency: {latency:.4f} seconds")

        # Calculate cost based on actual API call (assume 5 pages per document)
        metrics_collector.calculate_cost(5)

        print(f"Current metrics after this test - requests: {metrics_collector.metrics['request_count']}, avg_latency: {sum(metrics_collector.metrics['api_latencies'])/len(metrics_collector.metrics['api_latencies']) if metrics_collector.metrics['api_latencies'] else 0:.4f}")

        # Verify response structure
        self.assertEqual(output["recordId"], "real-test-1")
        if "data" in output:
            self.assertIn("text", output["data"])
            print(f"Extracted text length: {len(output['data']['text'])}")
        elif "errors" in output:
            print(f"API returned errors: {output['errors']}")
            # Even with errors, we got a latency measurement

    def test_real_azure_multiple_documents(self):
        """Test processing multiple documents to measure throughput."""
        document_count = 3  # Adjust based on your test documents
        total_start_time = time.time()

        for i in range(document_count):
            start_time = time.time()
            output = read(self.endpoint, self.key, f"real-test-{i+1}", {
                "Url": self.encoded_url,  # Same document or different URLs
                "SasToken": self.sas_token
            })
            end_time = time.time()

            latency = end_time - start_time
            metrics_collector.record_api_latency(latency)
            metrics_collector.increment_request_count()

            print(f"API latency: {latency:.4f} seconds")
            print(f"Document {i+1} latency: {latency:.4f} seconds")

        total_end_time = time.time()
        total_time = total_end_time - total_start_time

        # Calculate total cost for all documents
        total_pages = document_count * 5  # Assume 5 pages per document
        metrics_collector.calculate_cost(total_pages)

        print(f"Processed {document_count} documents in {total_time:.4f} seconds")
        print(f"Average time per document: {total_time/document_count:.4f} seconds")
        print(f"Total estimated cost: ${metrics_collector.metrics['total_cost']:.4f}")

        print(f"Final metrics after all tests - requests: {metrics_collector.metrics['request_count']}, avg_latency: {sum(metrics_collector.metrics['api_latencies'])/len(metrics_collector.metrics['api_latencies']) if metrics_collector.metrics['api_latencies'] else 0:.4f}")

if __name__ == '__main__':
    unittest.main(verbosity=2)