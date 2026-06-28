#!/usr/bin/env python3
"""
flights.py
----------
Мониторинг горящих авиабилетов через Aviasales / Travelpayouts API.
Запускается вручную или по расписанию (cron).

    python flights.py
    python flights.py --config /abs/path/to/config.json

Данные сохраняются в:
    flights.db   — SQLite-дедупликация (абсолютный путь задаётся в конфиге или по умолчанию)
    flights.log  — читаемый текстовый журнал (абсолютный путь задаётся в конфиге или по умолчанию)

Конфиг (config.json) — общий для обоих скриптов.
Специфичные ключи для этого скрипта:
    travelpayouts_token      — обязательно
    origins                  — список IATA-кодов аэропортов вылета
    currency                 — валюта (по умолчанию "eur")
    max_price                — число или dict {IATA: число, "default": число}
    destination_blacklist    — список IATA-кодов направлений для пропуска
    price_drop_threshold_pct — порог повторного уведомления (по умолч. 10)
    max_results_per_origin   — сколько предложений брать на аэропорт (по умолч. 10)
    flights_db_path          — путь к БД (по умолч. "flights.db")
    flights_log_path         — путь к логу (по умолч. "flights.log")

Все относительные пути в конфиге интерпретируются относительно директории, в которой находится данный скрипт.
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from storage import Storage

# ---------------------------------------------------------------------------
# Базовый каталог скрипта (все относительные пути привязываем к нему)
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Логирование
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("flights")

# ---------------------------------------------------------------------------
# Aviasales API
# ---------------------------------------------------------------------------

BASE = "https://api.travelpayouts.com"


class AviasalesClient:
    def __init__(self, token: str, currency: str = "eur"):
        if not token or token.startswith("YOUR_"):
            raise ValueError("Заполните travelpayouts_token в config.json")
        self.token = token
        self.currency = currency
        self.session = requests.Session()

    def _get(self, path: str, params: dict):
        params["token"] = self.token
        for attempt in range(3):
            try:
                r = self.session.get(f"{BASE}{path}", params=params, timeout=15)
                if r.status_code == 429:
                    wait = 5 * (attempt + 1)
                    log.warning("Rate limit — жду %d сек.", wait)
                    time.sleep(wait)
                    continue
                r.raise_for_status()
                return r.json()
            except requests.RequestException as e:
                log.warning("Попытка %d/3 неудачна: %s", attempt + 1, e)
                time.sleep(3)
        return None

    def get_special_offers(self, origin: str) -> list:
        data = self._get("/aviasales/v3/get_special_offers", {
            "origin": origin,
            "currency": self.currency,
            "market": "ru",
            "locale": "ru",
        })
        if not data:
            return []
        return data.get("data", []) or []


# ---------------------------------------------------------------------------
# Сохранение в лог
# ---------------------------------------------------------------------------

class FlightNotifier:
    def __init__(self, log_path: str = "flights.log"):
        # Преобразуем относительный путь в абсолютный относительно SCRIPT_DIR
        p = Path(log_path)
        if not p.is_absolute():
            p = SCRIPT_DIR / p
        self.log_path = p

    def save(self, deal: dict) -> bool:
        now         = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        origin      = deal.get("origin_name") or deal.get("origin", "?")
        destination = deal.get("destination_name") or deal.get("destination", "?")
        price       = deal.get("price", "?")
        currency    = str(deal.get("currency", "")).upper()
        depart      = (deal.get("departure_at") or "")[:10]
        airline     = deal.get("airline", "")
        link        = deal.get("link", "")

        block = (
            f"[{now}] ✈️  ГОРЯЩИЙ БИЛЕТ\n"
            f"  {origin} → {destination}\n"
            + (f"  Дата вылета : {depart}\n" if depart else "")
            + f"  Цена        : {price} {currency}\n"
            + (f"  Авиакомпания: {airline}\n" if airline else "")
            + (f"  Ссылка      : {link}\n" if link else "")
            + "-" * 60 + "\n"
        )

        try:
            self.log_path.open("a", encoding="utf-8").write(block)
        except OSError as e:
            log.error("Ошибка записи в %s: %s", self.log_path, e)
            return False

        log.info("Сохранено: %s → %s  %s %s", origin, destination, price, currency)
        return True


# ---------------------------------------------------------------------------
# Основная логика
# ---------------------------------------------------------------------------

def load_config(path: Path) -> dict:
    if not path.exists():
        log.error(
            "Файл %s не найден. Скопируйте config.example.json → config.json и заполните.",
            path,
        )
        sys.exit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def max_price_for(cfg: dict, origin: str):
    mp = cfg.get("max_price")
    if isinstance(mp, dict):
        return mp.get(origin, mp.get("default"))
    return mp


def run(cfg: dict, client: AviasalesClient, storage: Storage, notifier: FlightNotifier) -> int:
    blacklist  = [b.upper() for b in cfg.get("destination_blacklist", [])]
    threshold  = cfg.get("price_drop_threshold_pct", 10)
    max_res    = cfg.get("max_results_per_origin", 10)
    currency   = cfg.get("currency", "eur")
    total      = 0

    for origin in cfg.get("origins", []):
        deals = client.get_special_offers(origin)
        if not deals:
            log.info("[%s] нет горящих предложений", origin)
            continue

        deals = sorted(deals, key=lambda d: d.get("price", 9_999_999))[:max_res]
        mp    = max_price_for(cfg, origin)

        for d in deals:
            price = d.get("price")
            dest  = (d.get("destination") or "").upper()

            if price is None:
                continue
            if dest in blacklist:
                log.debug("Пропускаю %s → в чёрном списке", dest)
                continue
            if mp and price > mp:
                continue

            key          = d.get("signature") or f"{origin}-{dest}-{d.get('departure_at')}"
            origin_name  = d.get("origin_name") or origin
            dest_name    = d.get("destination_name") or dest

            if storage.should_save(key, price, threshold,
                                   origin=origin_name, destination=dest_name):
                link = d.get("link", "")
                url  = f"https://www.aviasales.ru/search/{link.lstrip('/')}" if link else ""
                notifier.save({
                    "origin":           d.get("origin"),
                    "origin_name":      origin_name,
                    "destination":      dest,
                    "destination_name": dest_name,
                    "departure_at":     d.get("departure_at"),
                    "price":            price,
                    "currency":         currency,
                    "airline":          d.get("airline_title") or d.get("airline", ""),
                    "link":             url,
                })
                total += 1

    return total


def main():
    parser = argparse.ArgumentParser(description="Мониторинг горящих авиабилетов")
    parser.add_argument("--config", default="config.json", help="Путь к config.json")
    args = parser.parse_args()

    # Преобразуем путь к конфигу в абсолютный относительно SCRIPT_DIR
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = SCRIPT_DIR / config_path

    cfg = load_config(config_path)

    # Преобразуем пути к БД и логу в абсолютные (если они относительные)
    db_path = cfg.get("flights_db_path", "flights.db")
    p_db = Path(db_path)
    if not p_db.is_absolute():
        p_db = SCRIPT_DIR / p_db
    cfg["flights_db_path"] = str(p_db)

    log_path = cfg.get("flights_log_path", "flights.log")
    p_log = Path(log_path)
    if not p_log.is_absolute():
        p_log = SCRIPT_DIR / p_log
    cfg["flights_log_path"] = str(p_log)

    try:
        client = AviasalesClient(
            token=cfg["travelpayouts_token"],
            currency=cfg.get("currency", "eur"),
        )
    except (ValueError, KeyError) as e:
        log.error("Ошибка конфига: %s", e)
        sys.exit(1)

    storage  = Storage(cfg["flights_db_path"])
    notifier = FlightNotifier(cfg["flights_log_path"])

    total = run(cfg, client, storage, notifier)
    log.info("Готово. Новых записей: %d", total)
    storage.cleanup()


if __name__ == "__main__":
    main()