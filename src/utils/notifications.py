from typing import Dict, List, Literal
from pyrogram import Client
from src.utils.config import Config


class NotificationManager:
    _translations = {
        "startup": {
            "en": (
                "<b>▶️ AGB started!</b>\n\n"
                "<b>Language:</b> <code>{language}</code>\n"
                "<b>Current balance:</b> <code>{balance} ⭐</code>\n\n"
                "<b>Gifts purchase logic:</b>\n"
                "<blockquote>{logic}</blockquote>\n\n"
                "💡 <b>Gifts outside the set criteria will be skipped!</b>\n\n"
                "<b>Made by @Fixyres | Donate: t.me/send?start=IVAeSi7A07xd</b>"
            ),
            "ru": (
                "<b>▶️ AGB запущен!</b>\n\n"
                "<b>Язык:</b> <code>{language}</code>\n"
                "<b>Текущий баланс:</b> <code>{balance} ⭐</code>\n\n"
                "<b>Логика покупки подарков:</b>\n"
                "<blockquote>{logic}</blockquote>\n\n"
                "💡 <b>Подарки вне заданных критериев будут пропущены!</b>\n\n"
                "<b>Made by @Fixyres | Donate: t.me/send?start=IVAeSi7A07xd</b>"
            ),
        },
        "new_gift": {
            "en": "🎁 <b>New Gift!</b>\n<b>ID:</b> <code>{id}</code>\n<b>Limited:</b> {limited}\n<b>Supply:</b> {supply}",
            "ru": "🎁 <b>Новый подарок!</b>\n<b>ID:</b> <code>{id}</code>\n<b>Ограниченный:</b> {limited}\n<b>Остаток:</b> {supply}",
        },
        "purchase": {
            "en": "🎉 Purchased gift <code>{gift_id}</code> ({current}/{total}) for {price} ⭐️. Remaining balance: {remaining} ⭐️. Recipient: {recipient}. Rule #{rule_index}",
            "ru": "🎉 Куплен подарок <code>{gift_id}</code> ({current}/{total}) за {price} ⭐️. Остаток баланса: {remaining} ⭐️. Получатель: {recipient}. Правило №{rule_index}"
        },
        "error": {
            "en": "❌ Error purchasing gift <code>{gift_id}</code>: {error}",
            "ru": "❌ Ошибка при покупке подарка <code>{gift_id}</code>: {error}"
        },
        "partial_purchase": {
            "en": "⚠️ Partial purchase for rule #{rule_index}: requested {requested}, purchased {purchased}. Missing cost: {remaining} ⭐️. Balance left: {balance} ⭐️. Recipient: {recipient}",
            "ru": "⚠️ Частичная покупка по правилу №{rule_index}: запрошено {requested}, куплено {purchased}. Не хватает на сумму: {remaining} ⭐️. Остаток баланса: {balance} ⭐️. Получатель: {recipient}"
        },
        "summary": {
            "en": (
                "⚠️ Skipped:\n"
                "• 🛑 Sold out: {sold_out_count}\n"
                "• ♾️ Unlimited: {non_limited_count}\n"
                "• 🔻 Not upgradable: {non_upgradable_count}"
            ),
            "ru": (
                "⚠️ Пропущено:\n"
                "• 🛑 Распродано: {sold_out_count}\n"
                "• ♾️ Неограниченные: {non_limited_count}\n"
                "• 🔻 Без улучшения: {non_upgradable_count}"
            ),
        },
    }

    def __init__(self, app: Client, chat_id: str = "me") -> None:
        self.app = app
        self.config = Config.load()
        self.chat_id = chat_id
        self.language: Literal["en", "ru"] = self.config.language if self.config.language in ("en", "ru") else "en"

    def _format(self, key: str, **kwargs) -> str:
        template = self._translations.get(key, {}).get(self.language)
        if template is None:
            raise ValueError(f"Translation key '{key}' not found for language '{self.language}'")
        return template.format(**kwargs)

    async def notify_purchase(self, gift_id: int, current: int, total: int, price: int, remaining: int, recipient: str, rule_index: int) -> None:
        message = self._format(
            "purchase",
            gift_id=gift_id,
            current=current,
            total=total,
            price=price,
            remaining=remaining,
            recipient=recipient,
            rule_index=rule_index,
        )
        await self.app.send_message(self.chat_id, message)

    async def notify_error(self, gift_id: int, error: Exception) -> None:
        message = self._format(
            "error",
            gift_id=gift_id,
            error=str(error),
        )
        await self.app.send_message(self.chat_id, message)

    async def notify_partial_purchase(self, gift_id: int, requested: int, purchased: int, remaining: int, balance: int, recipient: str, rule_index: int) -> None:
        message = self._format(
            "partial_purchase",
            requested=requested,
            purchased=purchased,
            remaining=remaining,
            balance=balance,
            recipient=recipient,
            rule_index=rule_index,
            gift_id=gift_id,
        )
        await self.app.send_message(self.chat_id, message)

    async def notify_startup(self) -> None:
        logic = []
        for i, (price_range, supply_limit, gift_count, recipient) in enumerate(self.config.gift_purchase_rules, start=1):
            low, high = price_range
            logic.append(f"Rule {i}: {low}-{high} ⭐ (supply ≤ {supply_limit}) x {gift_count} → {recipient}")

        message = self._format(
            "startup",
            language="Русский" if self.language == "ru" else "English",
            balance=await self.app.get_stars_balance(),
            logic="\n".join(logic),
        )
        await self.app.send_message(self.chat_id, message)

    async def notify_new_gift(self, gift: Dict) -> None:
        message = self._format(
            "new_gift",
            id=gift.get("id", "N/A"),
            limited="Да" if gift.get("is_limited") else "Нет" if self.language == "ru" else
                    "Yes" if gift.get("is_limited") else "No",
            supply=gift.get("total_amount", "∞"),
        )
        await self.app.send_message(self.chat_id, message)

    async def notify_summary(self, stats: Dict[str, int]) -> None:
        if not any(stats.values()):
            return
        message = self._format(
            "summary",
            sold_out_count=stats.get("sold_out_count", 0),
            non_limited_count=stats.get("non_limited_count", 0),
            non_upgradable_count=stats.get("non_upgradable_count", 0),
        )
        await self.app.send_message(self.chat_id, message)