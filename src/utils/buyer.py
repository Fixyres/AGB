from typing import List, Tuple, Dict
from pyrogram import Client
from pyrogram.errors import RPCError

from src.utils.notifications import NotificationManager
from src.utils.log import log
from src.utils.config import Config


class GiftPurchaser:
    def __init__(self, cfg: Config, notifier: NotificationManager):
        self.cfg = cfg
        self.notifier = notifier

    async def purchase_all(self, app: Client, gifts: List[Tuple[int, dict]]):
        balance = await app.get_stars_balance()
        total_bought = 0

        for rule_index, (price_range, supply_limit, gift_count, recipient) in enumerate(self.cfg.gift_purchase_rules, start=1):
            needed = gift_count
            filtered_gifts = [
                (gift_id, gift) for gift_id, gift in gifts
                if price_range[0] <= gift.get("price", 0) <= price_range[1]
                and gift.get("total_amount", float("inf")) <= supply_limit
                and not gift.get("is_sold_out", False)
            ]

            if not filtered_gifts:
                log(f"Rule #{rule_index}: No suitable gifts found. Skipping.", level="INFO")
                continue

            filtered_gifts.sort(key=lambda x: x[1].get("price", 0), reverse=True)

            for gift_id, gift in filtered_gifts:
                price = gift.get("price", 0)
                max_affordable = min(needed, balance // price)
                if max_affordable <= 0:
                    continue

                for _ in range(max_affordable):
                    try:
                        await app.send_gift(
                            chat_id=recipient,
                            gift_id=gift_id,
                            hide_my_name=self.cfg.hide_sender_name
                        )
                        balance -= price
                        total_bought += 1
                        needed -= 1

                        await self.notifier.notify_purchase(
                            gift_id=gift_id,
                            current=gift_count - needed,
                            total=gift_count,
                            price=price,
                            remaining=balance,
                            recipient=recipient,
                            rule_index=rule_index,
                        )

                        if needed == 0:
                            break
                    except RPCError as ex:
                        await self.notifier.notify_error(gift_id=gift_id, error=ex)
                        break

                if needed == 0:
                    break

            if needed > 0:
                min_price = min((gift.get("price", float("inf")) for _, gift in filtered_gifts), default=0)
                remaining_cost = needed * min_price if min_price != float("inf") else 0
                await self.notifier.notify_partial_purchase(
                    gift_id=-1,
                    requested=gift_count,
                    purchased=gift_count - needed,
                    remaining=remaining_cost,
                    balance=balance,
                    recipient=recipient,
                    rule_index=rule_index,
                )
                log(f"Rule #{rule_index}: Bought {gift_count - needed} out of {gift_count} gifts due to insufficient balance.", level="WARN")

            if balance <= 0:
                break

        if total_bought == 0:
            log("No gifts were purchased due to criteria or balance limits.", level="INFO")