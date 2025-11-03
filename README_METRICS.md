# Custom Form Recognition Metrics Testing

This document explains how to run the metrics tests for the Custom Form Recognition Azure Function.

## Setup

### 1. Environment Variables

The tests can run in two modes:

#### Mock Mode (Default - No Azure Costs)
- Set `USE_REAL_AZURE=false` (default)
- Uses mocked Azure services for testing without incurring costs
- Safe for CI/CD pipelines

#### Real Azure Mode (With Costs)
- Set `USE_REAL_AZURE=true`
- Requires valid Azure credentials
- Actually calls Azure Form Recognizer API
- **Warning**: This will incur Azure usage costs!

### 2. GitHub Secrets (for CI/CD)

Add these secrets to your GitHub repository:

- `FR_ENDPOINT`: Your Azure Form Recognizer endpoint URL
- `FR_ENDPOINT_KEY`: Your Azure Form Recognizer API key
- `USE_REAL_AZURE`: Set to `true` if you want to run real API tests (optional, defaults to `false`)

### 3. Local Testing

For local testing, create a `.env` file or set environment variables:

```bash
export FR_ENDPOINT="https://your-resource.openai.azure.com/"
export FR_ENDPOINT_KEY="your-api-key"
export USE_REAL_AZURE="true"  # or "false" for mock mode
```

## Running Tests

### Local Execution

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
python -m pytest tests/test_metrics.py -v

# Run specific test
python tests/test_metrics.py TestMetrics.test_latency_measurement
```

### GitHub Actions

The workflow will automatically run tests based on the `USE_REAL_AZURE` setting.

## Metrics Collected

The test suite collects the following metrics:

1. **Execution Time**: Time taken to run the Azure Function
2. **API Latency**: Time for individual Azure API calls
3. **Request Count**: Number of documents processed
4. **Cost Estimation**: Estimated Azure Form Recognizer costs
5. **Workflow Runtime**: Total GitHub Actions execution time

## Output Files

- `tests/test_metrics.json`: Detailed metrics summary
- GitHub Actions artifacts: Downloadable metrics files

## Cost Considerations

- **Mock Mode**: $0.00 - No Azure API calls
- **Real Mode**: ~$1.50 per 1000 pages processed (Azure pricing as of 2023)

Always test in mock mode first to ensure functionality before enabling real Azure calls.

## Example Metrics Output

```json
{
  "total_requests": 5,
  "avg_execution_time": 2.341,
  "avg_api_latency": 1.892,
  "max_execution_time": 3.124,
  "min_execution_time": 1.567,
  "estimated_cost": 0.0075
}