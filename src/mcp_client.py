# -*- coding: utf-8 -*-
"""
CMC Agent Hub integration for BNB Hack 2026
============================================

This module provides a client for the CoinMarketCap Agent Hub MCP Server.

Architecture:
    In production, the agent connects to CMC's MCP (Model Context Protocol)
    endpoint, which exposes cryptocurrency tools as structured MCP resources.
    This enables AI agents to programmatically access market data, trending
    coins, Fear & Greed index, and more via a standardized protocol.

    For the hackathon submission, this module implements a REST API fallback
    that mirrors the MCP tool interface. When the MCP server is available,
    the client will prefer it; otherwise, it gracefully falls back to
    direct REST API calls using the same CMC_API_KEY.

MCP Server Setup (when available):
    The CMC MCP Server can be started via:
        npx @anthropic-ai/mcp coinmarketcap

    Or configured in the agent's MCP settings to auto-connect.

Available MCP Tools (mapped from CMC Agent Hub):
    - get_crypto_quotes_latest  → Crypto price quotes
    - get_fear_greed_index      → Market sentiment
    - get_trending_cryptos      → Social trending coins
    - get_global_metrics        → Global market stats

Author: Rony Costa (@Fealtycripto)
License: MIT
"""

import os
import requests
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

CMC_API_KEY = os.getenv("CMC_API_KEY", "")
CMC_BASE_URL = "https://pro-api.coinmarketcap.com"
HEADERS = {
    "X-CMC_PRO_API_KEY": CMC_API_KEY,
    "Accept": "application/json",
}


class CMCMCPClient:
    """
    CoinMarketCap MCP Client — Agent Hub Integration.

    This class wraps CMC Agent Hub tools using the MCP protocol pattern.
    In the current implementation, methods fall back to REST API calls.
    In the final version, the agent will connect via MCP protocol to
    CMC's hosted MCP server for real-time tool invocation.

    MCP Protocol Flow (target architecture):
        1. Agent discovers available tools via MCP handshake
        2. Agent calls tools by name with structured parameters
        3. MCP server executes the tool and returns structured response
        4. Agent processes the response in its reasoning loop

    REST Fallback Flow (current implementation):
        1. Methods call CMC REST API directly using API key
        2. Response is parsed and returned in the same format
        3. Seamless migration to MCP when server is deployed

    Usage:
        client = CMCMCPClient()
        quotes = client.get_crypto_quotes("BTC")
        fg_value, fg_label = client.get_fear_greed()
        trending = client.get_trending()
    """

    def __init__(self, mcp_endpoint: Optional[str] = None):
        """
        Initialize the CMC MCP Client.

        Args:
            mcp_endpoint: Optional MCP server URL. When provided, the client
                will attempt to connect via MCP protocol first. If None or
                unreachable, falls back to REST API.

        In the final version, mcp_endpoint would be something like:
            "mcp://coinmarketcap.com/agent-hub"
        """
        self.mcp_endpoint = mcp_endpoint
        self.api_key = CMC_API_KEY
        self.base_url = CMC_BASE_URL
        self.headers = HEADERS.copy()
        self._mcp_connected = False

        if mcp_endpoint:
            self._try_mcp_connect()

    def _try_mcp_connect(self) -> bool:
        """
        Attempts to establish MCP connection with the CMC server.

        In the final implementation, this would:
        1. Send MCP initialize request
        2. Negotiate capabilities
        3. List available tools
        4. Cache tool schemas for validation

        Returns:
            bool: True if MCP connection established, False otherwise.
        """
        # TODO: Implement MCP protocol handshake when CMC MCP server is live
        # For now, always falls back to REST API
        self._mcp_connected = False
        return False

    def get_crypto_quotes(self, symbol: str = "BTC") -> dict:
        """
        MCP Tool: get_crypto_quotes_latest

        Fetches the latest price quote for a cryptocurrency.

        In MCP mode, this would call:
            tool_name: "get_crypto_quotes_latest"
            params: {"symbol": symbol, "convert": "USD"}

        Args:
            symbol: Cryptocurrency ticker symbol (e.g., "BTC", "ETH", "BNB")

        Returns:
            dict: Quote data including price, volume, market_cap, percent_change.
                  Returns empty dict on failure.

        Example response:
            {
                "symbol": "BTC",
                "price": 107234.56,
                "volume_24h": 28500000000,
                "market_cap": 2130000000000,
                "percent_change_24h": 2.34,
                "percent_change_7d": -1.45,
                "last_updated": "2026-06-09T23:00:00Z"
            }
        """
        if self._mcp_connected:
            return self._mcp_call("get_crypto_quotes_latest", {
                "symbol": symbol,
                "convert": "USD",
            })

        # REST API fallback
        url = f"{self.base_url}/v1/cryptocurrency/quotes/latest"
        params = {"symbol": symbol.upper(), "convert": "USD"}
        try:
            r = requests.get(url, headers=self.headers, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            coin_data = data["data"][symbol.upper()]
            quote = coin_data["quote"]["USD"]
            return {
                "symbol": symbol.upper(),
                "price": quote.get("price", 0),
                "volume_24h": quote.get("volume_24h", 0),
                "market_cap": quote.get("market_cap", 0),
                "percent_change_24h": quote.get("percent_change_24h", 0),
                "percent_change_7d": quote.get("percent_change_7d", 0),
                "last_updated": quote.get("last_updated", ""),
            }
        except Exception as e:
            print(f"[WARN] CMCMCPClient.get_crypto_quotes({symbol}) failed: {e}")
            return {}

    def get_fear_greed(self) -> tuple:
        """
        MCP Tool: get_fear_greed_index

        Fetches the current Fear & Greed Index value and classification.

        In MCP mode, this would call:
            tool_name: "get_fear_greed_index"
            params: {}

        Returns:
            tuple: (value: int, label: str)
                - value: 0-100 (0 = Extreme Fear, 100 = Extreme Greed)
                - label: "Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"
                - Returns (50, "Neutral") on failure.

        Note:
            Uses Alternative.me as primary source (more reliable than CMC
            global-metrics on Basic plan which may not include F&G data).
        """
        if self._mcp_connected:
            result = self._mcp_call("get_fear_greed_index", {})
            return (result.get("value", 50), result.get("label", "Neutral"))

        # REST API fallback — Alternative.me (more reliable for F&G)
        try:
            r = requests.get(
                "https://api.alternative.me/fng/?limit=1&format=json",
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
            value = int(data["data"][0]["value"])
            label = self._fg_label(value)
            return (value, label)
        except Exception as e:
            print(f"[WARN] CMCMCPClient.get_fear_greed() failed: {e}")
            return (50, "Neutral")

    def get_trending(self) -> list:
        """
        MCP Tool: get_trending_cryptocurrencies

        Fetches the list of currently trending cryptocurrencies from CMC.

        In MCP mode, this would call:
            tool_name: "get_trending_cryptocurrencies"
            params: {"limit": 10}

        Returns:
            list: List of dicts with trending coin data. Each dict contains:
                - symbol (str): Coin ticker
                - name (str): Full name
                - rank (int): Trending position (1-based)
                - id (int): CMC coin ID

                Returns empty list on failure.

        Example response:
            [
                {"symbol": "BTC", "name": "Bitcoin", "rank": 1, "id": 1},
                {"symbol": "ETH", "name": "Ethereum", "rank": 2, "id": 1027},
                ...
            ]

        Note:
            The trending endpoint (/v1/cryptocurrency/trending/latest) may
            not be available on CMC Basic plan. Fails silently.
        """
        if self._mcp_connected:
            return self._mcp_call("get_trending_cryptocurrencies", {"limit": 10})

        # REST API fallback
        url = f"{self.base_url}/v1/cryptocurrency/trending/latest"
        try:
            r = requests.get(url, headers=self.headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            trending_list = data.get("data", [])

            result = []
            for i, coin in enumerate(trending_list[:10]):
                result.append({
                    "symbol": coin.get("symbol", ""),
                    "name": coin.get("name", ""),
                    "rank": i + 1,
                    "id": coin.get("id", 0),
                })
            return result
        except Exception:
            # Trending endpoint may not be available on Basic plan
            return []

    def _mcp_call(self, tool_name: str, params: dict) -> dict:
        """
        Executes an MCP tool call against the CMC MCP server.

        In the final implementation, this would:
        1. Serialize the tool call as MCP JSON-RPC
        2. Send to the MCP server endpoint
        3. Await structured response
        4. Parse and return the result

        Args:
            tool_name: Name of the MCP tool to invoke
            params: Tool parameters as a dictionary

        Returns:
            dict: Tool execution result

        TODO: Implement actual MCP protocol communication
              when CMC MCP server is deployed for BNB Hack 2026.
        """
        raise NotImplementedError(
            f"MCP protocol call to '{tool_name}' not yet implemented. "
            "Falling back to REST API."
        )

    @staticmethod
    def _fg_label(value: int) -> str:
        """Maps Fear & Greed numeric value to human-readable label."""
        if value <= 24:
            return "Extreme Fear"
        elif value <= 44:
            return "Fear"
        elif value <= 55:
            return "Neutral"
        elif value <= 74:
            return "Greed"
        else:
            return "Extreme Greed"

    def status(self) -> dict:
        """
        Returns the current client status and connection mode.

        Returns:
            dict: Status information including connection mode,
                  API key presence, and available capabilities.
        """
        return {
            "mode": "MCP" if self._mcp_connected else "REST_FALLBACK",
            "mcp_endpoint": self.mcp_endpoint,
            "mcp_connected": self._mcp_connected,
            "api_key_configured": bool(self.api_key),
            "base_url": self.base_url,
            "available_tools": [
                "get_crypto_quotes",
                "get_fear_greed",
                "get_trending",
            ],
            "project": "Zion Smart DCA v4.0",
            "hackathon": "BNB Hack 2026 — Crypto Intelligence Agent Track",
        }


# ─── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  CMC MCP Client — Integration Test")
    print("=" * 60)

    client = CMCMCPClient()
    print(f"\nClient Status: {client.status()}")

    print("\n--- get_crypto_quotes('BTC') ---")
    quotes = client.get_crypto_quotes("BTC")
    if quotes:
        print(f"  BTC Price: ${quotes.get('price', 0):,.2f}")
        print(f"  24h Change: {quotes.get('percent_change_24h', 0):.2f}%")
        print(f"  Market Cap: ${quotes.get('market_cap', 0)/1e12:.2f}T")
    else:
        print("  [No data]")

    print("\n--- get_fear_greed() ---")
    fg_val, fg_label = client.get_fear_greed()
    print(f"  Fear & Greed: {fg_val} — {fg_label}")

    print("\n--- get_trending() ---")
    trending = client.get_trending()
    if trending:
        for coin in trending[:5]:
            print(f"  #{coin['rank']} {coin['symbol']} ({coin['name']})")
    else:
        print("  [No trending data — endpoint may require higher API tier]")

    print("\n" + "=" * 60)
