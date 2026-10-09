"""Katalog bekannter Reality-TV-Formate fuer die Einstellungen-Seite.

Das ist nur eine Vorschlagsliste fuer die Checkbox-Auswahl in der Web-App -
die tatsaechlich aktive Liste steht immer in config/reality_shows.json.
Ergaenzt nur Formate, die auf einem der Sender in
scraper/sources/tvspielfilm.py (SENDER_SLUGS) oder im Streaming-Angebot RTL+
(scraper/sources/rtlplus.py) laufen.
"""
from __future__ import annotations

VORSCHLAEGE: list[dict] = [
    {"name": "Der Bachelor", "aliases": ["Bachelor"]},
    {"name": "Die Bachelorette", "aliases": ["Bachelorette"]},
    {"name": "Bachelor in Paradise", "aliases": []},
    {"name": "Prince Charming", "aliases": []},
    {"name": "Sommerhaus der Stars", "aliases": ["Das Sommerhaus der Stars"]},
    {"name": "Kampf der Realitystars", "aliases": []},
    {"name": "Are You The One", "aliases": ["Are You The One?"]},
    {"name": "Temptation Island", "aliases": ["Temptation Island VIP"]},
    {"name": "Couple Challenge", "aliases": ["CoupleChallenge", "#CoupleChallenge"]},
    {"name": "Big Brother", "aliases": ["Promi Big Brother"]},
    {"name": "Love Island", "aliases": ["Love Island VIP"]},
    {"name": "Ich bin ein Star - Holt mich hier raus", "aliases": ["Dschungelcamp", "IBES"]},
    {"name": "Promis unter Palmen", "aliases": []},
    {"name": "Hochzeit auf den ersten Blick", "aliases": []},
    {"name": "Forsthaus Rampensau", "aliases": []},
    {"name": "The Biggest Loser", "aliases": []},
    {"name": "Köln 50667", "aliases": []},
    {"name": "Berlin - Tag & Nacht", "aliases": []},
    {"name": "Frauentausch", "aliases": []},
    {"name": "Prominent getrennt", "aliases": []},
    {"name": "Goodbye Deutschland", "aliases": ["Goodbye Deutschland! Die Auswanderer"]},
    {"name": "Zuhause im Glück", "aliases": []},
    {"name": "Ex on the Beach", "aliases": []},
    {"name": "Naked Attraction", "aliases": []},
    {"name": "Adam sucht Eva", "aliases": []},
    {"name": "Take Me Out", "aliases": []},
    {"name": "Shopping Queen", "aliases": []},
    {"name": "Mein Lokal, Dein Lokal", "aliases": []},
    {"name": "4 Hochzeiten und eine Traumreise", "aliases": []},
    {"name": "Mensch Retter", "aliases": []},
    {"name": "Das große Backen", "aliases": []},
    {"name": "Deutschland sucht den Superstar", "aliases": ["DSDS"]},
    {"name": "Das perfekte Dinner", "aliases": []},
    {"name": "Die Höhle der Löwen", "aliases": []},
    {"name": "Hartz und herzlich", "aliases": []},
    {"name": "Der Trödeltrupp", "aliases": []},
    {"name": "Rosins Restaurants", "aliases": []},
    {"name": "Armes Deutschland", "aliases": []},
    {"name": "Diese Ochsenknechts", "aliases": []},
    {"name": "Bella Italia", "aliases": []},
    {"name": "Hartz Rot Gold", "aliases": []},
    {"name": "Zwischen Tüll und Tränen", "aliases": []},
    {"name": "Mein Leben mit 300 kg", "aliases": []},
    {"name": "My Strange Addiction", "aliases": []},
    {"name": "Verpfuscht", "aliases": []},
    {"name": "Die Ruhrpottwache", "aliases": []},
]
