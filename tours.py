#!/usr/bin/env python3
import argparse,json,logging,os,re,sys,time
from datetime import datetime,timezone
from pathlib import Path
from storage import Storage
SCRIPT_DIR=os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(level=logging.INFO,format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log=logging.getLogger("tours")
BASE_URL="https://level.travel"; HOT_URL=BASE_URL+"/explore/{slug}/any/hot"; CARD_SEL='[class*="DesktopHotelCard_container"]'
def _parse_card(card):
    title_el=card.query_selector('[class*="HotelCardTitle_title"]')
    if not title_el: return None
    title=title_el.inner_text().strip(); href=title_el.get_attribute("href")or""; link=(BASE_URL+href)if href.startswith("/")else href
    m_price=re.search(r"offer_price=(\d+)",href); m_date=re.search(r"offer_date=([^&]+)",href)
    price=int(m_price.group(1))if m_price else None; offer_date=m_date.group(1)if m_date else""
    dates_el=card.query_selector('[class*="HotelCardDates_dates"]'); dates_str=dates_el.inner_text().strip()if dates_el else""
    m_nights=re.search(r"(\d+)\s*ноч",dates_str); nights=int(m_nights.group(1))if m_nights else None
    loc_el=card.query_selector('[class*="HotelCardLocation_text"]'); location=loc_el.inner_text().strip()if loc_el else""
    loc_parts=location.rsplit(",",1); country=loc_parts[-1].strip()if len(loc_parts)>1 else location; city=loc_parts[0].strip()if len(loc_parts)>1 else""
    rating_el=card.query_selector('[class*="HotelRating_rating"]'); reviews_el=card.query_selector('[class*="HotelRating_reviews"]')
    rating=rating_el.inner_text().strip()if rating_el else""; reviews=reviews_el.inner_text().strip()if reviews_el else""
    airline_el=card.query_selector('[class*="Label_labelText"]'); airline=airline_el.inner_text().strip()if airline_el else""
    stars_el=card.query_selector('[class*="HotelStars_container"]'); stars=len(stars_el.query_selector_all("svg"))if stars_el else 0
    beach_distance=None; beach_line=0; private_beach=False
    features=card.query_selector_all('[class*="HotelsFeature_label__fPCmY"]')
    for feat in features:
        text=feat.inner_text().strip()
        if'м' in text:
            m=re.search(r'(\d+)\s*([км]?м)',text)
            if m: beach_distance=int(m.group(1))*(1000 if m.group(2)=='км' else 1)
        if'линия' in text: beach_line=1
    labels=card.query_selector_all('[class*="HotelCardLabels_labelsContainer__"] span')
    for lbl in labels:
        if'Собственный пляж' in lbl.inner_text().strip(): private_beach=True; break
    hotel_id=None
    if href:
        m=re.search(r'/hotels/(\d+)-',href)
        if m: hotel_id=int(m.group(1))
    return{"title":title,"city":city,"country":country,"location":location,"price":price,"offer_date":offer_date,"dates_str":dates_str,"nights":nights,"rating":rating,"reviews":reviews,"airline":airline,"link":link,"stars":stars,"beach_distance":beach_distance,"beach_line":beach_line,"private_beach":private_beach,"hotel_id":hotel_id}
def _scrape_origin(page,slug,cfg,timeout_ms):
    url=HOT_URL.format(slug=slug); log.info("load %s",url)
    try: page.goto(url,wait_until="domcontentloaded",timeout=timeout_ms)
    except Exception as e: log.warning("fail %s: %s",url,e); return[]
    try: page.wait_for_selector(CARD_SEL,timeout=timeout_ms)
    except Exception: log.warning("no cards %s",url); return[]
    cards=page.query_selector_all(CARD_SEL); log.info("found %d cards on %s",len(cards),url)
    foreign_only=cfg.get("tour_foreign_only",True); bl=[b.lower() for b in cfg.get("tour_destination_blacklist",[])]
    max_price=cfg.get("tour_max_price_rub"); nights_min=cfg.get("tour_nights_min"); nights_max=cfg.get("tour_nights_max")
    res=[]
    for card in cards:
        try:
            d=_parse_card(card)
            if not d or d["price"] is None: continue
            if foreign_only and d["country"].strip().lower()=="россия": continue
            if any(b in (d["country"]+" "+d["city"]).lower() for b in bl): continue
            if max_price and d["price"]>max_price: continue
            if nights_min and d["nights"] and d["nights"]<nights_min: continue
            if nights_max and d["nights"] and d["nights"]>nights_max: continue
            res.append(d)
        except Exception as e: log.debug("parse error %s",e)
    return res
class TourNotifier:
    def __init__(self,log_path): self.log_path=Path(log_path)
    def save(self,deal):
        now=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        origin=deal.get("origin_name")or deal.get("origin","?")
        country=deal.get("country","?"); resort=deal.get("resort","?")
        price=deal.get("price","?"); depart=(deal.get("departure_at")or"")[:10]
        note=deal.get("note",""); link=deal.get("link","")
        stars=deal.get("stars",0); bd=deal.get("beach_distance"); bl=deal.get("beach_line",0); pb=deal.get("private_beach",False)
        block=f"[{now}] 🌴 ГОРЯЩИЙ ТУР (level.travel)\n  Откуда: {origin}\n  Страна: {country}\n  Курорт: {resort}\n"+(f"  Дата: {depart}\n"if depart else"")+f"  Цена: {price} RUB\n"+(f"  Звёзд: {stars}*\n"if stars else"")+(f"  Пляж: {bd} м\n"if bd is not None else"")+(f"  Линия: {bl}-я\n"if bl else"")+(f"  Собств.пляж: {'Да'if pb else'Нет'}\n")+(f"  {note}\n"if note else"")+(f"  {link}\n"if link else"")+"-"*60+"\n"
        try: self.log_path.open("a",encoding="utf-8").write(block)
        except OSError as e: log.error("write error %s",e); return False
        log.info("saved %s → %s, %s  %s RUB",origin,country,resort,price); return True
def load_config(path):
    p=Path(path)
    if not p.exists(): log.error("config %s not found",path); sys.exit(1)
    return json.loads(p.read_text(encoding="utf-8"))
def run(cfg,storage,notifier):
    origins=cfg.get("level_travel_origins",{})
    if not origins: log.error("no origins"); return 0
    try: from playwright.sync_api import sync_playwright
    except ImportError: log.error("playwright missing"); return 0
    threshold=cfg.get("price_drop_threshold_pct",10); timeout_ms=cfg.get("tour_scrape_timeout_sec",60)*1000; saved=0
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        page=browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",locale="ru-RU")
        for iata,slug in origins.items():
            try:
                deals=_scrape_origin(page,slug,cfg,timeout_ms)
                for d in deals:
                    price=d["price"]; nights_key=f"{d['nights']}н"if d['nights']else"?н"
                    key=f"tour-{slug}-{d.get('hotel_id',0)}-{d.get('offer_date','unknown')}-{nights_key}"
                    origin_name=slug.split("-")[0].capitalize()
                    if storage.should_save(key,float(price),threshold,origin=origin_name,country=d["country"],resort=d["city"],stars=d["stars"],beach_distance=d["beach_distance"],beach_line=d["beach_line"],private_beach=d["private_beach"]):
                        note_parts=[p for p in [d["dates_str"],d["airline"],(f"★ {d['rating']} ({d['reviews']})"if d["rating"]else"")]if p]
                        notifier.save({"origin":iata,"origin_name":origin_name,"country":d["country"],"resort":d["city"],"departure_at":d["offer_date"],"price":price,"note":" | ".join(note_parts),"link":d["link"],"stars":d["stars"],"beach_distance":d["beach_distance"],"beach_line":d["beach_line"],"private_beach":d["private_beach"]})
                        saved+=1
                time.sleep(3)
            except Exception: log.exception("error scraping %s",slug)
        browser.close()
    return saved
def main():
    p=argparse.ArgumentParser(); default_config=os.path.join(SCRIPT_DIR,"config.json")
    p.add_argument("--config",default=default_config); args=p.parse_args()
    cfg=load_config(args.config)
    db_path=os.path.abspath(cfg.get("tours_db_path","tours.db")if os.path.isabs(cfg.get("tours_db_path","tours.db"))else os.path.join(SCRIPT_DIR,cfg.get("tours_db_path","tours.db")))
    log_path=os.path.abspath(cfg.get("tours_log_path","tours.log")if os.path.isabs(cfg.get("tours_log_path","tours.log"))else os.path.join(SCRIPT_DIR,cfg.get("tours_log_path","tours.log")))
    log.info("DB: %s",db_path); log.info("LOG: %s",log_path)
    storage=Storage(db_path); notifier=TourNotifier(log_path)
    total=run(cfg,storage,notifier); log.info("done, saved %d",total); storage.cleanup()
if __name__=="__main__": main()