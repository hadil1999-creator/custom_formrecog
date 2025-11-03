import time
import json
import os

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
        Placeholder for Azure Monitor cost querying
        This would require additional Azure SDK dependencies and proper authentication
        For now, returns 0.0 as the actual implementation is complex and requires:
        - azure-monitor-query
        - azure-identity
        - Proper Azure permissions and setup
        """
        print("Azure usage cost query not implemented - requires additional setup")
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