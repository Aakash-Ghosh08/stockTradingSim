import json
import os
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Dict, Optional
import yfinance as yf

SAVE_PATH = os.path.join(os.path.dirname(__file__), "save.txt")
DEFAULT_CASH = 100000.0


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper().replace(" ", "")


def default_state() -> Dict:
    return {
        "cash": DEFAULT_CASH,
        "portfolio": {},
        "stock_prices": {},
        "stock_price_history": {},
        "transactions": [],
        "net_worth_history": [
            {
                "timestamp": now_str(),
                "net_worth": DEFAULT_CASH,
                "cash": DEFAULT_CASH,
                "portfolio_value": 0.0,
            }
        ],
        "tick_count": 0,
    }


def load_state() -> Dict:
    if os.path.exists(SAVE_PATH):
        try:
            with open(SAVE_PATH, "r", encoding="utf-8") as f:
                state = json.load(f)
                if "cash" not in state:
                    state["cash"] = DEFAULT_CASH
                if "portfolio" not in state:
                    state["portfolio"] = {}
                if "stock_prices" not in state:
                    state["stock_prices"] = {}
                if "stock_price_history" not in state:
                    state["stock_price_history"] = {}
                if "transactions" not in state:
                    state["transactions"] = []
                if "net_worth_history" not in state:
                    state["net_worth_history"] = []
                if "tick_count" not in state:
                    state["tick_count"] = 0
                return state
        except json.JSONDecodeError:
            pass
    return default_state()


def save_state(state: Dict) -> None:
    with open(SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def get_portfolio_value(state: Dict) -> float:
    portfolio_value = 0.0
    for symbol, position in state["portfolio"].items():
        price = state["stock_prices"].get(symbol, 0.0)
        shares = float(position.get("shares", 0)) if isinstance(position, dict) else float(position)
        portfolio_value += shares * float(price)
    return round(portfolio_value, 2)


def calculate_net_worth(state: Dict) -> float:
    return round(state["cash"] + get_portfolio_value(state), 2)


def calculate_gain_loss(state: Dict, symbol: str) -> float:
    symbol = normalize_symbol(symbol)
    position = state["portfolio"].get(symbol)
    if not position:
        return 0.0

    if isinstance(position, dict):
        shares = float(position.get("shares", 0.0))
        avg_cost = float(position.get("avg_cost", 0.0))
    else:
        shares = float(position)
        avg_cost = 0.0

    current_price = state["stock_prices"].get(symbol, 0.0)
    if shares <= 0:
        return 0.0
    return round((current_price - avg_cost) * shares, 2)


def fetch_live_price(symbol: str) -> Optional[float]:
    symbol = normalize_symbol(symbol)

    try:
        ticker = yf.Ticker(symbol)

        # Get the latest available close/last price
        history = ticker.history(period="1d", interval="1m")

        if history.empty:
            history = ticker.history(period="5d")

        if history.empty:
            return None

        return round(float(history["Close"].iloc[-1]), 2)

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

    quote = result[0]
    print(json.dumps(quote, indent=2))
    price = quote.get("regularMarketPrice")
    if price is None:
        price = quote.get("ask")
    if price is None:
        price = quote.get("bid")
    if price is None:
        return None
    return round(float(price), 2)


def refresh_price(state: Dict, symbol: str) -> Optional[float]:
    symbol = normalize_symbol(symbol)
    price = fetch_live_price(symbol)
    if price is None:
        price = state["stock_prices"].get(symbol)
        if price is None:
            return None
        return round(float(price), 2)

    state["stock_prices"][symbol] = price
    state["stock_price_history"].setdefault(symbol, []).append(price)
    return round(float(price), 2)


def record_net_worth_snapshot(state: Dict) -> None:
    state["tick_count"] += 1
    portfolio_value = get_portfolio_value(state)
    state["net_worth_history"].append(
        {
            "timestamp": now_str(),
            "net_worth": round(state["cash"] + portfolio_value, 2),
            "cash": round(state["cash"], 2),
            "portfolio_value": round(portfolio_value, 2),
        }
    )


def buy_stock(state: Dict, symbol: str, shares: float) -> None:
    symbol = normalize_symbol(symbol)
    if shares <= 0:
        print("Shares must be greater than zero.")
        return

    price = refresh_price(state, symbol)
    if price is None:
        print(f"Could not retrieve a live price for {symbol}.")
        return

    cost = round(price * shares, 2)
    if cost > state["cash"]:
        print(f"You cannot afford {shares} share(s) of {symbol} at ${price:.2f} each.")
        return

    state["cash"] = round(state["cash"] - cost, 2)
    existing = state["portfolio"].get(symbol)
    if isinstance(existing, dict):
        new_shares = float(existing.get("shares", 0.0)) + float(shares)
        new_avg_cost = ((float(existing.get("avg_cost", 0.0)) * float(existing.get("shares", 0.0))) + cost) / new_shares
        state["portfolio"][symbol] = {"shares": round(new_shares, 6), "avg_cost": round(new_avg_cost, 2)}
    else:
        state["portfolio"][symbol] = {"shares": round(float(existing or 0.0) + float(shares), 6), "avg_cost": round(price, 2)}
    state["transactions"].append(
        {
            "timestamp": now_str(),
            "type": "buy",
            "symbol": symbol,
            "shares": shares,
            "price": price,
            "total": cost,
        }
    )
    record_net_worth_snapshot(state)
    print(f"Bought {shares} share(s) of {symbol} at ${price:.2f} each.")


def sell_stock(state: Dict, symbol: str, shares: float) -> None:
    symbol = normalize_symbol(symbol)
    if shares <= 0:
        print("Shares must be greater than zero.")
        return

    position = state["portfolio"].get(symbol)
    if not position:
        print(f"You do not own any shares of {symbol}.")
        return

    if isinstance(position, dict):
        owned = float(position.get("shares", 0.0))
    else:
        owned = float(position)
    if owned < shares:
        print(f"You only own {owned} share(s) of {symbol}.")
        return

    price = refresh_price(state, symbol)
    if price is None:
        print(f"Could not retrieve a live price for {symbol}.")
        return

    proceeds = round(price * shares, 2)
    state["cash"] = round(state["cash"] + proceeds, 2)

    if isinstance(position, dict):
        remaining_shares = owned - shares
        if remaining_shares <= 0:
            del state["portfolio"][symbol]
        else:
            state["portfolio"][symbol] = {"shares": round(remaining_shares, 6), "avg_cost": float(position.get("avg_cost", 0.0))}
    else:
        remaining_shares = owned - shares
        if remaining_shares <= 0:
            del state["portfolio"][symbol]
        else:
            state["portfolio"][symbol] = round(remaining_shares, 6)

    state["transactions"].append(
        {
            "timestamp": now_str(),
            "type": "sell",
            "symbol": symbol,
            "shares": shares,
            "price": price,
            "total": proceeds,
        }
    )
    record_net_worth_snapshot(state)
    print(f"Sold {shares} share(s) of {symbol} at ${price:.2f} each.")


def print_portfolio(state: Dict) -> None:
    portfolio_value = get_portfolio_value(state)
    print("\nPortfolio:")
    if not state["portfolio"]:
        print("  No holdings yet.")
    else:
        for symbol, position in sorted(state["portfolio"].items()):
            if isinstance(position, dict):
                shares = float(position.get("shares", 0.0))
                avg_cost = float(position.get("avg_cost", 0.0))
            else:
                shares = float(position)
                avg_cost = 0.0
            price = state["stock_prices"].get(symbol, 0.0)
            value = round(shares * price, 2)
            gain_loss = round((price - avg_cost) * shares, 2) if avg_cost else 0.0
            print(f"  {symbol}: {shares:.6f} share(s) @ ${price:.2f} each = ${value:.2f} | gain/loss: ${gain_loss:.2f}")
    print(f"  Cash available: ${state['cash']:.2f}")
    print(f"  Portfolio value: ${portfolio_value:.2f}")
    print(f"  Net worth: ${calculate_net_worth(state):.2f}")


def print_history(state: Dict) -> None:
    print("\nNet worth history:")
    if not state["net_worth_history"]:
        print("  No history yet.")
        return
    for entry in state["net_worth_history"][-10:]:
        print(f"  {entry['timestamp']} | cash=${entry['cash']:.2f} | portfolio=${entry['portfolio_value']:.2f} | net=${entry['net_worth']:.2f}")


def print_price_check(state: Dict, symbol: Optional[str] = None) -> None:
    if symbol is None:
        print("\nCurrent stock prices:")
        if not state["portfolio"]:
            print("  No holdings yet. Use 'buy <SYMBOL> <SHARES>' to add a position.")
            return
        for sym in sorted(state["portfolio"].keys()):
            price = refresh_price(state, sym)
            if price is None:
                continue
            owned = float(state["portfolio"].get(sym, {}).get("shares", 0.0)) if isinstance(state["portfolio"].get(sym), dict) else float(state["portfolio"].get(sym, 0.0))
            print(f"  {sym}: ${price:.2f} per share. You own {owned:.6f} share(s).")
        return

    symbol = normalize_symbol(symbol)
    price = refresh_price(state, symbol)
    if price is None:
        print(f"Could not retrieve a live price for {symbol}.")
        return
    owned = float(state["portfolio"].get(symbol, {}).get("shares", 0.0)) if isinstance(state["portfolio"].get(symbol), dict) else float(state["portfolio"].get(symbol, 0.0))
    print(f"{symbol}: ${price:.2f} per share. You own {owned:.6f} share(s).")


def refresh_prices(state: Dict) -> None:
    if not state["portfolio"]:
        print("No holdings to refresh.")
        return
    print("Refreshing prices...")
    for symbol in sorted(state["portfolio"].keys()):
        price = refresh_price(state, symbol)
        if price is None:
            print(f"  Could not refresh {symbol}.")
            continue
        print(f"  {symbol}: ${price:.2f}")
    record_net_worth_snapshot(state)


def print_help() -> None:
    print("\nCommands:")
    print("  buy <SYMBOL> <SHARES>")
    print("  sell <SYMBOL> <SHARES>")
    print("  check [SYMBOL]")
    print("  portfolio")
    print("  refresh")
    print("  history")
    print("  help")
    print("  quit")
    print("  Fractional shares are supported; enter decimal amounts such as 1.25.")


def main() -> None:
    state = load_state()
    print("Virtual stock trader started.")
    print(f"Starting cash: ${state['cash']:.2f}")
    print(f"Saved state file: {SAVE_PATH}")
    print_help()

    while True:
        try:
            raw = input("\n> ").strip()
        except EOFError:
            print("\nGoodbye.")
            break

        if not raw:
            continue

        parts = raw.split()
        command = parts[0].lower()

        if command in {"quit", "exit"}:
            save_state(state)
            print("State saved. Goodbye.")
            break

        if command == "help":
            print_help()
        elif command == "buy":
            if len(parts) != 3:
                print("Usage: buy <SYMBOL> <SHARES>")
            else:
                try:
                    shares = float(parts[2])
                except ValueError:
                    print("Shares must be a number.")
                else:
                    buy_stock(state, parts[1], shares)
        elif command == "sell":
            if len(parts) != 3:
                print("Usage: sell <SYMBOL> <SHARES>")
            else:
                try:
                    shares = float(parts[2])
                except ValueError:
                    print("Shares must be a number.")
                else:
                    sell_stock(state, parts[1], shares)
        elif command == "check":
            if len(parts) == 1:
                print_price_check(state)
            elif len(parts) == 2:
                print_price_check(state, parts[1])
            else:
                print("Usage: check [SYMBOL]")
        elif command == "refresh":
            refresh_prices(state)
        elif command in {"portfolio", "status"}:
            print_portfolio(state)
        elif command in {"history", "timeline"}:
            print_history(state)
        else:
            print("Unknown command. Type 'help' to see options.")

        save_state(state)


if __name__ == "__main__":
    main()
