"""
TradeQuest GUI - educational RPG trading simulator.
Run: python tradequest.py
Only standard Python libraries are used.
"""
import json
import math
import os
import random
import sqlite3
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from urllib.request import Request, urlopen

DB_NAME = "tradequest_v2.db"
APP_TITLE = "TradeQuest: RPG Market Academy"
BG = "#101828"
CARD = "#182235"
CARD_2 = "#202b44"
TEXT = "#f8fafc"
MUTED = "#9ca3af"
GREEN = "#22c55e"
RED = "#ef4444"
BLUE = "#38bdf8"
YELLOW = "#facc15"
PURPLE = "#a78bfa"
ORANGE = "#fb923c"

ASSETS = [
    ("AAPL", "Apple", "Акции", 190, 0.018),
    ("MSFT", "Microsoft", "Акции", 430, 0.016),
    ("NVDA", "Nvidia", "Акции", 120, 0.032),
    ("TSLA", "Tesla", "Акции", 180, 0.038),
    ("AMZN", "Amazon", "Акции", 185, 0.020),
    ("BTC-USD", "Bitcoin", "Крипта", 65000, 0.045),
    ("ETH-USD", "Ethereum", "Крипта", 3500, 0.052),
    ("SOL-USD", "Solana", "Крипта", 150, 0.065),
]

BOT_NAMES = [
    "Артём Волков", "Мария Ким", "Илья Соколов", "Вика Орлова", "Данил Морозов",
    "Кирилл Лебедев", "София Романова", "Никита Егоров", "Анна Смирнова", "Максим Фёдоров",
    "Ева Павлова", "Тимур Алексеев", "Лера Захарова", "Глеб Новиков", "Полина Котова",
]

QUESTS = [
    ("q_register", "Вход в академию", "Создать профиль и подтвердить возраст 18+.", 20, "start"),
    ("q_first_trade", "Первая сделка", "Купить любой актив на рынке.", 35, "basic"),
    ("q_stock", "Фондовый старт", "Купить хотя бы одну акцию компании.", 40, "basic"),
    ("q_crypto", "Крипто-разведка", "Купить хотя бы одну криптовалюту.", 40, "basic"),
    ("q_two_assets", "Не всё в одну корзину", "Держать минимум 2 разных актива.", 55, "risk"),
    ("q_four_assets", "Диверсификация", "Держать минимум 4 разных актива.", 80, "risk"),
    ("q_stock_crypto", "Смешанный портфель", "Иметь одновременно акции и крипту.", 70, "risk"),
    ("q_cash_guard", "Подушка безопасности", "После покупок сохранить минимум 2000 TQ$ наличными.", 65, "risk"),
    ("q_five_trades", "Активный участник", "Совершить 5 сделок покупки или продажи.", 70, "trade"),
    ("q_ten_trades", "Ритм рынка", "Совершить 10 сделок.", 100, "trade"),
    ("q_profit_sell", "Фиксация прибыли", "Продать актив дороже средней цены покупки.", 120, "trade"),
    ("q_no_panic", "Без паники", "Иметь 3+ активов и не продавать их минимум 2 минуты.", 90, "psychology"),
    ("q_value_105", "Первые проценты", "Поднять капитал выше 10 500 TQ$.", 120, "portfolio"),
    ("q_value_112", "Портфель растёт", "Поднять капитал выше 11 200 TQ$.", 180, "portfolio"),
    ("q_value_125", "Уверенный инвестор", "Поднять капитал выше 12 500 TQ$.", 260, "portfolio"),
    ("q_level_2", "Ученик рынка", "Получить минимум 150 XP.", 80, "level"),
    ("q_level_3", "Аналитик", "Получить минимум 350 XP.", 130, "level"),
    ("q_level_4", "Риск-менеджер", "Получить минимум 650 XP.", 190, "level"),
    ("q_lessons_1", "Теория перед сделкой", "Пройти 1 учебное испытание.", 60, "study"),
    ("q_lessons_3", "Финансовая база", "Пройти 3 учебных испытания.", 130, "study"),
    ("q_lessons_5", "Глубокое обучение", "Пройти 5 учебных испытаний.", 220, "study"),
    ("q_challenge", "Экзамен TradeQuest", "Иметь 4 актива, 10 сделок, 3 урока и капитал выше 11 000 TQ$.", 350, "final"),
]

LESSONS = [
    ("Что снижает риск портфеля?", ["Покупка одного актива", "Диверсификация", "Случайные сделки"], 1),
    ("Что показывает свечной график?", ["Открытие, максимум, минимум, закрытие", "Только прибыль", "Только новости"], 0),
    ("Что лучше делать перед сделкой?", ["Игнорировать риск", "Оценить риск и размер позиции", "Купить всё на баланс"], 1),
    ("Что значит фиксировать прибыль?", ["Продать дороже покупки", "Купить дороже", "Удалить портфель"], 0),
    ("Почему нельзя учиться на реальных деньгах без подготовки?", ["Рынок всегда растёт", "Есть риск убытков", "Крипта не меняется"], 1),
]

def now_text():
    return datetime.now().strftime("%H:%M:%S")

def money(value):
    return f"{value:,.2f} TQ$".replace(",", " ")

def rank_by_xp(xp):
    ranks = [(0, "Novice Trader"), (150, "Market Student"), (350, "Chart Analyst"),
             (650, "Risk Manager"), (1000, "Portfolio Builder"), (1450, "Pro Investor")]
    result = ranks[0][1]
    for need, name in ranks:
        if xp >= need:
            result = name
    return result

def asset_info(symbol):
    for item in ASSETS:
        if item[0] == symbol:
            return item
    return (symbol, symbol, "Актив", 100, 0.02)

class Store:
    def __init__(self):
        self.db = sqlite3.connect(DB_NAME)
        self.db.row_factory = sqlite3.Row
        self.init_db()

    def init_db(self):
        cur = self.db.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY, name TEXT, age_ok INTEGER, balance REAL, xp INTEGER,
            trades INTEGER DEFAULT 0, profitable_sells INTEGER DEFAULT 0,
            lessons INTEGER DEFAULT 0, created_at TEXT, last_sell_ts REAL DEFAULT 0)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS holdings(
            owner TEXT, symbol TEXT, qty REAL, avg_price REAL, PRIMARY KEY(owner, symbol))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS candles(
            symbol TEXT, ts INTEGER, open REAL, high REAL, low REAL, close REAL, volume REAL,
            PRIMARY KEY(symbol, ts))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS events(ts REAL, text TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS bots(
            name TEXT PRIMARY KEY, balance REAL, xp INTEGER, trades INTEGER DEFAULT 0)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS quest_claims(id TEXT PRIMARY KEY)""")
        self.db.commit()
        self.seed_market()
        self.seed_bots()

    def seed_market(self):
        cur = self.db.cursor()
        for sym, _name, _kind, base, vol in ASSETS:
            count = cur.execute("SELECT COUNT(*) FROM candles WHERE symbol=?", (sym,)).fetchone()[0]
            if count >= 60:
                continue
            price = base
            start = int(time.time()) - 60 * 86400
            for i in range(60):
                op = price
                drift = random.uniform(-vol, vol)
                close = max(0.1, op * (1 + drift))
                high = max(op, close) * (1 + random.random() * vol * 0.7)
                low = min(op, close) * (1 - random.random() * vol * 0.7)
                volume = random.randint(500_000, 5_000_000) * (5 if "USD" in sym else 1)
                cur.execute("INSERT OR REPLACE INTO candles VALUES(?,?,?,?,?,?,?)",
                            (sym, start + i * 86400, op, high, low, close, volume))
                price = close
        self.db.commit()

    def seed_bots(self):
        cur = self.db.cursor()
        if cur.execute("SELECT COUNT(*) FROM bots").fetchone()[0] > 0:
            return
        for name in BOT_NAMES:
            cur.execute("INSERT INTO bots VALUES(?,?,?,?)",
                        (name, random.randint(8500, 12500), random.randint(20, 520), random.randint(0, 12)))
        self.db.commit()

    def user(self):
        return self.db.execute("SELECT * FROM users ORDER BY id LIMIT 1").fetchone()

    def create_user(self, name):
        self.db.execute("INSERT INTO users(name, age_ok, balance, xp, created_at) VALUES(?,?,?,?,?)",
                        (name, 1, 10000, 0, datetime.now().isoformat(timespec="seconds")))
        self.log(f"{name} вступил в TradeQuest Academy")
        self.db.commit()

    def log(self, text):
        self.db.execute("INSERT INTO events VALUES(?,?)", (time.time(), f"[{now_text()}] {text}"))
        self.db.commit()

    def last_events(self, limit=12):
        return [r["text"] for r in self.db.execute("SELECT text FROM events ORDER BY ts DESC LIMIT ?", (limit,))]

    def current_price(self, symbol):
        row = self.db.execute("SELECT close FROM candles WHERE symbol=? ORDER BY ts DESC LIMIT 1", (symbol,)).fetchone()
        return float(row[0]) if row else asset_info(symbol)[3]

    def candles(self, symbol, limit=48):
        rows = self.db.execute("SELECT * FROM candles WHERE symbol=? ORDER BY ts DESC LIMIT ?", (symbol, limit)).fetchall()
        return list(reversed(rows))

    def replace_candles(self, symbol, data):
        cur = self.db.cursor()
        cur.execute("DELETE FROM candles WHERE symbol=?", (symbol,))
        for item in data[-80:]:
            cur.execute("INSERT OR REPLACE INTO candles VALUES(?,?,?,?,?,?,?)", item)
        self.db.commit()

    def move_market(self):
        cur = self.db.cursor()
        for sym, _name, _kind, _base, vol in ASSETS:
            last = self.candles(sym, 1)[0]
            op = float(last["close"])
            shock = random.gauss(0, vol * 0.40)
            close = max(0.1, op * (1 + shock))
            high = max(op, close) * (1 + abs(random.gauss(0, vol * 0.14)))
            low = min(op, close) * (1 - abs(random.gauss(0, vol * 0.14)))
            volume = max(1000, float(last["volume"]) * random.uniform(0.75, 1.35))
            ts = int(time.time())
            cur.execute("INSERT OR REPLACE INTO candles VALUES(?,?,?,?,?,?,?)",
                        (sym, ts, op, high, low, close, volume))
        self.db.commit()

    def holding(self, owner, symbol):
        r = self.db.execute("SELECT * FROM holdings WHERE owner=? AND symbol=?", (owner, symbol)).fetchone()
        return r

    def holdings(self, owner):
        return self.db.execute("SELECT * FROM holdings WHERE owner=? AND qty>0 ORDER BY symbol", (owner,)).fetchall()

    def buy(self, owner, symbol, qty, bot=False):
        price = self.current_price(symbol)
        total = price * qty
        table = "bots" if bot else "users"
        key = "name" if bot else "id"
        who = owner if bot else 1
        account = self.db.execute(f"SELECT * FROM {table} WHERE {key}=?", (who,)).fetchone()
        if not account or account["balance"] < total:
            return False, "Недостаточно баланса"
        old = self.holding(owner, symbol)
        if old:
            new_qty = old["qty"] + qty
            avg = (old["avg_price"] * old["qty"] + total) / new_qty
            self.db.execute("UPDATE holdings SET qty=?, avg_price=? WHERE owner=? AND symbol=?",
                            (new_qty, avg, owner, symbol))
        else:
            self.db.execute("INSERT INTO holdings VALUES(?,?,?,?)", (owner, symbol, qty, price))
        self.db.execute(f"UPDATE {table} SET balance=balance-?, trades=trades+1 WHERE {key}=?", (total, who))
        if not bot:
            self.db.execute("UPDATE users SET xp=xp+8 WHERE id=1")
        self.db.commit()
        return True, f"Куплено {qty:g} {symbol} по {price:.2f}"

    def sell(self, owner, symbol, qty, bot=False):
        old = self.holding(owner, symbol)
        if not old or old["qty"] < qty:
            return False, "Недостаточно актива"
        price = self.current_price(symbol)
        total = price * qty
        table = "bots" if bot else "users"
        key = "name" if bot else "id"
        who = owner if bot else 1
        new_qty = old["qty"] - qty
        if new_qty <= 0.000001:
            self.db.execute("DELETE FROM holdings WHERE owner=? AND symbol=?", (owner, symbol))
        else:
            self.db.execute("UPDATE holdings SET qty=? WHERE owner=? AND symbol=?", (new_qty, owner, symbol))
        profit = price > old["avg_price"]
        extra = ", profitable_sells=profitable_sells+1" if (profit and not bot) else ""
        self.db.execute(f"UPDATE {table} SET balance=balance+?, trades=trades+1{extra} WHERE {key}=?", (total, who))
        if not bot:
            self.db.execute("UPDATE users SET xp=xp+10, last_sell_ts=? WHERE id=1", (time.time(),))
        self.db.commit()
        return True, f"Продано {qty:g} {symbol} по {price:.2f}"

    def portfolio_value(self, owner, bot=False):
        table = "bots" if bot else "users"
        key = "name" if bot else "id"
        who = owner if bot else 1
        account = self.db.execute(f"SELECT balance FROM {table} WHERE {key}=?", (who,)).fetchone()
        total = float(account["balance"]) if account else 0
        for h in self.holdings(owner):
            total += h["qty"] * self.current_price(h["symbol"])
        return total

    def claimed(self):
        return {r[0] for r in self.db.execute("SELECT id FROM quest_claims")}

    def add_xp(self, xp):
        self.db.execute("UPDATE users SET xp=xp+? WHERE id=1", (xp,))
        self.db.commit()

    def claim(self, qid, xp):
        self.db.execute("INSERT OR IGNORE INTO quest_claims VALUES(?)", (qid,))
        self.add_xp(xp)

    def bot_turns(self):
        bots = self.db.execute("SELECT * FROM bots").fetchall()
        for b in bots:
            if random.random() > 0.33:
                continue
            owner = b["name"]
            if random.random() < 0.62 or not self.holdings(owner):
                sym = random.choice(ASSETS)[0]
                price = self.current_price(sym)
                qty = round(random.uniform(0.02, 2.0) if "USD" in sym else random.uniform(1, 8), 4)
                if price * qty > b["balance"] * 0.35:
                    qty = max(0.001, (b["balance"] * random.uniform(0.04, 0.18)) / price)
                ok, _ = self.buy(owner, sym, qty, True)
                if ok:
                    self.db.execute("UPDATE bots SET xp=xp+? WHERE name=?", (random.randint(4, 15), owner))
                    self.log(f"{owner} купил {sym} и укрепил портфель")
            else:
                h = random.choice(self.holdings(owner))
                qty = max(0.0001, h["qty"] * random.uniform(0.20, 0.75))
                ok, _ = self.sell(owner, h["symbol"], qty, True)
                if ok:
                    self.db.execute("UPDATE bots SET xp=xp+? WHERE name=?", (random.randint(5, 18), owner))
                    self.log(f"{owner} продал часть {h['symbol']} после движения цены")
        self.db.commit()

class MarketFetcher:
    def __init__(self, store, callback):
        self.store = store
        self.callback = callback
        self.loading = set()
        self.last_fetch = {}

    def fetch_if_needed(self, symbol):
        if symbol in self.loading:
            return
        if time.time() - self.last_fetch.get(symbol, 0) < 180:
            return
        self.loading.add(symbol)
        threading.Thread(target=self._worker, args=(symbol,), daemon=True).start()

    def _worker(self, symbol):
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=3mo&interval=1d"
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=6) as response:
                raw = json.loads(response.read().decode("utf-8"))
            result = raw["chart"]["result"][0]
            ts = result["timestamp"]
            q = result["indicators"]["quote"][0]
            data = []
            for i, stamp in enumerate(ts):
                vals = (q["open"][i], q["high"][i], q["low"][i], q["close"][i], q.get("volume", [0]*len(ts))[i])
                if any(v is None for v in vals[:4]):
                    continue
                data.append((symbol, int(stamp), float(vals[0]), float(vals[1]), float(vals[2]), float(vals[3]), float(vals[4] or 0)))
            if len(data) >= 10:
                self.store.replace_candles(symbol, data)
                self.last_fetch[symbol] = time.time()
        except Exception:
            pass
        finally:
            self.loading.discard(symbol)
            self.callback(symbol)

class TradeQuestApp:
    def __init__(self, root):
        self.root = root
        self.store = Store()
        self.selected_symbol = ASSETS[0][0]
        self.active_tab = "Главная"
        self.fetcher = MarketFetcher(self.store, self.after_fetch)
        self.root.title(APP_TITLE)
        self.root.geometry("1180x760")
        self.root.minsize(1040, 680)
        self.root.configure(bg=BG)
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TNotebook", background=BG, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=CARD_2, foreground=TEXT, padding=(18, 10), font=("Arial", 10, "bold"))
        self.style.map("TNotebook.Tab", background=[("selected", BLUE)], foreground=[("selected", "#07111f")])
        self.style.configure("Treeview", background=CARD, foreground=TEXT, fieldbackground=CARD, rowheight=28, borderwidth=0)
        self.style.configure("Treeview.Heading", background=CARD_2, foreground=TEXT, font=("Arial", 10, "bold"))
        if self.store.user():
            self.build_main()
        else:
            self.build_register()
        self.root.after(4500, self.tick)

    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def label(self, parent, text, size=12, color=TEXT, bold=False):
        return tk.Label(parent, text=text, bg=parent["bg"], fg=color,
                        font=("Arial", size, "bold" if bold else "normal"))

    def button(self, parent, text, command, color=BLUE):
        return tk.Button(parent, text=text, command=command, bg=color, fg="#07111f",
                         activebackground="#7dd3fc", bd=0, padx=14, pady=8,
                         font=("Arial", 10, "bold"), cursor="hand2")

    def build_register(self):
        self.clear()
        box = tk.Frame(self.root, bg=CARD, padx=38, pady=34)
        box.place(relx=0.5, rely=0.5, anchor="center")
        self.label(box, "TradeQuest", 32, BLUE, True).pack(pady=(0, 4))
        self.label(box, "Образовательная RPG-игра про инвестиции", 13, MUTED).pack(pady=(0, 25))
        self.label(box, "Введите имя игрока", 12, TEXT, True).pack(anchor="w")
        name_var = tk.StringVar()
        entry = tk.Entry(box, textvariable=name_var, width=32, bg="#0b1220", fg=TEXT,
                         insertbackground=TEXT, bd=0, font=("Arial", 15))
        entry.pack(pady=10, ipady=8)
        age_var = tk.IntVar(value=0)
        hint = "Мне есть 18+. Я понимаю, что это учебная игра без реальных денег."
        check = tk.Checkbutton(box, text=hint, variable=age_var, bg=CARD, fg=MUTED,
                               selectcolor="#0b1220", activebackground=CARD,
                               activeforeground=TEXT, font=("Arial", 9), cursor="hand2")
        check.pack(pady=(10, 18), anchor="w")

        def register():
            name = name_var.get().strip()
            if len(name) < 2:
                messagebox.showwarning("Регистрация", "Введите имя минимум из 2 символов.")
                return
            if not age_var.get():
                messagebox.showwarning("18+", "Чтобы продолжить, нужно нажать кнопку подтверждения 18+.")
                return
            self.store.create_user(name[:24])
            self.build_main()
        self.button(box, "Начать игру", register, GREEN).pack(fill="x", pady=(0, 8))
        self.label(box, "Проект для обучения: это не инвестиционная рекомендация.", 9, MUTED).pack()
        entry.focus_set()

    def build_main(self):
        self.clear()
        self.header = tk.Frame(self.root, bg=BG, padx=18, pady=12)
        self.header.pack(fill="x")
        self.title_label = self.label(self.header, "TradeQuest", 22, BLUE, True)
        self.title_label.pack(side="left")
        self.profile_label = self.label(self.header, "", 11, TEXT)
        self.profile_label.pack(side="right")
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.frames = {}
        for name in ["Главная", "Рынок", "Портфель", "Квесты", "Рейтинг", "Лента"]:
            frame = tk.Frame(self.tabs, bg=BG)
            self.frames[name] = frame
            self.tabs.add(frame, text=name)
        self.tabs.bind("<<NotebookTabChanged>>", self.on_tab)
        self.build_home()
        self.build_market()
        self.build_portfolio()
        self.build_quests()
        self.build_leaderboard()
        self.build_feed()
        self.refresh_all(full=True)

    def on_tab(self, _event=None):
        self.active_tab = self.tabs.tab(self.tabs.select(), "text")
        if self.active_tab == "Рынок":
            self.fetcher.fetch_if_needed(self.selected_symbol)
            self.draw_chart()
        elif self.active_tab == "Портфель":
            self.refresh_portfolio()
        elif self.active_tab == "Квесты":
            self.refresh_quests()
        elif self.active_tab == "Рейтинг":
            self.refresh_leaderboard()
        elif self.active_tab == "Лента":
            self.refresh_feed()

    def build_home(self):
        f = self.frames["Главная"]
        top = tk.Frame(f, bg=BG)
        top.pack(fill="x", padx=10, pady=10)
        self.home_cards = []
        for title in ["Баланс", "Капитал", "XP", "Ранг"]:
            card = tk.Frame(top, bg=CARD, padx=16, pady=14)
            card.pack(side="left", fill="x", expand=True, padx=6)
            self.label(card, title, 10, MUTED, True).pack(anchor="w")
            value = self.label(card, "—", 18, TEXT, True)
            value.pack(anchor="w", pady=(6, 0))
            self.home_cards.append(value)
        info = tk.Frame(f, bg=CARD, padx=18, pady=18)
        info.pack(fill="x", padx=16, pady=10)
        self.label(info, "Учебное испытание", 18, YELLOW, True).pack(anchor="w")
        self.lesson_text = self.label(info, "Ответь на вопрос и получи XP. Вопросы помогают закрывать сложные квесты.", 12, TEXT)
        self.lesson_text.pack(anchor="w", pady=(5, 12))
        self.lesson_buttons = []
        for _ in range(3):
            b = self.button(info, "Ответ", lambda: None, CARD_2)
            b.configure(fg=TEXT, activebackground="#334155")
            b.pack(fill="x", pady=4)
            self.lesson_buttons.append(b)
        self.next_lesson()
        txt = tk.Text(f, height=10, bg=CARD, fg=TEXT, bd=0, padx=14, pady=12, wrap="word", font=("Arial", 11))
        txt.pack(fill="both", expand=True, padx=16, pady=10)
        txt.insert("end", "TradeQuest — это учебный симулятор. Цель: покупать и продавать виртуальные активы, изучать риски, закрывать квесты и обгонять других игроков в рейтинге.\n\n")
        txt.insert("end", "Новые улучшения: регистрация 18+, свечные графики, обновление графиков только на вкладке рынка, более сложные квесты и боты-трейдеры, которые выглядят как обычные участники рейтинга.")
        txt.config(state="disabled")

    def next_lesson(self):
        lesson = random.choice(LESSONS)
        self.lesson_text.config(text=lesson[0])
        for i, option in enumerate(lesson[1]):
            self.lesson_buttons[i].config(text=option, command=lambda i=i, ok=lesson[2]: self.answer_lesson(i == ok))

    def answer_lesson(self, correct):
        if correct:
            self.store.db.execute("UPDATE users SET lessons=lessons+1, xp=xp+25 WHERE id=1")
            self.store.db.commit()
            self.store.log("Игрок прошёл учебное испытание и получил 25 XP")
            messagebox.showinfo("Верно", "Правильный ответ! +25 XP")
        else:
            messagebox.showwarning("Почти", "Неверно. Попробуй другой вопрос, это нормально для обучения.")
        self.next_lesson()
        self.refresh_all()

    def build_market(self):
        f = self.frames["Рынок"]
        left = tk.Frame(f, bg=BG, width=260)
        left.pack(side="left", fill="y", padx=(12, 6), pady=12)
        right = tk.Frame(f, bg=BG)
        right.pack(side="right", fill="both", expand=True, padx=(6, 12), pady=12)
        self.label(left, "Активы", 17, BLUE, True).pack(anchor="w", pady=(0, 10))
        self.asset_list = tk.Listbox(left, bg=CARD, fg=TEXT, selectbackground=BLUE, selectforeground="#07111f",
                                     bd=0, height=16, font=("Consolas", 11), activestyle="none")
        self.asset_list.pack(fill="both", expand=True)
        for sym, name, kind, _base, _vol in ASSETS:
            self.asset_list.insert("end", f"{sym:<8} {kind:<6} {name}")
        self.asset_list.bind("<<ListboxSelect>>", self.select_asset)
        self.asset_list.selection_set(0)
        panel = tk.Frame(right, bg=CARD, padx=14, pady=12)
        panel.pack(fill="x", pady=(0, 10))
        self.market_title = self.label(panel, "", 18, TEXT, True)
        self.market_title.pack(side="left")
        self.market_status = self.label(panel, "", 10, MUTED)
        self.market_status.pack(side="right")
        self.chart = tk.Canvas(right, bg="#0b1220", highlightthickness=0, height=410)
        self.chart.pack(fill="both", expand=True)
        trade = tk.Frame(right, bg=CARD, padx=14, pady=12)
        trade.pack(fill="x", pady=(10, 0))
        self.label(trade, "Количество:", 11, MUTED, True).pack(side="left")
        self.qty_var = tk.StringVar(value="1")
        tk.Entry(trade, textvariable=self.qty_var, width=10, bg="#0b1220", fg=TEXT,
                 insertbackground=TEXT, bd=0, font=("Arial", 12)).pack(side="left", padx=10, ipady=5)
        self.button(trade, "Купить", self.buy_asset, GREEN).pack(side="left", padx=5)
        self.button(trade, "Продать", self.sell_asset, RED).pack(side="left", padx=5)
        self.button(trade, "Обновить реальные данные", self.manual_fetch, BLUE).pack(side="left", padx=5)

    def select_asset(self, _event=None):
        sel = self.asset_list.curselection()
        if not sel:
            return
        self.selected_symbol = ASSETS[sel[0]][0]
        self.fetcher.fetch_if_needed(self.selected_symbol)
        if self.active_tab == "Рынок":
            self.draw_chart()

    def manual_fetch(self):
        self.market_status.config(text="загрузка реальных данных...")
        self.fetcher.last_fetch[self.selected_symbol] = 0
        self.fetcher.fetch_if_needed(self.selected_symbol)

    def after_fetch(self, symbol):
        if self.active_tab == "Рынок" and symbol == self.selected_symbol:
            self.root.after(0, self.draw_chart)

    def draw_chart(self):
        if self.active_tab != "Рынок":
            return
        sym, name, kind, _base, _vol = asset_info(self.selected_symbol)
        data = self.store.candles(sym, 56)
        if not data:
            return
        self.market_title.config(text=f"{sym} • {name} • {kind}")
        last = float(data[-1]["close"])
        prev = float(data[-2]["close"]) if len(data) > 1 else last
        change = (last - prev) / prev * 100 if prev else 0
        source = "реальные данные или симуляция" if time.time() - self.fetcher.last_fetch.get(sym, 0) < 220 else "симуляция / кэш"
        self.market_status.config(text=f"Цена: {last:.2f} | День: {change:+.2f}% | {source}")
        c = self.chart
        c.delete("all")
        w = max(c.winfo_width(), 760)
        h = max(c.winfo_height(), 410)
        pad_l, pad_r, pad_t, pad_b = 62, 24, 30, 72
        chart_h = h - pad_t - pad_b
        vol_h = 56
        price_h = chart_h - vol_h - 18
        highs = [float(r["high"]) for r in data]
        lows = [float(r["low"]) for r in data]
        vols = [float(r["volume"]) for r in data]
        max_p, min_p = max(highs), min(lows)
        span = max(max_p - min_p, 0.01)
        max_v = max(vols) or 1
        c.create_rectangle(0, 0, w, h, fill="#0b1220", outline="")
        for i in range(6):
            y = pad_t + i * price_h / 5
            price = max_p - i * span / 5
            c.create_line(pad_l, y, w - pad_r, y, fill="#1f2a44")
            c.create_text(8, y, text=f"{price:.2f}", fill=MUTED, anchor="w", font=("Arial", 9))
        candle_w = max(5, (w - pad_l - pad_r) / len(data) * 0.55)
        def py(price):
            return pad_t + (max_p - price) / span * price_h
        def vx(i):
            return pad_l + i * (w - pad_l - pad_r) / max(1, len(data) - 1)
        ma_points = []
        closes = [float(r["close"]) for r in data]
        for i, r in enumerate(data):
            x = vx(i)
            op, hi, lo, cl = map(float, (r["open"], r["high"], r["low"], r["close"]))
            color = GREEN if cl >= op else RED
            c.create_line(x, py(hi), x, py(lo), fill=color, width=1)
            top, bottom = py(max(op, cl)), py(min(op, cl))
            if abs(bottom - top) < 2:
                bottom += 2
            c.create_rectangle(x - candle_w/2, top, x + candle_w/2, bottom, fill=color, outline=color)
            vh = (float(r["volume"]) / max_v) * vol_h
            c.create_rectangle(x - candle_w/2, h - pad_b + vol_h - vh, x + candle_w/2, h - pad_b + vol_h, fill="#334155", outline="")
            if i >= 6:
                ma = sum(closes[i-6:i+1]) / 7
                ma_points.append((x, py(ma)))
        for a, b in zip(ma_points, ma_points[1:]):
            c.create_line(a[0], a[1], b[0], b[1], fill=YELLOW, width=2)
        c.create_text(pad_l, 18, text="Свечной график + объём + скользящая средняя", fill=MUTED, anchor="w", font=("Arial", 10))
        c.create_text(w - pad_r, h - 20, text="График перерисовывается только на вкладке «Рынок»", fill=MUTED, anchor="e", font=("Arial", 9))

    def qty(self):
        try:
            q = float(self.qty_var.get().replace(",", "."))
            if q <= 0:
                raise ValueError
            return q
        except ValueError:
            messagebox.showwarning("Количество", "Введите положительное число.")
            return None

    def buy_asset(self):
        q = self.qty()
        if q is None:
            return
        ok, msg = self.store.buy("player", self.selected_symbol, q)
        messagebox.showinfo("Покупка" if ok else "Ошибка", msg)
        if ok:
            self.store.log(f"{self.store.user()['name']} купил {self.selected_symbol}")
        self.refresh_all()

    def sell_asset(self):
        q = self.qty()
        if q is None:
            return
        ok, msg = self.store.sell("player", self.selected_symbol, q)
        messagebox.showinfo("Продажа" if ok else "Ошибка", msg)
        if ok:
            self.store.log(f"{self.store.user()['name']} продал {self.selected_symbol}")
        self.refresh_all()

    def build_portfolio(self):
        f = self.frames["Портфель"]
        self.portfolio_summary = self.label(f, "", 16, TEXT, True)
        self.portfolio_summary.pack(anchor="w", padx=16, pady=12)
        cols = ("symbol", "qty", "avg", "price", "value", "pnl")
        self.portfolio_tree = ttk.Treeview(f, columns=cols, show="headings")
        for col, title in zip(cols, ["Актив", "Кол-во", "Средняя", "Цена", "Стоимость", "P/L"]):
            self.portfolio_tree.heading(col, text=title)
            self.portfolio_tree.column(col, anchor="center", width=140)
        self.portfolio_tree.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def refresh_portfolio(self):
        for item in self.portfolio_tree.get_children():
            self.portfolio_tree.delete(item)
        user = self.store.user()
        total = self.store.portfolio_value("player")
        self.portfolio_summary.config(text=f"Баланс: {money(user['balance'])}  •  Общий капитал: {money(total)}")
        for h in self.store.holdings("player"):
            price = self.store.current_price(h["symbol"])
            value = price * h["qty"]
            pnl = (price - h["avg_price"]) * h["qty"]
            self.portfolio_tree.insert("", "end", values=(h["symbol"], f"{h['qty']:.4g}", f"{h['avg_price']:.2f}", f"{price:.2f}", money(value), f"{pnl:+.2f}"))

    def build_quests(self):
        f = self.frames["Квесты"]
        top = tk.Frame(f, bg=BG)
        top.pack(fill="x", padx=16, pady=12)
        self.quest_summary = self.label(top, "", 15, TEXT, True)
        self.quest_summary.pack(side="left")
        self.button(top, "Зачесть доступные квесты", self.claim_ready, GREEN).pack(side="right")
        self.quest_box = tk.Canvas(f, bg=BG, highlightthickness=0)
        self.quest_scroll = ttk.Scrollbar(f, orient="vertical", command=self.quest_box.yview)
        self.quest_inner = tk.Frame(self.quest_box, bg=BG)
        self.quest_inner.bind("<Configure>", lambda e: self.quest_box.configure(scrollregion=self.quest_box.bbox("all")))
        self.quest_box.create_window((0, 0), window=self.quest_inner, anchor="nw")
        self.quest_box.configure(yscrollcommand=self.quest_scroll.set)
        self.quest_box.pack(side="left", fill="both", expand=True, padx=(16, 0), pady=(0, 16))
        self.quest_scroll.pack(side="right", fill="y", padx=(0, 16), pady=(0, 16))

    def quest_ready(self, qid):
        u = self.store.user()
        holds = self.store.holdings("player")
        symbols = {h["symbol"] for h in holds}
        kinds = {asset_info(s)[2] for s in symbols}
        value = self.store.portfolio_value("player")
        if qid == "q_register": return True
        if qid == "q_first_trade": return u["trades"] >= 1
        if qid == "q_stock": return "Акции" in kinds
        if qid == "q_crypto": return "Крипта" in kinds
        if qid == "q_two_assets": return len(symbols) >= 2
        if qid == "q_four_assets": return len(symbols) >= 4
        if qid == "q_stock_crypto": return {"Акции", "Крипта"}.issubset(kinds)
        if qid == "q_cash_guard": return u["balance"] >= 2000 and u["trades"] >= 1
        if qid == "q_five_trades": return u["trades"] >= 5
        if qid == "q_ten_trades": return u["trades"] >= 10
        if qid == "q_profit_sell": return u["profitable_sells"] >= 1
        if qid == "q_no_panic": return len(symbols) >= 3 and time.time() - (u["last_sell_ts"] or 0) > 120
        if qid == "q_value_105": return value >= 10500
        if qid == "q_value_112": return value >= 11200
        if qid == "q_value_125": return value >= 12500
        if qid == "q_level_2": return u["xp"] >= 150
        if qid == "q_level_3": return u["xp"] >= 350
        if qid == "q_level_4": return u["xp"] >= 650
        if qid == "q_lessons_1": return u["lessons"] >= 1
        if qid == "q_lessons_3": return u["lessons"] >= 3
        if qid == "q_lessons_5": return u["lessons"] >= 5
        if qid == "q_challenge": return len(symbols) >= 4 and u["trades"] >= 10 and u["lessons"] >= 3 and value >= 11000
        return False

    def refresh_quests(self):
        for w in self.quest_inner.winfo_children():
            w.destroy()
        claimed = self.store.claimed()
        done = sum(1 for q in QUESTS if q[0] in claimed)
        self.quest_summary.config(text=f"Квесты: {done}/{len(QUESTS)} выполнено")
        for qid, title, desc, xp, tag in QUESTS:
            ready = self.quest_ready(qid)
            taken = qid in claimed
            color = GREEN if taken else (YELLOW if ready else CARD)
            card = tk.Frame(self.quest_inner, bg=color if taken else CARD, padx=14, pady=10)
            card.pack(fill="x", padx=4, pady=6)
            head = f"✓ {title}" if taken else (f"! {title}" if ready else title)
            self.label(card, head, 13, "#07111f" if taken else TEXT, True).pack(anchor="w")
            self.label(card, f"{desc}  •  Награда: {xp} XP  •  Раздел: {tag}", 10, "#07111f" if taken else MUTED).pack(anchor="w", pady=(3, 0))

    def claim_ready(self):
        count = 0
        for qid, title, _desc, xp, _tag in QUESTS:
            if qid not in self.store.claimed() and self.quest_ready(qid):
                self.store.claim(qid, xp)
                self.store.log(f"Квест выполнен: {title} (+{xp} XP)")
                count += 1
        messagebox.showinfo("Квесты", f"Зачтено квестов: {count}" if count else "Пока нет новых выполненных квестов.")
        self.refresh_all()

    def build_leaderboard(self):
        f = self.frames["Рейтинг"]
        self.label(f, "Рейтинг выглядит как список реальных участников игры", 13, MUTED).pack(anchor="w", padx=16, pady=12)
        cols = ("place", "name", "rank", "capital", "xp", "trades")
        self.leader_tree = ttk.Treeview(f, columns=cols, show="headings")
        for col, title, width in zip(cols, ["#", "Игрок", "Ранг", "Капитал", "XP", "Сделки"], [50, 220, 170, 160, 90, 90]):
            self.leader_tree.heading(col, text=title)
            self.leader_tree.column(col, anchor="center", width=width)
        self.leader_tree.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def refresh_leaderboard(self):
        for item in self.leader_tree.get_children():
            self.leader_tree.delete(item)
        rows = []
        u = self.store.user()
        rows.append((u["name"], rank_by_xp(u["xp"]), self.store.portfolio_value("player"), u["xp"], u["trades"]))
        for b in self.store.db.execute("SELECT * FROM bots"):
            rows.append((b["name"], rank_by_xp(b["xp"]), self.store.portfolio_value(b["name"], True), b["xp"], b["trades"]))
        rows.sort(key=lambda x: (x[2], x[3]), reverse=True)
        for i, row in enumerate(rows, 1):
            self.leader_tree.insert("", "end", values=(i, row[0], row[1], money(row[2]), row[3], row[4]))

    def build_feed(self):
        f = self.frames["Лента"]
        self.feed_text = tk.Text(f, bg=CARD, fg=TEXT, bd=0, padx=14, pady=14, font=("Consolas", 11), wrap="word")
        self.feed_text.pack(fill="both", expand=True, padx=16, pady=16)

    def refresh_feed(self):
        self.feed_text.config(state="normal")
        self.feed_text.delete("1.0", "end")
        for event in self.store.last_events(60):
            self.feed_text.insert("end", event + "\n")
        self.feed_text.config(state="disabled")

    def refresh_all(self, full=False):
        u = self.store.user()
        if not u:
            return
        total = self.store.portfolio_value("player")
        self.profile_label.config(text=f"{u['name']} • {rank_by_xp(u['xp'])} • {money(total)}")
        if hasattr(self, "home_cards"):
            values = [money(u["balance"]), money(total), str(u["xp"]), rank_by_xp(u["xp"])]
            for lbl, val in zip(self.home_cards, values):
                lbl.config(text=val)
        if self.active_tab == "Рынок":
            self.draw_chart()
        if self.active_tab == "Портфель" or full:
            self.refresh_portfolio()
        if self.active_tab == "Квесты" or full:
            self.refresh_quests()
        if self.active_tab == "Рейтинг" or full:
            self.refresh_leaderboard()
        if self.active_tab == "Лента" or full:
            self.refresh_feed()

    def tick(self):
        self.store.move_market()
        self.store.bot_turns()
        # Важно: график не трогаем, если пользователь не находится на вкладке рынка.
        self.refresh_all()
        self.root.after(4500, self.tick)

def main():
    root = tk.Tk()
    app = TradeQuestApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
