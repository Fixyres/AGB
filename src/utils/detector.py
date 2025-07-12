import json
from pathlib import Path
from typing import Dict, List, Tuple
from pyrogram import Client, types


class GiftDetector:
    def __init__(self, data_path: Path, prioritize_low: bool) -> None:
        self.data_path = data_path
        self.prioritize_low = prioritize_low

    def load_gift_history(self) -> Dict[int, dict]:
        if not self.data_path.exists():
            return {}
        try:
            with self.data_path.open("r", encoding="utf-8") as f:
                return {gift["id"]: gift for gift in json.load(f)}
        except Exception:
            return {}

    def save_gift_history(self, gifts: List[dict]) -> None:
        with self.data_path.open("w", encoding="utf-8") as f:
            json.dump(gifts, f, indent=4, ensure_ascii=False, default=types.Object.default)

    async def fetch_current_gifts(self, app: Client) -> Tuple[Dict[int, dict], List[int]]:
        raw_gifts = await app.get_available_gifts()
        gifts = [json.loads(json.dumps(gift, default=types.Object.default, ensure_ascii=False)) for gift in raw_gifts]
        gift_dict = {gift["id"]: gift for gift in gifts}
        return gift_dict, list(gift_dict.keys())

    @staticmethod
    def categorize_skips(gift: dict) -> Dict[str, int]:
        return {
            "sold_out_count": int(gift.get("is_sold_out", False)),
            "non_limited_count": int(not gift.get("is_limited", False)),
            "non_upgradable_count": int("upgrade_price" not in gift),
        }

    def prioritize(self, gifts: Dict[int, dict], gift_ids: List[int]) -> List[Tuple[int, dict]]:
        for gid, gift in gifts.items():
            gift["position"] = len(gift_ids) - gift_ids.index(gid)

        sorted_gifts = sorted(gifts.items(), key=lambda x: x[1]["position"])

        if self.prioritize_low:
            return sorted(
                sorted_gifts,
                key=lambda x: (
                    x[1].get("total_amount", float("inf")) if x[1].get("is_limited") else float("inf"),
                    x[1]["position"]
                )
            )
        return sorted_gifts