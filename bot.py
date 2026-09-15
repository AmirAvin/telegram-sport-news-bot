import os
import re
import json
import html
import time
import requests
import feedparser
import asyncio
import calendar
import hashlib
from urllib.parse import urlsplit, urlunsplit
from difflib import SequenceMatcher
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.constants import ParseMode

# ============================================================
# SETTINGS
# ============================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL", "@ligebartar24")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

SENT_FILE = "sent_news.json"
LAST_RUN_FILE = "last_run.json"
TELEGRAM_LAST_RUN_FILE = "telegram_last_run.json"
MAX_NEWS_PER_RUN = 10
TELEGRAM_SOURCE_CHANNELS = ["ft360_ir"]
TELEGRAM_MAX_POSTS_TO_SCAN = 80

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120 Safari/537.36"
)

# ============================================================
# RSS SOURCES
# ============================================================
RSS_SOURCES = [
    "https://www.khabarvarzeshi.com/rss/tp/63",
    "https://www.khabarvarzeshi.com/rss/tp/110",
    "https://www.khabarvarzeshi.com/rss/tp/111",
    "https://www.khabarvarzeshi.com/rss/tp/103",
    "https://www.khabarvarzeshi.com/rss/tp/64",
    "https://www.khabarvarzeshi.com/rss/tp/65",
    "https://www.khabarvarzeshi.com/rss/tp/66",
    "https://www.khabarvarzeshi.com/rss/tp/67",
    "https://www.khabarvarzeshi.com/rss/tp/68",
    "https://www.khabarvarzeshi.com/rss/tp/75",
    "https://www.khabarvarzeshi.com/rss/tp/76",
    "https://www.sarpoosh.com/rss/football.xml",
    "https://www.sarpoosh.com/rss/iran-pro-league.xml",
    "https://www.sarpoosh.com/rss/football-world.xml",
    "https://www.sarpoosh.com/rss/champions-league.xml",
    "https://www.sarpoosh.com/rss/football-transfers/iran.xml",
    "https://www.sarpoosh.com/rss/football-transfers/world.xml",
]

# ============================================================
# FOOTBALL KEYWORDS
# ============================================================
FOOTBALL_KEYWORDS = [
    "ÙÙØªØ¨Ø§Ù", "Ø§Ø³ØªÙÙØ§Ù", "Ù¾Ø±Ø³Ù¾ÙÙÛØ³", "Ø³Ù¾Ø§ÙØ§Ù", "ØªØ±Ø§Ú©ØªÙØ±", "Ø°ÙØ¨ Ø¢ÙÙ", "Ø°ÙØ¨âØ¢ÙÙ",
    "ÙÙÙØ§Ù", "Ú¯Ù Ú¯ÙØ±", "Ú¯ÙâÚ¯ÙØ±", "ÙÙÙØ§Ø¯", "Ø¢ÙÙÙÛÙÛÙÙ", "ÙØ³ Ø±ÙØ³ÙØ¬Ø§Ù", "ÙØ³ Ú©Ø±ÙØ§Ù",
    "Ø´ÙØ³ Ø¢Ø°Ø±", "Ø®ÛØ¨Ø±", "ÙÙØ§Ø¯Ø§Ø±", "ÚØ§Ø¯Ø±ÙÙÙ", "ÙØ³Ø§Ø¬Û", "Ù¾ÛÚ©Ø§Ù", "Ø³Ø§ÛÙ¾Ø§",
    "ÙÛÚ¯ Ø¨Ø±ØªØ±", "ÙÛÚ¯ ÛÚ©", "ÙÛÚ¯ Ø¢Ø²Ø§Ø¯Ú¯Ø§Ù", "Ø¬Ø§Ù Ø­Ø°ÙÛ", "Ø¬Ø§Ù Ø¬ÙØ§ÙÛ", "ÙÛÚ¯ ÙÙØ±ÙØ§ÙØ§Ù",
    "ÙÛÚ¯ Ø§Ø±ÙÙ¾Ø§", "ÙÛÚ¯ Ú©ÙÙØ±Ø§ÙØ³", "ØªÛÙ ÙÙÛ", "ØªÛÙâÙÙÛ", "ÙØ±Ø¨Û", "Ø³Ø±ÙØ±Ø¨Û", "Ø¨Ø§Ø²ÛÚ©Ù",
    "ÙÙØ§Ø¬Ù", "ÙØ¯Ø§ÙØ¹", "Ø¯Ø±ÙØ§Ø²Ù Ø¨Ø§Ù", "Ø¯Ø±ÙØ§Ø²ÙâØ¨Ø§Ù", "Ú¯ÙØ²Ù", "Ú¯ÙØ²ÙÛ", "Ú¯Ù", "Ù¾ÙØ§ÙØªÛ",
    "Ú©Ø§Ø±Øª ÙØ±ÙØ²", "Ú©Ø§Ø±Øª Ø²Ø±Ø¯", "Ø¯Ø§ÙØ±Û", "Ø¯Ø§ÙØ±", "VAR", "ÙÛØ¯ÛÙ", "ÙÛØ¯Ø¦Ù",
    "Ø·Ø§Ø±ÙÛ", "ÙÙØ¯Û Ø·Ø§Ø±ÙÛ", "Ø¢Ø²ÙÙÙ", "Ø³Ø±Ø¯Ø§Ø± Ø¢Ø²ÙÙÙ", "ÙÙÛ Ø²Ø§Ø¯Ù", "ÙÙÛâØ²Ø§Ø¯Ù", "ÙØ­Ø¨Û",
    "ÙØ­ÙØ¯ ÙØ­Ø¨Û", "Ø¬ÙØ§ÙØ¨Ø®Ø´", "ÙØ¯ÙØ³", "Ø¨ÛØ±Ø§ÙÙÙØ¯", "Ø­Ø³ÛÙ Ø­Ø³ÛÙÛ", "ÙÙØ¹Ù ÙÙÛÛ", "ÙÙØ¹ÙâÙÙÛÛ",
    "ÙØ¬ÛØ¯Û", "Ø¬Ø¨Ø§Ø±Û", "Ù¾ÛØ±ÙØ² ÙØ±Ø¨Ø§ÙÛ", "ÙÙÛØ¯Ú©ÛØ§", "ØªØ§Ø±ØªØ§Ø±", "Ø³ÙØ±Ø§Ø¨ Ø¨Ø®ØªÛØ§Ø±Û Ø²Ø§Ø¯Ù",
    "Ø³ÙØ±Ø§Ø¨ Ø¨Ø®ØªÛØ§Ø±ÛâØ²Ø§Ø¯Ù", "Ø±Ø¦Ø§Ù ÙØ§Ø¯Ø±ÛØ¯", "Ø¨Ø§Ø±Ø³ÙÙÙØ§", "Ø§ØªÙØªÛÚ©Ù", "ÙÙÚØ³ØªØ±ÛÙÙØ§ÛØªØ¯",
    "ÙÙÚØ³ØªØ±Ø³ÛØªÛ", "ÙÛÙØ±Ù¾ÙÙ", "Ø¢Ø±Ø³ÙØ§Ù", "ÚÙØ³Û", "ØªØ§ØªÙÙØ§Ù", "Ø¨Ø§ÛØ±Ù", "Ø¯ÙØ±ØªÙÙÙØ¯",
    "ÛÙÙÙØªÙØ³", "Ø§ÛÙØªØ±", "ÙÛÙØ§Ù", "Ù¾Ø§Ø±Û Ø³Ù ÚØ±ÙÙ", "Ù¾Ø§Ø±ÛâØ³ÙâÚØ±ÙÙ", "ÙØ§Ù¾ÙÙÛ", "Ø±Ù", "ÙØ§ØªØ²ÛÙ",
    "ÙØ³Û", "Ø±ÙÙØ§ÙØ¯Ù", "Ø§ÙØ¨Ø§Ù¾Ù", "ÙØ§ÙÙØ¯", "ÙÛÙØ§Ø±", "ØµÙØ§Ø­", "ÙÛÙÛØ³ÛÙØ³", "Ø¨ÙÛÙÚ¯Ø§Ù",
    "Ø¢Ø³ÛØ§", "Ø§Ø±ÙÙ¾Ø§", "ÙØ·Ø±", "Ø§ÙØ§Ø±Ø§Øª", "Ø¹Ø±Ø¨Ø³ØªØ§Ù",
]

NON_FOOTBALL_KEYWORDS = ["ÙØ§ÙÛØ¨Ø§Ù", "Ø¨Ø³Ú©ØªØ¨Ø§Ù", "Ú©Ø´ØªÛ", "ØªÙÛØ³", "Ø¨ÙÚ©Ø³", "ÙØ±ÙÙÙ ÛÚ©", "Ø§ØªÙÙØ¨ÛÙØ±Ø§ÙÛ", "Ø§Ø³Ø¨"]

# ============================================================
# HASHTAG MAP
# ============================================================
HASHTAG_MAP = {
    "Ø§Ø³ØªÙÙØ§Ù":"#Ø§Ø³ØªÙÙØ§Ù", "Ù¾Ø±Ø³Ù¾ÙÙÛØ³":"#Ù¾Ø±Ø³Ù¾ÙÙÛØ³", "Ø³Ù¾Ø§ÙØ§Ù":"#Ø³Ù¾Ø§ÙØ§Ù", "ØªØ±Ø§Ú©ØªÙØ±":"#ØªØ±Ø§Ú©ØªÙØ±",
    "Ø°ÙØ¨ Ø¢ÙÙ":"#Ø°ÙØ¨âØ¢ÙÙ", "Ø°ÙØ¨âØ¢ÙÙ":"#Ø°ÙØ¨âØ¢ÙÙ", "ÙÙÙØ§Ø¯":"#ÙÙÙØ§Ø¯", "ÙÙÙØ§Ù":"#ÙÙÙØ§Ù",
    "Ú¯Ù Ú¯ÙØ±":"#Ú¯ÙâÚ¯ÙØ±", "Ú¯ÙâÚ¯ÙØ±":"#Ú¯ÙâÚ¯ÙØ±", "Ø¢ÙÙÙÛÙÛÙÙ":"#Ø¢ÙÙÙÛÙÛÙÙ", "ÙØ³ Ø±ÙØ³ÙØ¬Ø§Ù":"#ÙØ³_Ø±ÙØ³ÙØ¬Ø§Ù",
    "ÙØ³ Ú©Ø±ÙØ§Ù":"#ÙØ³_Ú©Ø±ÙØ§Ù", "Ø´ÙØ³ Ø¢Ø°Ø±":"#Ø´ÙØ³âØ¢Ø°Ø±", "Ø®ÛØ¨Ø±":"#Ø®ÛØ¨Ø±", "ÙÙØ§Ø¯Ø§Ø±":"#ÙÙØ§Ø¯Ø§Ø±",
    "ÚØ§Ø¯Ø±ÙÙÙ":"#ÚØ§Ø¯Ø±ÙÙÙ", "ÙØ³Ø§Ø¬Û":"#ÙØ³Ø§Ø¬Û", "Ù¾ÛÚ©Ø§Ù":"#Ù¾ÛÚ©Ø§Ù", "Ø³Ø§ÛÙ¾Ø§":"#Ø³Ø§ÛÙ¾Ø§",
    "ÙÛÚ¯ Ø¨Ø±ØªØ±":"#ÙÛÚ¯_Ø¨Ø±ØªØ±", "ÙÛÚ¯ ÛÚ©":"#ÙÛÚ¯_ÛÚ©", "ÙÛÚ¯ Ø¢Ø²Ø§Ø¯Ú¯Ø§Ù":"#ÙÛÚ¯_Ø¢Ø²Ø§Ø¯Ú¯Ø§Ù", "Ø¬Ø§Ù Ø­Ø°ÙÛ":"#Ø¬Ø§Ù_Ø­Ø°ÙÛ",
    "Ø¬Ø§Ù Ø¬ÙØ§ÙÛ":"#Ø¬Ø§Ù_Ø¬ÙØ§ÙÛ", "ÙÛÚ¯ ÙÙØ±ÙØ§ÙØ§Ù":"#ÙÛÚ¯_ÙÙØ±ÙØ§ÙØ§Ù", "ÙÛÚ¯ Ø§Ø±ÙÙ¾Ø§":"#ÙÛÚ¯_Ø§Ø±ÙÙ¾Ø§",
    "ÙÛÚ¯ Ú©ÙÙØ±Ø§ÙØ³":"#ÙÛÚ¯_Ú©ÙÙØ±Ø§ÙØ³", "Ø³ÙÙ¾Ø± Ø¬Ø§Ù":"#Ø³ÙÙ¾Ø±Ø¬Ø§Ù", "ØªÛÙ ÙÙÛ":"#ØªÛÙ_ÙÙÛ", "ØªÛÙâÙÙÛ":"#ØªÛÙ_ÙÙÛ",
    "Ø§ÛØ±Ø§Ù":"#Ø§ÛØ±Ø§Ù", "ÙÙØ¯Û Ø·Ø§Ø±ÙÛ":"#Ø·Ø§Ø±ÙÛ", "Ø·Ø§Ø±ÙÛ":"#Ø·Ø§Ø±ÙÛ", "Ø³Ø±Ø¯Ø§Ø± Ø¢Ø²ÙÙÙ":"#Ø¢Ø²ÙÙÙ", "Ø¢Ø²ÙÙÙ":"#Ø¢Ø²ÙÙÙ",
    "Ø¹ÙÛØ±Ø¶Ø§ Ø¬ÙØ§ÙØ¨Ø®Ø´":"#Ø¬ÙØ§ÙØ¨Ø®Ø´", "Ø¬ÙØ§ÙØ¨Ø®Ø´":"#Ø¬ÙØ§ÙØ¨Ø®Ø´", "ÙØ­ÙØ¯ ÙØ­Ø¨Û":"#ÙØ­ÙØ¯ÙØ­Ø¨Û", "ÙØ­Ø¨Û":"#ÙØ­Ø¨Û",
    "ÙÙÛ Ø²Ø§Ø¯Ù":"#ÙÙÛâØ²Ø§Ø¯Ù", "ÙÙÛâØ²Ø§Ø¯Ù":"#ÙÙÛâØ²Ø§Ø¯Ù", "Ø¨ÛØ±Ø§ÙÙÙØ¯":"#Ø¨ÛØ±Ø§ÙÙÙØ¯", "Ø­Ø³ÛÙ Ø­Ø³ÛÙÛ":"#Ø­Ø³ÛÙâØ­Ø³ÛÙÛ",
    "Ø­Ø³ÛÙÛ":"#Ø­Ø³ÛÙÛ", "Ù¾ÛØ±ÙØ² ÙØ±Ø¨Ø§ÙÛ":"#Ù¾ÛØ±ÙØ²ÙØ±Ø¨Ø§ÙÛ", "Ø³ÙØ±Ø§Ø¨ Ø¨Ø®ØªÛØ§Ø±Û Ø²Ø§Ø¯Ù":"#Ø¨Ø®ØªÛØ§Ø±ÛâØ²Ø§Ø¯Ù",
    "Ø³ÙØ±Ø§Ø¨ Ø¨Ø®ØªÛØ§Ø±ÛâØ²Ø§Ø¯Ù":"#Ø¨Ø®ØªÛØ§Ø±ÛâØ²Ø§Ø¯Ù", "ÙÙØ¹Ù ÙÙÛÛ":"#ÙÙØ¹ÙâÙÙÛÛ", "ÙÙØ¹ÙâÙÙÛÛ":"#ÙÙØ¹ÙâÙÙÛÛ",
    "Ø¬Ø¨Ø§Ø±Û":"#Ø¬Ø¨Ø§Ø±Û", "ÙÙÛØ¯Ú©ÛØ§":"#ÙÙÛØ¯Ú©ÛØ§", "ØªØ§Ø±ØªØ§Ø±":"#ØªØ§Ø±ØªØ§Ø±", "Ø¹ÙÛ Ø¯Ø§ÛÛ":"#Ø¹ÙÛ_Ø¯Ø§ÛÛ", "Ú©Ø±ÛÙ Ø¨Ø§ÙØ±Û":"#Ú©Ø±ÛÙ_Ø¨Ø§ÙØ±Û",
    "Ø±Ø¦Ø§Ù ÙØ§Ø¯Ø±ÛØ¯":"#Ø±Ø¦Ø§Ù_ÙØ§Ø¯Ø±ÛØ¯", "Ø¨Ø§Ø±Ø³ÙÙÙØ§":"#Ø¨Ø§Ø±Ø³ÙÙÙØ§", "Ø§ØªÙØªÛÚ©Ù ÙØ§Ø¯Ø±ÛØ¯":"#Ø§ØªÙØªÛÚ©Ù_ÙØ§Ø¯Ø±ÛØ¯", "Ø§ØªÙØªÛÚ©Ù":"#Ø§ØªÙØªÛÚ©Ù",
    "ÙÙÚØ³ØªØ±ÛÙÙØ§ÛØªØ¯":"#ÙÙÚØ³ØªØ±ÛÙÙØ§ÛØªØ¯", "ÙÙÚØ³ØªØ±Ø³ÛØªÛ":"#ÙÙÚØ³ØªØ±Ø³ÛØªÛ", "ÙÛÙØ±Ù¾ÙÙ":"#ÙÛÙØ±Ù¾ÙÙ", "Ø¢Ø±Ø³ÙØ§Ù":"#Ø¢Ø±Ø³ÙØ§Ù",
    "ÚÙØ³Û":"#ÚÙØ³Û", "ØªØ§ØªÙÙØ§Ù":"#ØªØ§ØªÙÙØ§Ù", "Ø¨Ø§ÛØ±Ù ÙÙÙÛØ®":"#Ø¨Ø§ÛØ±Ù_ÙÙÙÛØ®", "Ø¨Ø§ÛØ±Ù":"#Ø¨Ø§ÛØ±Ù", "Ø¯ÙØ±ØªÙÙÙØ¯":"#Ø¯ÙØ±ØªÙÙÙØ¯",
    "ÛÙÙÙØªÙØ³":"#ÛÙÙÙØªÙØ³", "Ø§ÛÙØªØ± ÙÛÙØ§Ù":"#Ø§ÛÙØªØ±_ÙÛÙØ§Ù", "Ø§ÛÙØªØ±":"#Ø§ÛÙØªØ±", "Ø¢Ø« ÙÛÙØ§Ù":"#ÙÛÙØ§Ù", "ÙÛÙØ§Ù":"#ÙÛÙØ§Ù",
    "Ù¾Ø§Ø±Û Ø³Ù ÚØ±ÙÙ":"#Ù¾Ø§Ø±ÛâØ³ÙâÚØ±ÙÙ", "Ù¾Ø§Ø±ÛâØ³ÙâÚØ±ÙÙ":"#Ù¾Ø§Ø±ÛâØ³ÙâÚØ±ÙÙ", "ÙØ§Ù¾ÙÙÛ":"#ÙØ§Ù¾ÙÙÛ", "Ø±Ù":"#Ø±Ù", "ÙØ§ØªØ²ÛÙ":"#ÙØ§ØªØ²ÛÙ",
    "ÙÛÙÙÙ ÙØ³Û":"#ÙØ³Û", "ÙØ³Û":"#ÙØ³Û", "Ú©Ø±ÛØ³ØªÛØ§ÙÙ Ø±ÙÙØ§ÙØ¯Ù":"#Ø±ÙÙØ§ÙØ¯Ù", "Ø±ÙÙØ§ÙØ¯Ù":"#Ø±ÙÙØ§ÙØ¯Ù", "Ø§ÙØ¨Ø§Ù¾Ù":"#Ø§ÙØ¨Ø§Ù¾Ù",
    "ÙØ§ÙÙØ¯":"#ÙØ§ÙÙØ¯", "ÙÛÙØ§Ø±":"#ÙÛÙØ§Ø±", "ØµÙØ§Ø­":"#ØµÙØ§Ø­", "ÙÛÙÛØ³ÛÙØ³":"#ÙÛÙÛØ³ÛÙØ³", "Ø¨ÙÛÙÚ¯Ø§Ù":"#Ø¨ÙÛÙÚ¯Ø§Ù", "ÙÙØªØ¨Ø§Ù":"#ÙÙØªØ¨Ø§Ù",
}

# ============================================================
# TEXT / URL HELPERS
# ============================================================
def normalize_title(text):
    if not text:
        return ""
    text = html.unescape(str(text))
    replacements = {"Ù":"Û", "Ù":"Û", "Ù":"Ú©", "Û":"Ù", "Ø©":"Ù", "\u200c":" ", "\u200d":" ", "\u200e":" ", "\u200f":" ", "\ufeff":" "}
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[ÙÙÙÙÙÙÙÙÙ]", "", text)
    text = re.sub(r"[^\w\sØ¢-Û]", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def normalize_url(url):
    if not url:
        return ""
    try:
        parts = urlsplit(str(url).strip())
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", ""))
    except Exception:
        return str(url).strip().lower()


def make_news_fingerprint(title):
    normalized = normalize_title(title)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest() if normalized else ""


def make_news_key(news):
    return f"title:{make_news_fingerprint(news.get('title',''))}|url:{normalize_url(news.get('link',''))}"


def title_similarity(title1, title2):
    a, b = normalize_title(title1), normalize_title(title2)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def truncate_to_sentence(text, max_length):
    if not text:
        return ""
    text = str(text).strip()
    if len(text) <= max_length:
        return text
    candidate = text[:max_length].rstrip()
    positions = [candidate.rfind(x) for x in ["Ø", "?", "!", "ï¼", "ã", ".", "Ø", ";"]]
    positions = [x for x in positions if x >= 0]
    if positions:
        return candidate[:max(positions)+1].strip()
    p = candidate.rfind("\n\n")
    if p > 0:
        return candidate[:p].strip()
    p = candidate.rfind(" ")
    return candidate[:p].strip() if p > 0 else candidate


def create_hashtags(title, article_text=""):
    normalized = normalize_title(f"{title} {article_text}")
    found = []
    for key in sorted(HASHTAG_MAP, key=lambda x: len(normalize_title(x)), reverse=True):
        if normalize_title(key) in normalized and HASHTAG_MAP[key] not in found:
            found.append(HASHTAG_MAP[key])
        if len(found) >= 4:
            break
    if "#ÙÙØªØ¨Ø§Ù" not in found:
        found.append("#ÙÙØªØ¨Ø§Ù")
    return " ".join(found[:5])


def is_football_news(title, body=""):
    normalized = normalize_title(f"{title} {body}")
    for bad in NON_FOOTBALL_KEYWORDS:
        if normalize_title(bad) in normalized:
            return False
    return any(normalize_title(k) in normalized for k in FOOTBALL_KEYWORDS)

# ============================================================
# SENT DATABASE
# ============================================================
def load_sent_news():
    if not os.path.exists(SENT_FILE):
        return set()
    try:
        with open(SENT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return {str(x) for x in data}
        if isinstance(data, dict):
            return {str(x) for x in data.keys()}
    except Exception as e:
        print("LOAD SENT ERROR:", repr(e))
    return set()


def save_sent_news(sent):
    try:
        with open(SENT_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(sent), f, ensure_ascii=False, indent=2)
        print("ð¾ SENT DATABASE SAVED:", len(sent))
    except Exception as e:
        print("SAVE SENT ERROR:", repr(e))


def sent_contains_url(normalized_link, sent):
    if not normalized_link:
        return False
    for item in sent:
        if isinstance(item, str) and (item.startswith("http://") or item.startswith("https://")):
            if normalize_url(item) == normalized_link:
                return True
    return False


def sent_contains_title_hash(title_hash, sent):
    if not title_hash:
        return False
    if title_hash in sent:
        return True
    for item in sent:
        if isinstance(item, str) and item.startswith("title:"):
            if item.split("|", 1)[0].replace("title:", "", 1) == title_hash:
                return True
    return False


def migrate_historical_news(news, sent):
    clean_link = normalize_url(news.get("link", ""))
    title_hash = make_news_fingerprint(news.get("title", ""))
    if sent_contains_url(clean_link, sent):
        if clean_link:
            sent.add(clean_link)
        if title_hash:
            sent.add(title_hash)
        sent.add(make_news_key(news))
        return True
    return False


def is_already_sent(news, sent):
    link = news.get("link", "")
    clean_link = normalize_url(link)
    title_hash = make_news_fingerprint(news.get("title", ""))
    return bool((link and link in sent) or (clean_link and clean_link in sent) or sent_contains_url(clean_link, sent) or sent_contains_title_hash(title_hash, sent) or make_news_key(news) in sent)


def register_sent(news, sent):
    link = news.get("link", "")
    clean_link = normalize_url(link)
    title_hash = make_news_fingerprint(news.get("title", ""))
    if link:
        sent.add(link)
    if clean_link:
        sent.add(clean_link)
    if title_hash:
        sent.add(title_hash)
    sent.add(make_news_key(news))

# ============================================================
# STATE HELPERS
# ============================================================
def load_timestamp(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            value = json.load(f).get("last_run")
        return float(value) if value else None
    except Exception as e:
        print("LOAD STATE ERROR:", path, repr(e))
        return None


def save_timestamp(path, timestamp):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"last_run": timestamp}, f, ensure_ascii=False, indent=2)
        print("ð¾ STATE SAVED:", path, timestamp)
    except Exception as e:
        print("SAVE STATE ERROR:", path, repr(e))

# ============================================================
# RSS
# ============================================================
def get_news(rss_url):
    try:
        response = requests.get(rss_url, headers={"User-Agent": USER_AGENT}, timeout=30)
        print("RSS STATUS:", response.status_code)
        if response.status_code != 200:
            return []
        feed = feedparser.parse(response.content)
        news = []
        for entry in feed.entries:
            title = html.unescape(entry.get("title", "")).strip()
            link = entry.get("link", "").strip()
            summary = entry.get("summary", entry.get("description", ""))
            if title and link and is_football_news(title, BeautifulSoup(summary, "html.parser").get_text(" ", strip=True)):
                news.append({"title": title, "link": link, "summary": summary, "entry": entry, "source": "rss"})
        return news
    except Exception as e:
        print("RSS ERROR:", repr(e))
        return []


def get_news_timestamp(news):
    try:
        entry = news.get("entry")
        if not entry:
            return None
        parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        return float(calendar.timegm(parsed)) if parsed else None
    except Exception as e:
        print("DATE ERROR:", repr(e))
        return None

# ============================================================
# TELEGRAM PUBLIC CHANNEL SCRAPER
# ============================================================
def telegram_post_timestamp(tag):
    try:
        value = tag.get("datetime")
        if not value:
            return None
        value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value).timestamp()
    except Exception:
        return None


def extract_telegram_image(message):
    try:
        photo = message.select_one("a.tgme_widget_message_photo_wrap")
        if photo:
            style = photo.get("style", "")
            m = re.search(r"url\(['\"]?([^'\")]+)", style)
            if m:
                return html.unescape(m.group(1))
        img = message.select_one("img.tgme_widget_message_photo_image")
        if img:
            return img.get("src") or img.get("data-src")
    except Exception as e:
        print("TELEGRAM IMAGE ERROR:", repr(e))
    return None


def get_telegram_news(channel):
    url = f"https://t.me/s/{channel}"
    print("\nTELEGRAM SOURCE:", url)
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8"}, timeout=30)
        print("TELEGRAM STATUS:", response.status_code)
        if response.status_code != 200:
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        messages = soup.select("div.tgme_widget_message")[-TELEGRAM_MAX_POSTS_TO_SCAN:]
        result = []
        for message in messages:
            text_node = message.select_one("div.tgme_widget_message_text")
            text = text_node.get_text("\n", strip=True) if text_node else ""
            text = re.sub(r"\n{3,}", "\n\n", text).strip()
            if not text:
                continue
            link_node = message.select_one("a.tgme_widget_message_date")
            link = link_node.get("href", "") if link_node else ""
            if not link:
                continue
            ts = telegram_post_timestamp(link_node) if link_node else None
            if ts is None:
                # Telegram sometimes exposes the datetime on the time tag.
                time_node = message.select_one("time")
                ts = telegram_post_timestamp(time_node) if time_node else None
            if ts is None:
                continue
            if not is_football_news(text):
                continue
            result.append({
                "title": text.split("\n", 1)[0][:300],
                "link": link,
                "summary": text,
                "text": text,
                "timestamp": ts,
                "image_url": extract_telegram_image(message),
                "source": "telegram",
                "source_channel": channel,
                "entry": None,
            })
        result.sort(key=lambda x: x.get("timestamp", 0))
        print("TELEGRAM FOOTBALL POSTS:", len(result))
        return result
    except Exception as e:
        print("TELEGRAM SCRAPE ERROR:", repr(e))
        return []

# ============================================================
# ARTICLE / IMAGE / APARAT
# ============================================================
def get_article_text(url):
    print("ð GETTING ARTICLE TEXT:", url)
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT, "Accept-Language":"fa-IR,fa;q=0.9,en;q=0.8"}, timeout=30)
        print("ARTICLE STATUS:", response.status_code)
        if response.status_code != 200:
            return ""
        soup = BeautifulSoup(response.content, "html.parser")
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "form", "aside"]):
            tag.decompose()
        selectors = ["article", "[class*='article-content']", "[class*='article_content']", "[class*='news-content']", "[class*='news_content']", "[class*='post-content']", "[class*='post_content']", "[class*='content-detail']", "[class*='content_detail']", "[class*='news-text']", "[class*='news_text']", "[class*='article-body']", "[class*='article_body']", "main"]
        container = None
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element and len(element.find_all("p")) >= 2:
                    container = element
                    break
            except Exception:
                pass
        paragraphs = container.find_all("p") if container else soup.find_all("p")
        bad_phrases = ["Ø¹Ø¶ÙÛØª Ø¯Ø± Ú©Ø§ÙØ§Ù", "Ø§Ø®Ø¨Ø§Ø± ÙØ±ØªØ¨Ø·", "ÙØ·Ø§ÙØ¨ ÙØ±ØªØ¨Ø·", "ØªØ¨ÙÛØºØ§Øª", "Ú©Ø¯ Ø®Ø¨Ø±", "ÙÙØ¨Ø¹:", "ÙÙØ¨Ø¹ Ø®Ø¨Ø±", "Ø§Ø±Ø³Ø§Ù Ø¯ÛØ¯Ú¯Ø§Ù", "Ø¯ÛØ¯Ú¯Ø§Ù"]
        texts, seen = [], set()
        for p in paragraphs:
            text = re.sub(r"\s+", " ", p.get_text(" ", strip=True)).strip()
            if len(text) < 25 or any(x in text for x in bad_phrases):
                continue
            n = normalize_title(text)
            if n not in seen:
                seen.add(n)
                texts.append(text)
        result = "\n\n".join(texts).strip()
        print("ARTICLE TEXT:", len(result), "characters")
        return result
    except Exception as e:
        print("ARTICLE TEXT ERROR:", repr(e))
        return ""


def extract_aparat_hash(text):
    if not text:
        return None
    try:
        text = html.unescape(str(text))
        patterns = [r'aparat\.com/v/([A-Za-z0-9]+)', r'videohash[\/"\':=\s]+([A-Za-z0-9]+)', r'embed/videohash/([A-Za-z0-9]+)', r'videohash=([A-Za-z0-9]+)']
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m and m.group(1).strip():
                return m.group(1).strip()
    except Exception:
        pass
    return None


def find_aparat_hash_in_entry(entry):
    if not entry:
        return None
    try:
        for key in entry.keys():
            value = entry.get(key)
            if isinstance(value, bytes):
                value = value.decode("utf-8", errors="ignore")
            if isinstance(value, str):
                found = extract_aparat_hash(value)
                if found:
                    return found
    except Exception:
        pass
    return None


def get_aparat_video(url, news_entry=None):
    print("ð¥ CHECKING APARAT VIDEO:", url)
    try:
        headers = {"User-Agent": USER_AGENT, "Accept-Language":"fa-IR,fa;q=0.9,en;q=0.8", "Referer":"https://www.aparat.com/"}
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            return None
        video_hash = extract_aparat_hash(response.text)
        if not video_hash and news_entry:
            video_hash = find_aparat_hash_in_entry(news_entry.get("entry"))
        if not video_hash and news_entry:
            video_hash = extract_aparat_hash(news_entry.get("summary", ""))
        if not video_hash:
            print("â APARAT VIDEO HASH NOT FOUND")
            return None
        api_url = f"https://www.aparat.com/api/fa/v1/video/video/show/videohash/{video_hash}"
        api_response = requests.get(api_url, headers=headers, timeout=30)
        if api_response.status_code != 200:
            return None
        data = api_response.json().get("data", {}).get("attributes", {})
        links = data.get("file_link_all", [])
        choices = []
        for item in links:
            if not isinstance(item, dict):
                continue
            profile = item.get("profile", "")
            urls = item.get("urls", [])
            if isinstance(urls, str):
                urls = [urls]
            for media_url in urls:
                if isinstance(media_url, str) and ".mp4" in media_url.lower():
                    choices.append((profile, media_url))
        for quality in ["360p", "240p", "144p"]:
            for profile, media_url in choices:
                if profile == quality:
                    return media_url
        return choices[0][1] if choices else None
    except Exception as e:
        print("APARAT VIDEO ERROR:", repr(e))
        return None


def get_entry_image(news):
    if news.get("image_url"):
        return news.get("image_url")
    try:
        entry = news.get("entry")
        if entry:
            for group in [entry.get("media_content", []), entry.get("media_thumbnail", []), entry.get("enclosures", [])]:
                for media in group:
                    if isinstance(media, dict):
                        url = media.get("url") or media.get("href")
                        if url:
                            return url
            summary = news.get("summary", "")
            soup = BeautifulSoup(summary, "html.parser")
            img = soup.find("img")
            if img:
                return img.get("src") or img.get("data-src") or img.get("data-original")
    except Exception as e:
        print("IMAGE ERROR:", repr(e))
    return None

# ============================================================
# CAPTIONS
# ============================================================
def build_media_caption(title, article_text, hashtags):
    footer = f"\n\n{html.escape(hashtags)}\n\n@ligebartar24"
    fixed = f"<b>{html.escape(title)}</b>\n\n"
    available = max(50, 1024 - len(fixed) - len(footer) - 5)
    body = truncate_to_sentence(article_text, available)
    return fixed + html.escape(body) + footer


def build_text_message(title, article_text, hashtags):
    footer = f"\n\n{html.escape(hashtags)}\n\n@ligebartar24"
    fixed = f"<b>{html.escape(title)}</b>\n\n"
    available = max(100, 4096 - len(fixed) - len(footer) - 5)
    body = truncate_to_sentence(article_text, available)
    return fixed + html.escape(body) + footer


def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)

# ============================================================
# SEND NEWS
# ============================================================
def send_news(bot, news, sent):
    title = news["title"]
    print("\nPROCESSING:", title)

    if news.get("source") == "telegram":
        article_text = news.get("text") or news.get("summary") or title
    else:
        article_text = get_article_text(news["link"])
        if not article_text:
            article_text = BeautifulSoup(news.get("summary", ""), "html.parser").get_text(" ", strip=True)
            article_text = re.sub(r"\s+", " ", article_text).strip()

    hashtags = create_hashtags(title, article_text)
    caption = build_media_caption(title, article_text, hashtags)
    print("HASHTAGS:", hashtags)

    # Aparat video only for RSS/news sites. Telegram source videos are not downloaded here.
    if news.get("source") != "telegram":
        video_url = get_aparat_video(news["link"], news)
        if video_url:
            temp_file = "temp_video.mp4"
            try:
                media_response = requests.get(video_url, headers={"User-Agent": USER_AGENT, "Referer":"https://www.aparat.com/", "Origin":"https://www.aparat.com"}, stream=True, timeout=120)
                if media_response.status_code == 200:
                    with open(temp_file, "wb") as f:
                        for chunk in media_response.iter_content(chunk_size=1024 * 256):
                            if chunk:
                                f.write(chunk)
                    with open(temp_file, "rb") as video_file:
                        run_async(bot.send_video(chat_id=CHANNEL, video=video_file, caption=caption, parse_mode=ParseMode.HTML, supports_streaming=True))
                    print("â VIDEO NEWS SENT")
                    register_sent(news, sent)
                    return True
            except Exception as e:
                print("VIDEO ERROR:", repr(e))
            finally:
                if os.path.exists(temp_file):
                    try: os.remove(temp_file)
                    except Exception: pass

    image_url = get_entry_image(news)
    if image_url:
        temp_image = "temp_news.jpg"
        try:
            image_response = requests.get(image_url, headers={"User-Agent": USER_AGENT}, timeout=30)
            if image_response.status_code == 200 and image_response.content:
                with open(temp_image, "wb") as f:
                    f.write(image_response.content)
                with open(temp_image, "rb") as photo:
                    run_async(bot.send_photo(chat_id=CHANNEL, photo=photo, caption=caption, parse_mode=ParseMode.HTML))
                print("â IMAGE NEWS SENT")
                register_sent(news, sent)
                return True
        except Exception as e:
            print("IMAGE SEND ERROR:", repr(e))
        finally:
            if os.path.exists(temp_image):
                try: os.remove(temp_image)
                except Exception: pass

    try:
        run_async(bot.send_message(chat_id=CHANNEL, text=build_text_message(title, article_text, hashtags), parse_mode=ParseMode.HTML, disable_web_page_preview=True))
        print("â TEXT NEWS SENT")
        register_sent(news, sent)
        return True
    except Exception as e:
        print("TELEGRAM SEND ERROR:", repr(e))
        return False

# ============================================================
# RSS PROCESSOR
# ============================================================
def process_rss_news(bot, sent):
    print("\n========================================")
    print("ð° CHECKING RSS FOOTBALL NEWS")
    print("========================================")
    current_time = time.time()
    last_run = load_timestamp(LAST_RUN_FILE)
    if last_run is None:
        print("â ï¸ RSS FIRST RUN - BASELINE ONLY")
        save_timestamp(LAST_RUN_FILE, current_time)
        return

    all_new = []
    for rss_url in RSS_SOURCES:
        print("\nRSS:", rss_url)
        for news in get_news(rss_url):
            if migrate_historical_news(news, sent) or is_already_sent(news, sent):
                continue
            ts = get_news_timestamp(news)
            if ts is None or ts <= last_run:
                continue
            all_new.append(news)

    unique, seen_titles, seen_urls = [], set(), set()
    for news in all_new:
        th = make_news_fingerprint(news["title"])
        u = normalize_url(news["link"])
        if th in seen_titles or (u and u in seen_urls):
            continue
        seen_titles.add(th)
        if u: seen_urls.add(u)
        unique.append(news)
    unique.sort(key=lambda x: get_news_timestamp(x) or 0)

    sent_count = 0
    last_success = None
    for news in unique[:MAX_NEWS_PER_RUN]:
        if send_news(bot, news, sent):
            sent_count += 1
            last_success = get_news_timestamp(news)
            save_sent_news(sent)
        time.sleep(1)

    if last_success is not None:
        save_timestamp(LAST_RUN_FILE, last_success)
    elif not unique:
        save_timestamp(LAST_RUN_FILE, current_time)
    save_sent_news(sent)
    print("RSS NEWS SENT:", sent_count)

# ============================================================
# TELEGRAM PROCESSOR
# ============================================================
def process_telegram_news(bot, sent):
    print("\n========================================")
    print("ð£ CHECKING TELEGRAM SOURCE CHANNELS")
    print("========================================")
    current_time = time.time()
    last_run = load_timestamp(TELEGRAM_LAST_RUN_FILE)
    if last_run is None:
        print("â ï¸ TELEGRAM FIRST RUN - BASELINE ONLY")
        latest = current_time
        for channel in TELEGRAM_SOURCE_CHANNELS:
            posts = get_telegram_news(channel)
            if posts:
                latest = max(latest, max(x.get("timestamp", current_time) for x in posts))
        save_timestamp(TELEGRAM_LAST_RUN_FILE, latest)
        print("â TELEGRAM BASELINE CREATED")
        return

    all_new = []
    for channel in TELEGRAM_SOURCE_CHANNELS:
        posts = get_telegram_news(channel)
        for news in posts:
            ts = news.get("timestamp")
            if not ts or ts <= last_run:
                continue
            if migrate_historical_news(news, sent) or is_already_sent(news, sent):
                continue
            all_new.append(news)

    unique, seen_titles = [], set()
    for news in all_new:
        th = make_news_fingerprint(news["title"] + " " + news.get("text", ""))
        if th in seen_titles:
            continue
        seen_titles.add(th)
        unique.append(news)
    unique.sort(key=lambda x: x.get("timestamp", 0))

    sent_count = 0
    last_success = None
    for news in unique[:MAX_NEWS_PER_RUN]:
        if send_news(bot, news, sent):
            sent_count += 1
            last_success = news.get("timestamp")
            save_sent_news(sent)
        time.sleep(1)

    if last_success is not None:
        save_timestamp(TELEGRAM_LAST_RUN_FILE, last_success)
    elif not unique:
        save_timestamp(TELEGRAM_LAST_RUN_FILE, current_time)
    save_sent_news(sent)
    print("TELEGRAM NEWS SENT:", sent_count)

# ============================================================
# API FOOTBALL
# ============================================================
def check_api_status():
    if not API_FOOTBALL_KEY:
        print("â ï¸ API FOOTBALL KEY NOT FOUND")
        return False
    try:
        response = requests.get("https://v3.football.api-sports.io/status", headers={"x-apisports-key": API_FOOTBALL_KEY}, timeout=20)
        print("API REQUEST:", response.status_code)
        data = response.json()
        print("API RESPONSE:", data)
        return not bool(data.get("errors", {}))
    except Exception as e:
        print("API STATUS ERROR:", repr(e))
        return False

# ============================================================
# MAIN
# ============================================================
def main():
    print("TELEGRAM SPORTS NEWS BOT")
    print("================================")
    print("ð®ð· RSS + ð£ TELEGRAM FOOTBALL")
    print("================================")

    if not BOT_TOKEN:
        print("â BOT_TOKEN NOT FOUND")
        return

    bot = Bot(token=BOT_TOKEN)
    if not check_api_status():
        print("â ï¸ API FOOTBALL UNAVAILABLE")
        print("â¡ï¸ RSS + TELEGRAM NEWS WILL STILL RUN")

    sent = load_sent_news()
    print("SENT DATABASE COUNT:", len(sent))

    # ÙØ± Ø¯Ù ÙÙØ¨Ø¹ ÙØ¶Ø¹ÛØª Ø²ÙØ§ÙÛ Ø¬Ø¯Ø§ Ø¯Ø§Ø±ÙØ¯ ØªØ§ ÛÚ©Û Ø¨Ø§Ø¹Ø« Ø§Ø² Ø¯Ø³Øª Ø±ÙØªÙ Ø®Ø¨Ø±ÙØ§Û Ø¯ÛÚ¯Ø±Û ÙØ´ÙØ¯.
    process_rss_news(bot, sent)
    process_telegram_news(bot, sent)

    print("\n================================")
    print("BOT RUN FINISHED")
    print("================================")


if __name__ == "__main__":
    main()
