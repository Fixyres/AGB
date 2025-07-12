import asyncio
from pyrogram import Client
from pathlib import Path

from src.utils.config import Config
from src.utils.detector import GiftDetector
from src.utils.notifications import NotificationManager
from src.utils.log import log
from src.utils.buyer import GiftPurchaser

BANNER = r"""

···································································
:_____/\\\\\\\\\_________/\\\\\\\\\\\\___/\\\\\\\\\\\\\___        :
: ___/\\\\\\\\\\\\\_____/\\\//////////___\/\\\/////////\\\_       :
:  __/\\\/////////\\\___/\\\______________\/\\\_______\/\\\_      :
:   _\/\\\_______\/\\\__\/\\\____/\\\\\\\__\/\\\\\\\\\\\\\\__     :
:    _\/\\\\\\\\\\\\\\\__\/\\\___\/////\\\__\/\\\/////////\\\_    :
:     _\/\\\/////////\\\__\/\\\_______\/\\\__\/\\\_______\/\\\_   :
:      _\/\\\_______\/\\\__\/\\\_______\/\\\__\/\\\_______\/\\\_  :
:       _\/\\\_______\/\\\__\//\\\\\\\\\\\\/___\/\\\\\\\\\\\\\/__ :
:        _\///________\///____\////////////_____\/////////////____:
···································································

<<<AGB - Auto Gifts Buyer for Telegram>>>
"""

async def main() -> None:
    print(BANNER)
    cfg = Config.load()
    detector = GiftDetector(cfg.data_path, cfg.prioritize_low_supply)

    async with Client(
        name="AGB",
        api_id=cfg.api_id,
        api_hash=cfg.api_hash,
        phone_number=cfg.phone,
    ) as app:
        notifier = NotificationManager(app, chat_id="me")
        purchaser = GiftPurchaser(cfg, notifier)

        await notifier.notify_startup()

        if not Path(cfg.data_path).exists():
            current_gifts, gift_ids = await detector.fetch_current_gifts(app)
            detector.save_gift_history(list(current_gifts.values()))

        while True:
            log("Checking new gifts...", level="INFO")
            await asyncio.sleep(cfg.interval)

            current_gifts, gift_ids = await detector.fetch_current_gifts(app)
            old_gifts = detector.load_gift_history()
            new_gifts = {gid: gift for gid, gift in current_gifts.items() if gid not in old_gifts}

            if new_gifts:
                summary = {'sold_out_count': 0, 'non_limited_count': 0, 'non_upgradable_count': 0}
                for gift in new_gifts.values():
                    for key, val in detector.categorize_skips(gift).items():
                        summary[key] += val

                prioritized = detector.prioritize(new_gifts, gift_ids)
                print(prioritized)
        
                await purchaser.purchase_all(app, prioritized)

                await notifier.notify_summary(summary)

            detector.save_gift_history(list(current_gifts.values()))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("Graceful shutdown requested. Exiting...", level="INFO")