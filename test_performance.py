import pytest
import time
import os
import json
from unittest.mock import patch, MagicMock
from latestocr import main, compose_response

def test_performance_metrics():
    use_real_azure = os.getenv("USE_REAL_AZURE", "false").lower() == "true"

    # Prepare data for 10 requests
    if use_real_azure:
        # For real Azure, use a valid document URL (assuming TEST_DOCUMENT_URL is set)
        test_document_url = os.getenv("TEST_DOCUMENT_URL")
        if not test_document_url:
            pytest.skip("TEST_DOCUMENT_URL not set for real Azure tests")
        # Encode URL to base64
        import base64
        url_b64 = base64.b64encode(test_document_url.encode()).decode()
        # Assume SasToken is part of the URL or empty
        sas_token = ""
        mock_data = {
            "values": [
                {
                    "recordId": f"record_{i}",
                    "data": {
                        "Url": url_b64,
                        "SasToken": sas_token
                    }
                } 
            ]
        }
        print(mock_data)
    else:
        # Mock data for testing
        mock_data = {
            "values": [
                {
                    "recordId": f"record_{i}",
                    "data": {
                        "Url": "bW9ja191cmw=",  # base64 for "mock_url"
                        "SasToken": "?sas=mock"
                    }
                }
            ]
        }

    if use_real_azure:
        # Run against real Azure
        start_time = time.time()
        response = compose_response(json.dumps(mock_data))
        end_time = time.time()
    else:
        # Mock the Azure client
        with patch('latestocr.DocumentAnalysisClient') as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_poller = MagicMock()
            mock_result = MagicMock()
            mock_result.content = "Mock extracted text"
            mock_poller.result.return_value = mock_result
            mock_client.begin_analyze_document_from_url.return_value = mock_poller

            # Measure start time
            start_time = time.time()

            # Execute the function
            response = compose_response(json.dumps(mock_data))

            # Measure end time
            end_time = time.time()

    # Calculate metrics
    execution_time = end_time - start_time
    num_requests = len(mock_data["values"])
    # Estimated cost: Azure Form Recognizer Read API ~$0.001 per page (assuming 1 page per doc)
    # Adjust based on actual pricing
    estimated_cost_per_doc = 0.001  # placeholder
    total_estimated_cost = num_requests * estimated_cost_per_doc

    # Assertions
    assert execution_time > 0
    assert num_requests == 10
    assert total_estimated_cost == 0.01  # 10 * 0.001

    # Print metrics for CI
    print(f"Execution Time: {execution_time:.4f} seconds")
    print(f"Number of Requests: {num_requests}")
    print(f"Estimated Cost: ${total_estimated_cost:.4f}")

    # Verify response structure
    response_data = json.loads(response)
    assert len(response_data["values"]) == num_requests

    # Ensure no errors in response
    for value in response_data["values"]:
        assert "errors" not in value or len(value["errors"]) == 0