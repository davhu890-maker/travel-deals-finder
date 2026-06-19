#!/usr/bin/env python3
"""
Альтернативный скрипт для запуска с использованием APScheduler
Для более точного расписания и лучшей интеграции с системой
"""

import asyncio
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import main

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_search():
    """Запуск поиска в отдельном потоке"""
    try:
        finder = main.TravelDealsFinder('config.json')
        asyncio.run(finder.run_search())
    except Exception as e:
        logger.error(f"Error in scheduled search: {e}")

def start_scheduler(interval_minutes: int = 60):
    """Запуск планировщика"""
    scheduler = BackgroundScheduler()
    
    # Добавляем задачу
    scheduler.add_job(
        run_search,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id='travel_deals_search',
        name='Travel Deals Search',
        misfire_grace_time=15
    )
    
    scheduler.start()
    logger.info(f"Scheduler started with interval {interval_minutes} minutes")
    
    try:
        while True:
            asyncio.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown()
        logger.info("Scheduler stopped")

if __name__ == '__main__':
    start_scheduler(60)
