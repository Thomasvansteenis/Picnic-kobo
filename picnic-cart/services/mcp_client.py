"""MCP Server client for Picnic API operations."""

import os
import logging
import json
from typing import Dict, Any, Optional, List

import requests

logger = logging.getLogger(__name__)

MCP_SERVER_URL = os.getenv('MCP_SERVER_URL', 'http://localhost:3000')
MCP_TIMEOUT = int(os.getenv('MCP_TIMEOUT', '30'))


class MCPClient:
    """Client for communicating with the Picnic MCP Server."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or MCP_SERVER_URL

    def call_tool(self, tool_name: str, arguments: Dict = None) -> Any:
        """Call an MCP tool and return the result."""
        try:
            response = requests.post(
                f"{self.base_url}/call-tool",
                json={"name": tool_name, "arguments": arguments or {}},
                timeout=MCP_TIMEOUT
            )
            response.raise_for_status()

            data = response.json()

            # Extract result from MCP response format
            if 'content' in data and isinstance(data['content'], list):
                for content in data['content']:
                    if content.get('type') == 'text':
                        try:
                            return json.loads(content['text'])
                        except json.JSONDecodeError:
                            return content['text']

            return data

        except requests.exceptions.Timeout:
            logger.error(f"MCP call timeout: {tool_name}")
            raise Exception("Request timeout")
        except requests.exceptions.RequestException as e:
            logger.error(f"MCP call error: {tool_name} - {e}")
            raise Exception(f"MCP server error: {e}")

    def health_check(self) -> bool:
        """Check if MCP server is healthy."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    # ========================================================================
    # Product Operations
    # ========================================================================

    def search_products(self, query: str) -> List[Dict]:
        """Search for products."""
        return self.call_tool('search_products', {'query': query})

    def get_categories(self) -> List[Dict]:
        """Get product categories."""
        return self.call_tool('get_categories')

    # ========================================================================
    # Cart Operations
    # ========================================================================

    def get_cart(self) -> Dict:
        """Get current shopping cart."""
        return self.call_tool('get_cart')

    def add_to_cart(self, product_id: str, count: int = 1) -> Dict:
        """Add product to cart."""
        return self.call_tool('add_to_cart', {
            'productId': product_id,
            'count': count
        })

    def remove_from_cart(self, product_id: str, count: int = 1) -> Dict:
        """Remove product from cart."""
        return self.call_tool('remove_from_cart', {
            'productId': product_id,
            'count': count
        })

    def clear_cart(self) -> Dict:
        """Clear entire cart."""
        return self.call_tool('clear_cart')

    def bulk_add_to_cart(self, items: List[Dict]) -> Dict:
        """Add multiple items to cart."""
        return self.call_tool('bulk_add_to_cart', {'items': items})

    # ========================================================================
    # Order Operations
    # ========================================================================

    def get_deliveries(self) -> List[Dict]:
        """Get all deliveries."""
        return self.call_tool('get_deliveries')

    def get_order_history(
        self,
        filter: str = 'COMPLETED',
        limit: int = 50
    ) -> Dict:
        """Get order history."""
        return self.call_tool('get_order_history', {
            'filter': filter,
            'limit': limit
        })

    def search_orders(
        self,
        query: str,
        scope: str = 'all'
    ) -> Dict:
        """Search within orders."""
        return self.call_tool('search_orders', {
            'query': query,
            'scope': scope
        })

    # ========================================================================
    # User Operations
    # ========================================================================

    def get_user(self) -> Dict:
        """Get user details."""
        return self.call_tool('get_user')

    def get_lists(self) -> List[Dict]:
        """Get user's shopping lists."""
        return self.call_tool('get_lists')


# Global instance
_mcp_client = None


def get_mcp_client() -> MCPClient:
    """Get the MCP client singleton."""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client
