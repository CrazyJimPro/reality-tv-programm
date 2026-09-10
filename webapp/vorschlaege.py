"""Katalog bekannter Reality-TV-Formate fuer die Einstellungen-Seite.

Das ist nur eine Vorschlagsliste fuer die Checkbox-Auswahl in der Web-App -
die tatsaechlich aktive Liste steht immer in config/reality_shows.json.
Ergaenzt keine Formate, die nicht auf RTL/VOX/Sat.1/ProSieben/RTL2/Kabel Eins
laufen.
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
]
