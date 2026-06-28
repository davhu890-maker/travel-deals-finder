import sqlite3,time,logging
log=logging.getLogger("storage")
SCHEMA="""
CREATE TABLE IF NOT EXISTS seen(key TEXT PRIMARY KEY,origin TEXT,price REAL NOT NULL,peak_price REAL NOT NULL,notified_price REAL NOT NULL,notify_count INTEGER NOT NULL DEFAULT 0,first_seen REAL NOT NULL,last_seen REAL NOT NULL,stars INTEGER DEFAULT 0,beach_distance INTEGER,beach_line INTEGER DEFAULT 0,private_beach BOOLEAN DEFAULT 0,country TEXT,resort TEXT);
CREATE TABLE IF NOT EXISTS price_history(id INTEGER PRIMARY KEY AUTOINCREMENT,key TEXT NOT NULL,origin TEXT,price REAL NOT NULL,was_notified INTEGER NOT NULL DEFAULT 0,seen_at REAL NOT NULL,country TEXT,resort TEXT);
CREATE INDEX IF NOT EXISTS idx_history_key ON price_history(key);
CREATE INDEX IF NOT EXISTS idx_history_seen_at ON price_history(seen_at);
CREATE VIEW IF NOT EXISTS route_stats AS SELECT h.key,s.origin,s.country,s.resort,COUNT(*) AS observations,ROUND(AVG(h.price),0) AS avg_price,ROUND(MIN(h.price),0) AS min_price,ROUND(MAX(h.price),0) AS max_price,ROUND(MAX(h.price)-MIN(h.price),0) AS price_range,ROUND((1.0-MIN(h.price)/MAX(h.price))*100,1) AS max_drop_pct,SUM(h.was_notified) AS notify_count,datetime(MIN(h.seen_at),'unixepoch') AS first_seen,datetime(MAX(h.seen_at),'unixepoch') AS last_seen,ROUND(s.price,0) AS current_price,ROUND(s.peak_price,0) AS current_peak,ROUND(s.notified_price,0) AS last_notified_price,s.stars,s.beach_distance,s.beach_line,s.private_beach FROM price_history h LEFT JOIN seen s ON s.key=h.key GROUP BY h.key;
"""
class Storage:
    def __init__(self,path="deals.db"):
        self.path=path
        con=sqlite3.connect(path)
        con.executescript(SCHEMA)
        self._migrate(con)
        con.close()
    def _migrate(self,con):
        cols={r[1] for r in con.execute("PRAGMA table_info(seen)")}
        if"peak_price"not in cols:
            con.execute("ALTER TABLE seen ADD COLUMN peak_price REAL;")
            con.execute("UPDATE seen SET peak_price=notified_price WHERE peak_price IS NULL")
            con.commit()
            log.info("migrate peak_price")
        for col,defn in [("origin","TEXT"),("notify_count","INTEGER NOT NULL DEFAULT 0"),("stars","INTEGER DEFAULT 0"),("beach_distance","INTEGER"),("beach_line","INTEGER DEFAULT 0"),("private_beach","BOOLEAN DEFAULT 0"),("country","TEXT"),("resort","TEXT")]:
            if col not in cols:
                con.execute(f"ALTER TABLE seen ADD COLUMN {col} {defn}")
                con.commit()
                log.info("migrate seen.%s",col)
        hcols={r[1] for r in con.execute("PRAGMA table_info(price_history)")}
        for col,defn in [("country","TEXT"),("resort","TEXT")]:
            if col not in hcols:
                con.execute(f"ALTER TABLE price_history ADD COLUMN {col} {defn}")
                con.commit()
                log.info("migrate price_history.%s",col)
    def should_save(self,key,price,threshold_pct,origin="",country="",resort="",stars=0,beach_distance=None,beach_line=0,private_beach=False):
        now=time.time()
        con=sqlite3.connect(self.path)
        with con:
            row=con.execute("SELECT peak_price,notified_price,notify_count FROM seen WHERE key=?",(key,)).fetchone()
            if row is None:
                con.execute("INSERT INTO seen(key,origin,price,peak_price,notified_price,notify_count,first_seen,last_seen,stars,beach_distance,beach_line,private_beach,country,resort) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(key,origin,price,price,price,1,now,now,stars,beach_distance,beach_line,1 if private_beach else 0,country,resort))
                con.execute("INSERT INTO price_history(key,origin,price,was_notified,seen_at,country,resort) VALUES(?,?,?,?,?,?,?)",(key,origin,price,1,now,country,resort))
                return True
            peak,notified,notify_count=row
            if price<=peak*(1-threshold_pct/100):
                con.execute("UPDATE seen SET price=?,peak_price=?,notified_price=?,notify_count=?,origin=?,last_seen=?,stars=?,beach_distance=?,beach_line=?,private_beach=?,country=?,resort=? WHERE key=?",(price,price,price,notify_count+1,origin,now,stars,beach_distance,beach_line,1 if private_beach else 0,country,resort,key))
                con.execute("INSERT INTO price_history(key,origin,price,was_notified,seen_at,country,resort) VALUES(?,?,?,?,?,?,?)",(key,origin,price,1,now,country,resort))
                return True
            new_peak=max(peak,price)
            con.execute("UPDATE seen SET price=?,peak_price=?,origin=?,last_seen=?,stars=?,beach_distance=?,beach_line=?,private_beach=?,country=?,resort=? WHERE key=?",(price,new_peak,origin,now,stars,beach_distance,beach_line,1 if private_beach else 0,country,resort,key))
            con.execute("INSERT INTO price_history(key,origin,price,was_notified,seen_at,country,resort) VALUES(?,?,?,?,?,?,?)",(key,origin,price,0,now,country,resort))
            return False
    def cleanup(self,days=30):
        cutoff=time.time()-days*86400
        con=sqlite3.connect(self.path)
        with con:
            old=[r[0] for r in con.execute("SELECT key FROM seen WHERE last_seen<?",(cutoff,))]
            if old:
                p=",".join("?"*len(old))
                con.execute(f"DELETE FROM price_history WHERE key IN ({p})",old)
                con.execute(f"DELETE FROM seen WHERE key IN ({p})",old)
                log.info("cleaned %d",len(old))