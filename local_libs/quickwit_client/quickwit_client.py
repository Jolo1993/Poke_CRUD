import requests
from typing import Dict, List, Optional


class QuickwitClient:
    """Python client for Quickwit search engine using the requests library."""

    def __init__(self, base_url: str = "http://localhost:7280"):
        """
        Initialize the Quickwit client.

        Args:
            base_url: The base URL of the Quickwit server
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make a request to the Quickwit API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else {}

    # Index Management

    def create_index(self, index_config: Dict, format: str = "json") -> Dict:
        """Create a new index with the given configuration.

        Args:
            index_config: Either a dictionary (for JSON) or path to YAML file
            format: 'json' or 'yaml'
        """
        if format.lower() == "yaml":
            with open(index_config, 'rb') as config_file:
                data = config_file.read()
            headers = {"content-type": "application/yaml"}
            return self._request("POST", "/api/v1/indexes", data=data, headers=headers)
        else:
            # Your existing JSON implementation
            return self._request("POST", "/api/v1/indexes", json=index_config)

    def delete_index(self, index_id: str) -> Dict:
        """Delete an index by ID."""
        return self._request("DELETE", f"/api/v1/indexes/{index_id}")

    def get_index(self, index_id: str) -> Dict:
        """Get index metadata by ID."""
        return self._request("GET", f"/api/v1/indexes/{index_id}")

    def list_indexes(self) -> Dict:
        """List all available indexes."""
        return self._request("GET", "/api/v1/indexes")

    # Document Management
    def ingest(self, index_id: str, docs: List[Dict]) -> Dict:
        """
        Ingest documents into an index.

        Args:
            index_id: The target index ID
            docs: List of documents to ingest
        """
        return self._request("POST", f"/api/v1/{index_id}/ingest",
                             json={"documents": docs})

    # Search
    def search(self, index_id: str, query: str, max_hits: int = 10,
               start_offset: int = 0, search_fields: Optional[List[str]] = None,
               sort_by: Optional[List[Dict]] = None) -> Dict:
        """
        Search documents in an index.

        Args:
            index_id: The index ID to search
            query: The search query string
            max_hits: Maximum number of hits to return
            start_offset: Offset for pagination
            search_fields: List of fields to search in
            sort_by: Sorting specifications
        """
        params = {
            "query": query,
            "max_hits": max_hits,
            "start_offset": start_offset
        }

        if search_fields:
            params["search_fields"] = search_fields

        if sort_by:
            params["sort_by"] = sort_by

        return self._request("POST", f"/api/v1/{index_id}/search", json=params)

    # Health check
    def health(self) -> Dict:
        """Check the health status of the Quickwit server."""
        return self._request("GET", "/health")

    # Metrics
    def metrics(self) -> str:
        """Get Quickwit metrics in Prometheus format."""
        url = f"{self.base_url}/metrics"
        response = self.session.get(url)
        response.raise_for_status()
        return response.text

    def __del__(self):
        """Close the session when the client is destroyed."""
        self.session.close()


# Example usage
if __name__ == "__main__":
    client = QuickwitClient()

    # Create an index
    index_config = {
        "version": "0.4",
        "index_id": "my-index",
        "doc_mapping": {
            "field_mappings": [
                {"name": "id", "type": "text", "tokenizer": "raw"},
                {"name": "content", "type": "text"}
            ],
            "timestamp_field": "timestamp"
        }
    }

    # Example operations
    # client.create_index(index_config)
    # client.ingest("my-index", [{"id": "1", "content": "Example document"}])
    # search_results = client.search("my-index", "example")
    # print(search_results)
