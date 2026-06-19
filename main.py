#!/usr/bin/env python3
"""
Travel Hot Deals Finder - автоматический поиск выгодных туров и перелетов
Скрипт отслеживает цены из нескольких точек отправления и уведомляет об лучших предложениях
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiohttp
import requests
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('travel_deals.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class Deal:
    """Класс для хранения информации о предложении"""
    departure_city: str
    departure_code: str
    destination_city: str
    destination_code: str
    price: float
    currency: str
    departure_date: str
    return_date: Optional[str]
    airline: str
    deal_type: str  # flight, tour
    url: str
    discount_percent: float
    original_price: Optional[float] = None
    found_at: str = None
    
    def __post_init__(self):
        if self.found_at is None:
            self.found_at = datetime.now().isoformat()


class FlightSearchAPI:
    """Базовый класс для поиска авиабилетов"""
    
    def __init__(self):
        self.session = None
    
    async def search_flights(self, departure_code: str, destination_code: str,
                           departure_date: str, return_date: Optional[str] = None) -> List[Deal]:
        """Поиск авиабилетов"""
        raise NotImplementedError


class KayakAPI(FlightSearchAPI):
    """Интеграция с Kayak API"""
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.base_url = "https://api.kayak.com/v1"
    
    async def search_flights(self, departure_code: str, destination_code: str,
                           departure_date: str, return_date: Optional[str] = None) -> List[Deal]:
        """Поиск на Kayak"""
        deals = []
        try:
            params = {
                'apikey': self.api_key,
                'origin': departure_code,
                'destination': destination_code,
                'depart_date': departure_date,
            }
            if return_date:
                params['return_date'] = return_date
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/search", params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # Парсинг результатов Kayak
                        for result in data.get('results', []):
                            deal = Deal(
                                departure_city=result.get('origin'),
                                departure_code=departure_code,
                                destination_city=result.get('destination'),
                                destination_code=destination_code,
                                price=result.get('price'),
                                currency=result.get('currency', 'USD'),
                                departure_date=departure_date,
                                return_date=return_date,
                                airline=result.get('airline'),
                                deal_type='flight',
                                url=result.get('url'),
                                discount_percent=result.get('discount', 0),
                                original_price=result.get('original_price')
                            )
                            deals.append(deal)
        except Exception as e:
            logger.error(f"Error searching Kayak: {e}")
        
        return deals


class SkyScanner:
    """Интеграция с SkyScanner API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.skyscanner.com"
    
    async def search_flights(self, departure_code: str, destination_code: str,
                           departure_date: str, return_date: Optional[str] = None) -> List[Deal]:
        """Поиск на SkyScanner"""
        deals = []
        try:
            headers = {'X-API-KEY': self.api_key}
            params = {
                'originPlace': departure_code,
                'destinationPlace': destination_code,
                'outboundDate': departure_date,
            }
            if return_date:
                params['inboundDate'] = return_date
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/browse/flights",
                    headers=headers,
                    params=params
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for quote in data.get('Quotes', []):
                            deal = Deal(
                                departure_city=quote.get('OutboundLeg', {}).get('DepartureAirport'),
                                departure_code=departure_code,
                                destination_city=quote.get('OutboundLeg', {}).get('ArrivalAirport'),
                                destination_code=destination_code,
                                price=quote.get('MinPrice'),
                                currency=data.get('Currency'),
                                departure_date=departure_date,
                                return_date=return_date,
                                airline=quote.get('OutboundLeg', {}).get('CarrierIds', ['Unknown'])[0],
                                deal_type='flight',
                                url=data.get('SearchUrl'),
                                discount_percent=0
                            )
                            deals.append(deal)
        except Exception as e:
            logger.error(f"Error searching SkyScanner: {e}")
        
        return deals


class TourSearchAPI:
    """Интеграция с API туроператоров"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.touroperator.com"
    
    async def search_tours(self, departure_code: str, destination_code: str,
                          departure_date: str, nights: int = 7) -> List[Deal]:
        """Поиск туров"""
        deals = []
        try:
            params = {
                'api_key': self.api_key,
                'from': departure_code,
                'to': destination_code,
                'date': departure_date,
                'nights': nights,
                'include_deals': True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/search", params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for tour in data.get('tours', []):
                            deal = Deal(
                                departure_city=departure_code,
                                departure_code=departure_code,
                                destination_city=tour.get('destination'),
                                destination_code=destination_code,
                                price=tour.get('price'),
                                currency=tour.get('currency', 'USD'),
                                departure_date=departure_date,
                                return_date=(datetime.strptime(departure_date, '%Y-%m-%d') + timedelta(nights=nights)).strftime('%Y-%m-%d'),
                                airline=tour.get('operator'),
                                deal_type='tour',
                                url=tour.get('booking_url'),
                                discount_percent=tour.get('discount', 0),
                                original_price=tour.get('original_price')
                            )
                            deals.append(deal)
        except Exception as e:
            logger.error(f"Error searching tours: {e}")
        
        return deals


class DealFilter:
    """Фильтрация и сортировка предложений"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.history_file = 'deal_history.json'
        self.load_history()
    
    def load_history(self):
        """Загрузка истории найденных предложений"""
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                self.history = json.load(f)
        else:
            self.history = []
    
    def save_history(self, deal: Deal):
        """Сохранение предложения в историю"""
        deal_dict = asdict(deal)
        self.history.append(deal_dict)
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def is_good_deal(self, deal: Deal) -> bool:
        """Проверка, является ли предложение выгодным"""
        # Минимальная скидка
        if deal.discount_percent < self.config.get('min_discount', 10):
            if deal.original_price is None or deal.original_price == 0:
                # Если нет оригинальной цены, проверяем по среднему
                avg_price = self._get_average_price(deal)
                discount = ((avg_price - deal.price) / avg_price * 100) if avg_price else 0
                if discount < self.config.get('min_discount', 10):
                    return False
        
        # Максимальная цена
        max_price = self.config.get('max_prices', {}).get(deal.destination_code, float('inf'))
        if deal.price > max_price:
            return False
        
        # Не был ли уже это предложение отправлен
        if self._was_already_sent(deal):
            return False
        
        return True
    
    def _get_average_price(self, deal: Deal) -> float:
        """Получение средней цены из истории"""
        similar_deals = [
            d for d in self.history
            if d['departure_code'] == deal.departure_code and
               d['destination_code'] == deal.destination_code and
               d['deal_type'] == deal.deal_type
        ]
        if similar_deals:
            prices = [d['price'] for d in similar_deals]
            return sum(prices) / len(prices)
        return 0
    
    def _was_already_sent(self, deal: Deal) -> bool:
        """Проверка, было ли это предложение уже отправлено"""
        for h_deal in self.history:
            if (h_deal['departure_code'] == deal.departure_code and
                h_deal['destination_code'] == deal.destination_code and
                h_deal['price'] == deal.price and
                h_deal['departure_date'] == deal.departure_date):
                return True
        return False
    
    def get_best_deals(self, deals: List[Deal], limit: int = 10) -> List[Deal]:
        """Получение лучших предложений"""
        good_deals = [d for d in deals if self.is_good_deal(d)]
        # Сортировка по цене / скидке
        sorted_deals = sorted(
            good_deals,
            key=lambda x: (x.price / (x.original_price or x.price * 1.2), -x.discount_percent)
        )
        return sorted_deals[:limit]


class NotificationService:
    """Сервис отправки уведомлений"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.email_sender = config.get('email', {}).get('sender')
        self.email_password = config.get('email', {}).get('password')
        self.email_recipients = config.get('email', {}).get('recipients', [])
        self.smtp_server = config.get('email', {}).get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = config.get('email', {}).get('smtp_port', 587)
    
    def send_email(self, deals: List[Deal], subject: str = "🎉 Найдены выгодные туры и перелеты!"):
        """Отправка уведомления по Email"""
        if not self.email_sender or not self.email_recipients:
            logger.warning("Email not configured")
            return
        
        try:
            html_content = self._generate_html(deals)
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_sender
            msg['To'] = ', '.join(self.email_recipients)
            
            msg.attach(MIMEText(html_content, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_sender, self.email_password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {self.email_recipients}")
        except Exception as e:
            logger.error(f"Error sending email: {e}")
    
    def send_telegram(self, deals: List[Deal]):
        """Отправка уведомления в Telegram"""
        telegram_token = self.config.get('telegram', {}).get('token')
        telegram_chat_id = self.config.get('telegram', {}).get('chat_id')
        
        if not telegram_token or not telegram_chat_id:
            logger.warning("Telegram not configured")
            return
        
        try:
            message = self._generate_telegram_message(deals)
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            payload = {
                'chat_id': telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            requests.post(url, json=payload)
            logger.info(f"Telegram message sent to {telegram_chat_id}")
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
    
    def send_slack(self, deals: List[Deal]):
        """Отправка уведомления в Slack"""
        slack_webhook = self.config.get('slack', {}).get('webhook_url')
        
        if not slack_webhook:
            logger.warning("Slack not configured")
            return
        
        try:
            payload = self._generate_slack_payload(deals)
            requests.post(slack_webhook, json=payload)
            logger.info("Slack message sent")
        except Exception as e:
            logger.error(f"Error sending Slack message: {e}")
    
    def _generate_html(self, deals: List[Deal]) -> str:
        """Генерация HTML для email"""
        deals_html = ""
        for deal in deals:
            deals_html += f"""
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 12px;">{deal.departure_city} → {deal.destination_city}</td>
                <td style="padding: 12px; font-weight: bold;">${deal.price} {deal.currency}</td>
                <td style="padding: 12px; color: green;">-{deal.discount_percent}%</td>
                <td style="padding: 12px;">{deal.departure_date}</td>
                <td style="padding: 12px; text-transform: capitalize;">{deal.deal_type}</td>
                <td style="padding: 12px;"><a href="{deal.url}" style="color: #0066cc;">Посмотреть</a></td>
            </tr>
            """
        
        html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th {{ background-color: #f2f2f2; padding: 12px; text-align: left; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #666; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Горячие предложения найдены!</h1>
                    <p>Рекомендуем срочно посмотреть эти выгодные туры и перелеты</p>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Маршрут</th>
                            <th>Цена</th>
                            <th>Скидка</th>
                            <th>Дата</th>
                            <th>Тип</th>
                            <th>Ссылка</th>
                        </tr>
                    </thead>
                    <tbody>
                        {deals_html}
                    </tbody>
                </table>
                <div class="footer">
                    <p>Это автоматическое сообщение от Travel Hot Deals Finder</p>
                    <p>Письмо отправлено: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _generate_telegram_message(self, deals: List[Deal]) -> str:
        """Генерация сообщения для Telegram"""
        message = "🎉 <b>Найдены выгодные туры и перелеты!</b>\n\n"
        for i, deal in enumerate(deals, 1):
            message += f"""<b>{i}. {deal.departure_city} → {deal.destination_city}</b>
💰 Цена: <b>${deal.price}</b> {deal.currency}
📉 Скидка: <b>{deal.discount_percent}%</b>
📅 Дата: {deal.departure_date}
✈️ Тип: {deal.deal_type}
🔗 <a href="{deal.url}">Смотреть предложение</a>

"""
        return message
    
    def _generate_slack_payload(self, deals: List[Deal]) -> Dict:
        """Генерация payload для Slack"""
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🎉 *Найдены выгодные туры и перелеты!*"
                }
            }
        ]
        
        for deal in deals:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{deal.departure_city} → {deal.destination_city}*\n💰 ${deal.price} {deal.currency} | 📉 -{deal.discount_percent}% | 📅 {deal.departure_date}"
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Посмотреть"
                    },
                    "url": deal.url
                }
            })
        
        return {"blocks": blocks}


class TravelDealsFinder:
    """Главный класс для поиска горячих туров и перелетов"""
    
    def __init__(self, config_file: str = 'config.json'):
        self.config = self._load_config(config_file)
        self.flight_apis = self._init_flight_apis()
        self.tour_api = self._init_tour_api()
        self.filter = DealFilter(self.config)
        self.notifier = NotificationService(self.config)
    
    def _load_config(self, config_file: str) -> Dict:
        """Загрузка конфигурации"""
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            raise FileNotFoundError(f"Config file {config_file} not found")
    
    def _init_flight_apis(self) -> Dict[str, FlightSearchAPI]:
        """Инициализация API для поиска авиабилетов"""
        apis = {}
        
        if self.config.get('kayak', {}).get('api_key'):
            apis['kayak'] = KayakAPI(self.config['kayak']['api_key'])
        
        if self.config.get('skyscanner', {}).get('api_key'):
            apis['skyscanner'] = SkyScanner(self.config['skyscanner']['api_key'])
        
        return apis
    
    def _init_tour_api(self) -> Optional[TourSearchAPI]:
        """Инициализация API для поиска туров"""
        if self.config.get('tour_operator', {}).get('api_key'):
            return TourSearchAPI(self.config['tour_operator']['api_key'])
        return None
    
    async def search_all_deals(self) -> List[Deal]:
        """Поиск всех предложений из всех источников"""
        all_deals = []
        
        departure_points = self.config.get('departure_points', [])
        destinations = self.config.get('destinations', [])
        search_date = self.config.get('search_date', (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'))
        
        tasks = []
        
        # Поиск авиабилетов
        for api_name, api in self.flight_apis.items():
            for dep in departure_points:
                for dest in destinations:
                    tasks.append(api.search_flights(
                        dep['code'], dest['code'],
                        search_date,
                        self.config.get('return_date')
                    ))
        
        # Поиск туров
        if self.tour_api:
            for dep in departure_points:
                for dest in destinations:
                    tasks.append(self.tour_api.search_tours(
                        dep['code'], dest['code'],
                        search_date,
                        self.config.get('tour_nights', 7)
                    ))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, list):
                    all_deals.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Error in search task: {result}")
        
        return all_deals
    
    async def run_search(self):
        """Запуск поиска и отправка уведомлений"""
        logger.info("Starting travel deals search...")
        
        try:
            # Поиск всех предложений
            deals = await self.search_all_deals()
            logger.info(f"Found {len(deals)} total deals")
            
            # Фильтрация лучших предложений
            best_deals = self.filter.get_best_deals(deals)
            
            if best_deals:
                logger.info(f"Found {len(best_deals)} good deals")
                
                # Сохранение в историю
                for deal in best_deals:
                    self.filter.save_history(deal)
                
                # Отправка уведомлений
                self.notifier.send_email(best_deals)
                self.notifier.send_telegram(best_deals)
                self.notifier.send_slack(best_deals)
            else:
                logger.info("No good deals found")
        
        except Exception as e:
            logger.error(f"Error during search: {e}")
    
    async def run_periodic(self, interval_minutes: int = 60):
        """Запуск периодического поиска"""
        logger.info(f"Starting periodic search with interval {interval_minutes} minutes")
        
        while True:
            await self.run_search()
            logger.info(f"Next search in {interval_minutes} minutes")
            await asyncio.sleep(interval_minutes * 60)


async def main():
    """Главная функция"""
    finder = TravelDealsFinder('config.json')
    
    # Получение интервала из переменной окружения или конфига
    interval = int(os.getenv('SEARCH_INTERVAL_MINUTES', 
                             finder.config.get('search_interval_minutes', 60)))
    
    if os.getenv('RUN_ONCE') == 'true':
        # Однократный поиск
        await finder.run_search()
    else:
        # Периодический поиск
        await finder.run_periodic(interval)


if __name__ == '__main__':
    asyncio.run(main())
