# -*- coding: utf-8 -*-
"""
tools/__init__.py — Point d'entrée du package d'outils custom de l'agence.

Réexporte tous les outils CrewAI (décorés avec @tool) pour qu'ils puissent
être importés simplement via `from tools import ...` dans agents.py.
"""

from tools.visuels import (
    generer_slide_png,
    generer_story_png,
    generer_photo_ingredient,
)
from tools.drive import uploader_dossier_drive
from tools.email_tool import enregistrer_planning, envoyer_email_recap

__all__ = [
    "generer_slide_png",
    "generer_story_png",
    "generer_photo_ingredient",
    "uploader_dossier_drive",
    "enregistrer_planning",
    "envoyer_email_recap",
]
