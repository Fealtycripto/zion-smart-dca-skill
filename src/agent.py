# -*- coding: utf-8 -*-
"""
Zion Smart DCA — BNB AI Agent SDK Integration
ERC-8004 On-chain Identity Registration

BNB Hack 2026 | Track 2: Crypto Intelligence Agent
Special Prize: Best use of BNB AI Agent SDK ($2,000)

This module:
1. Defines the agent identity card (ERC-8004 metadata)
2. Registers the agent on BNB testnet (gas-free via paymaster)
3. Wraps the Zion DCA skill as a discoverable on-chain agent

Usage:
    python src/agent.py --register       # register on BNB testnet
    python src/agent.py --info           # show agent card (no wallet needed)
    python src/agent.py --run            # run skill + show agent context
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

# ─── Agent Card (ERC-8004 metadata) ──────────────────────────────────────────

AGENT_CARD = {
    "name":        "Zion Smart DCA",
    "version":     "4.0",
    "description": (
        "An intelligent Bitcoin accumulation agent (v4.0) using CoinMarketCap "
        "Fear & Greed Index, RSI signals, and halving cycle analysis to "
        "dynamically scale DCA purchases. Features 5 pillars: Cycle Reading, "
        "F&G Multiplier (0–24/25–44/45–55/56–74/75–100), double-layer Buildup "
        "confirmation, Scaling Out with dual confirmation, and Reserve First. "
        "Supports flexible frequency (daily/weekly/biweekly/monthly) and any "
        "budget amount. Includes Black Swan Protocol and fiscal efficiency layer."
    ),
    "author":      "Rony Costa (@Fealtycripto)",
    "repository":  "https://github.com/Fealtycripto/zion-smart-dca-skill",
    "license":     "MIT",
    "created_at":  "2026-06-09",
    "hackathon":   "BNB Hack 2026 — Crypto Intelligence Agent Track",
    "capabilities": [
        "btc_accumulation_strategy",
        "fear_greed_analysis",
        "rsi_signal_detection",
        "reserve_management",
        "portfolio_rebalancing",
        "backtest_execution",
        "cycle_analysis",
        "black_swan_protocol",
        "fiscal_efficiency",
        "flexible_frequency",
    ],
    "data_sources": [
        "CoinMarketCap Agent Hub (Fear & Greed, RSI, Price)",
        "Yahoo Finance (historical BTC OHLCV)",
    ],
    "input_schema": {
        "budget_usd":       {"type": "float",  "required": True,  "default": 100.0,
                             "description": "DCA base amount in USD. Any amount works: $10, $50, $100, $500."},
        "frequency":        {"type": "string", "required": False, "default": "weekly",
                             "enum": ["daily", "weekly", "biweekly", "monthly"],
                             "description": "DCA frequency — adapts to the investor's reality."},
        "btc_portfolio_pct": {"type": "float",  "required": False, "default": 0.54},
        "reserve_usd":       {"type": "float",  "required": False, "default": 0.0},
        "avg_buy_price_usd": {"type": "float",  "required": False, "default": 0.0,
                              "description": "Average buy price for Rule 5 (never sell below PM)."},
    },
    "output_schema": {
        "action":                     {"type": "string",  "enum": ["BUY", "SKIP", "SELL"]},
        "dca_type":                   {"type": "string"},
        "multiplier":                 {"type": "float"},
        "amount_usd":                 {"type": "float"},
        "btc_amount":                 {"type": "float"},
        "reserve_contribution_usd":   {"type": "float"},
        "reasoning":                  {"type": "array"},
        "rules_applied":              {"type": "array"},
        "cycle_phase":                {"type": "string"},
        "buildup_active":             {"type": "boolean"},
    },
    "performance": {
        "backtest_period":   "2021-01-01 to 2026-06-09",
        "total_weeks":       284,
        "total_return_pct":  58.3,
        "vs_standard_dca":   "+7.6pp",
        "sharpe_ratio":      1.792,
        "sortino_ratio":     4.461,
        "max_drawdown_pct":  -45.5,
        "win_rate_pct":      59.0,
        "profit_factor":     2.418,
        "buildup_events":    29,
        "live_trades":       57,
        "live_since":        "2026-02-01",
    },
    "networks": {
        "primary":  "BNB Smart Chain Testnet (chain_id: 97)",
        "mainnet":  "BNB Smart Chain (chain_id: 56)",
    },
}


def print_agent_card():
    """Prints the agent identity card in a readable format."""
    print("\n" + "=" * 60)
    print("  ZION SMART DCA — ERC-8004 AGENT IDENTITY CARD")
    print("=" * 60)
    print(f"  Name:        {AGENT_CARD['name']} v{AGENT_CARD['version']}")
    print(f"  Author:      {AGENT_CARD['author']}")
    print(f"  Network:     {AGENT_CARD['networks']['primary']}")
    print(f"  Repository:  {AGENT_CARD['repository']}")
    print(f"\n  Description:\n  {AGENT_CARD['description']}")
    print(f"\n  Capabilities:")
    for cap in AGENT_CARD["capabilities"]:
        print(f"    - {cap}")
    print(f"\n  Backtest Performance (5Y):")
    p = AGENT_CARD["performance"]
    print(f"    Total Return:    {p['total_return_pct']}%  (vs DCA: {p['vs_standard_dca']})")
    print(f"    Sharpe Ratio:    {p['sharpe_ratio']}")
    print(f"    Sortino Ratio:   {p['sortino_ratio']}")
    print(f"    Max Drawdown:    {p['max_drawdown_pct']}%")
    print(f"    Win Rate:        {p['win_rate_pct']}%")
    print(f"    Live trades:     {p['live_trades']} (since {p['live_since']})")
    print("=" * 60 + "\n")


def save_agent_card():
    """Saves agent card JSON for ERC-8004 metadata upload."""
    card_path = Path(__file__).parent.parent / "docs" / "agent_card.json"
    card_path.write_text(json.dumps(AGENT_CARD, indent=2), encoding="utf-8")
    print(f"Agent card saved to {card_path}")
    return card_path


def register_on_chain():
    """
    Registers the Zion Smart DCA agent on BNB Chain testnet via ERC-8004.
    Uses paymaster for gas-free registration on testnet.
    """
    private_key = os.getenv("AGENT_PRIVATE_KEY", "")

    # Lista de RPCs BNB testnet — tenta em ordem até um funcionar
    RPC_LIST = [
        os.getenv("BNB_RPC_URL", "https://data-seed-prebsc-1-s1.bnbchain.org:8545"),
        "https://data-seed-prebsc-1-s1.bnbchain.org:8545",
        "https://data-seed-prebsc-2-s1.bnbchain.org:8545",
        "https://bsc-testnet-rpc.publicnode.com",
    ]

    if not private_key:
        print("\n[INFO] No AGENT_PRIVATE_KEY in .env")
        print("To register on-chain, add your BNB testnet wallet private key:")
        print("  AGENT_PRIVATE_KEY=0x... (get a free testnet wallet at https://faucet.bnbchain.org)")
        print("\nShowing agent card instead:\n")
        print_agent_card()
        save_agent_card()
        return

    try:
        import bnbagent
        from bnbagent import ERC8004Agent, BNBAgentConfig, NetworkConfig, EVMWalletProvider

        print(f"\nBNBAgent SDK version: {bnbagent.__version__}")

        # Wallet provider
        wallet = EVMWalletProvider(
            password="zion-dca-hackathon",
            private_key=private_key,
            persist=False,
        )
        print(f"Wallet address: {wallet.address}")

        # ERC-8004 agent
        agent = ERC8004Agent(wallet_provider=wallet, network="bsc-testnet")

        # Gera o Agent URI (metadados on-chain)
        from bnbagent import AgentEndpoint
        agent_uri = agent.generate_agent_uri(
            name        = "Zion Smart DCA",
            description = "BTC accumulation skill using CMC Fear & Greed + RSI signals.",
            endpoints   = [AgentEndpoint(
                name     = "GitHub",
                endpoint = "https://github.com/Fealtycripto/zion-smart-dca-skill",
            )],
        )
        print(f"Agent URI generated ({len(agent_uri)} chars)")

        print("Registering agent (ERC-8004) on BNB testnet...")
        result = agent.register_agent(
            agent_uri = agent_uri,
            metadata  = [
                {"key": "version",    "value": AGENT_CARD["version"]},
                {"key": "author",     "value": AGENT_CARD["author"]},
                {"key": "hackathon",  "value": AGENT_CARD["hackathon"]},
                {"key": "repository", "value": AGENT_CARD["repository"]},
            ]
        )

        print(f"\nAgent registered successfully!")
        print(f"  Result: {result}")

        # Extrai campos do dict
        agent_id = result.get("agent_id") or result.get("tokenId") or result.get("id") or str(result)
        tx_hash  = result.get("tx_hash") or result.get("transactionHash") or result.get("hash") or "pending"

        print(f"  Agent ID:  {agent_id}")
        print(f"  TX Hash:   {tx_hash}")
        print(f"  Network:   BSC Testnet (chain 97)")
        if tx_hash and tx_hash != "pending":
            print(f"  Explorer:  https://testnet.bscscan.com/tx/{tx_hash}")

        # Salva resultado
        reg_path = Path(__file__).parent.parent / "docs" / "registration.json"
        reg_data = {
            "registered_at":  datetime.now().isoformat(),
            "wallet_address": wallet.address,
            "agent_id":       agent_id,
            "tx_hash":        tx_hash,
            "network":        "BSC Testnet (chain_id: 97)",
            "explorer":       f"https://testnet.bscscan.com/tx/{tx_hash}",
            "full_result":    result,
        }
        reg_path.write_text(json.dumps(reg_data, indent=2))
        print(f"\nRegistration saved to {reg_path}")
        return result


    except ImportError as e:
        print(f"[ERROR] BNBAgent SDK import failed: {e}")
        print("Run: pip install bnbagent")
    except Exception as e:
        print(f"[ERROR] Registration failed: {e}")
        print("Check your AGENT_PRIVATE_KEY and BNB_RPC_URL in .env")


def run_with_agent_context():
    """
    Runs the Zion Smart DCA skill wrapped with agent identity context.
    Shows how the agent presents itself when queried.
    """
    sys.path.insert(0, str(Path(__file__).parent))
    from zion_dca_skill import run_skill

    print_agent_card()
    print("Running live skill decision...\n")
    run_skill(budget=100.0, frequency="weekly", btc_pct=0.54, reserve=0.0)


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Zion Smart DCA v4.0 - BNB Agent SDK")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--register", action="store_true", help="Register agent on BNB testnet (ERC-8004)")
    g.add_argument("--info",     action="store_true", help="Show agent identity card")
    g.add_argument("--run",      action="store_true", help="Run skill with agent context")
    args = p.parse_args()

    if args.register:
        register_on_chain()
    elif args.info:
        print_agent_card()
        save_agent_card()
    elif args.run:
        run_with_agent_context()
    else:
        # Default: show card + save
        print_agent_card()
        save_agent_card()


if __name__ == "__main__":
    main()
