import time
import json
import os
from azure.monitor.query import LogsQueryClient
from azure.identity import DefaultAzureCredential

class MetricsCollector:
    def __init__(self):
        self.metrics = {
            "execution_times": [],
            "api_latencies": [],
            "request_count": 0,
            "total_cost": 0.0
        }

    def record_execution_time(self, start_time, end_time):
        execution_time = end_time - start_time
        self.metrics["execution_times"].append(execution_time)
        print(f"Execution time: {execution_time:.4f} seconds")

    def record_api_latency(self, latency):
        self.metrics["api_latencies"].append(latency)
        print(f"API latency: {latency:.4f} seconds")

    def increment_request_count(self):
        self.metrics["request_count"] += 1

    def calculate_cost(self, pages_processed=None):
        """
        Calculate Azure Form Recognizer cost
        Read API: $1.50 per 1000 pages (as of 2023)
        """
        if pages_processed is None:
            # Estimate based on requests (assuming average 5 pages per document)
            pages_processed = self.metrics["request_count"] * 5

        cost_per_1000_pages = 1.50
        cost = (pages_processed / 1000) * cost_per_1000_pages
        self.metrics["total_cost"] = cost
        print(f"Estimated cost for {pages_processed} pages: ${cost:.4f}")
        return cost

    def get_azure_usage_cost(self, subscription_id=None):
        """
        Query Azure Monitor for actual usage costs
        This would require proper Azure authentication and permissions
        """
        try:
            if subscription_id:
                credential = DefaultAzureCredential()
                client = LogsQueryClient(credential)

                # Query for Form Recognizer usage in the last 24 hours
                query = """
                AzureMetrics
                | where MetricName == "TotalCalls" or MetricName == "TotalTransactions"
                | where ResourceProvider == "MICROSOFT.COGNITIVESERVICES"
                | where OperationName contains "FormRecognizer"
                | summarize TotalCalls = sum(Total) by bin(TimeGenerated, 1h)
                | order by TimeGenerated desc
                """

                # Note: This is a placeholder - actual implementation would require
                # proper Azure Monitor setup and permissions
                print("Azure usage query would be executed here")
                return 0.0
            else:
                print("No subscription ID provided for Azure cost query")
                return 0.0
        except Exception as e:
            print(f"Error querying Azure costs: {e}")
            return 0.0

    def get_summary(self):
        summary = {
            "total_requests": self.metrics["request_count"],
            "avg_execution_time": sum(self.metrics["execution_times"]) / len(self.metrics["execution_times"]) if self.metrics["execution_times"] else 0,
            "avg_api_latency": sum(self.metrics["api_latencies"]) / len(self.metrics["api_latencies"]) if self.metrics["api_latencies"] else 0,
            "max_execution_time": max(self.metrics["execution_times"]) if self.metrics["execution_times"] else 0,
            "min_execution_time": min(self.metrics["execution_times"]) if self.metrics["execution_times"] else 0,
            "estimated_cost": self.metrics["total_cost"]
        }
        return summary

    def save_to_file(self, filename="metrics.json"):
        with open(filename, 'w') as f:
            json.dump(self.get_summary(), f, indent=2)
        print(f"Metrics saved to {filename}")

# Global instance for collecting metrics across tests
metrics_collector = MetricsCollector()