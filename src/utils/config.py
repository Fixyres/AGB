import sys
import re
from dataclasses import dataclass
from configparser import ConfigParser
from pathlib import Path
from typing import List, Tuple

@dataclass
class Config:
    api_id: int
    api_hash: str
    phone: str
    interval: int
    hide_sender_name: bool
    prioritize_low_supply: bool
    language: str
    data_path: Path
    gift_purchase_rules: List[Tuple[Tuple[int, int], int, int, str]]

    @staticmethod
    def load(config_path: Path = Path("config.ini")) -> "Config":
        if not config_path.exists():
            _fail("Config file not found: config.ini")

        parser = ConfigParser()
        parser.read(config_path, encoding="utf-8")

        def _get(section: str, option: str, expected_type: str):
            if not parser.has_option(section, option):
                _fail(f"Missing option: [{section}] {option}")
            value = parser.get(section, option).strip()
            if value == "":
                _fail(f"Empty value: [{section}] {option}")
            try:
                match expected_type:
                    case "int":
                        return int(value)
                    case "bool":
                        return parser.getboolean(section, option)
                    case "str":
                        return value
            except Exception:
                _fail(f"Invalid type for [{section}] {option}, expected {expected_type}")

        api_id = _get("Telegram", "api_id", "int")
        api_hash = _get("Telegram", "api_hash", "str")
        phone = _get("Telegram", "phone", "str")

        interval = _get("Bot", "interval", "int")
        hide_sender_name = _get("Bot", "hide_sender_name", "bool")
        language = _get("Bot", "lang", "str").lower()
        prioritize_low_supply = _get("Bot", "prioritize_low_supply", "bool")

        if language not in ("en", "ru"):
            _fail("Invalid language. Must be 'en' or 'ru'.")

        gift_purchase_rules: List[Tuple[Tuple[int, int], int, int, str]] = []

        if parser.has_section("Rules"):
            for key, value in parser.items("Rules"):
                parts = [x.strip() for x in value.split(",")]
                if len(parts) != 4:
                    _fail(f"Rule '{key}' must have 4 comma-separated values: price_range, supply_limit, gift_count, recipient")
                price_range_str, supply_str, count_str, recipient_rule = parts
                if not re.fullmatch(r"\d{1,9}-\d{1,9}", price_range_str):
                    _fail(f"Rule '{key}' has invalid price range format, expected 'min-max'")
                price_min, price_max = map(int, price_range_str.split("-"))
                if price_min >= price_max:
                    _fail(f"Rule '{key}' price range min must be less than max")
                try:
                    supply_limit_rule = int(supply_str)
                    gift_count_rule = int(count_str)
                except ValueError:
                    _fail(f"Rule '{key}' supply limit and gift count must be integers")
                if not recipient_rule.startswith("@"):
                    _fail(f"Rule '{key}' recipient must start with '@'")
                gift_purchase_rules.append(((price_min, price_max), supply_limit_rule, gift_count_rule, recipient_rule))

        return Config(
            api_id=api_id,
            api_hash=api_hash,
            phone=phone,
            interval=interval,
            hide_sender_name=hide_sender_name,
            prioritize_low_supply=prioritize_low_supply,
            language=language,
            data_path=Path("src/gifts.json"),
            gift_purchase_rules=gift_purchase_rules
        )

def _fail(msg: str):
    print(f"❌ config.ini error:\n→ {msg}")
    sys.exit(1)