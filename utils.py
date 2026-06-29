# -*- coding: utf-8 -*-
"""
utils.py — Fonctions utilitaires partagées du pipeline.

Contient notamment le chargeur de prompts qui lit les fichiers Markdown du
dossier `prompts/` et les injecte comme `backstory`/instructions dans les
agents CrewAI (voir agents.py).
"""

import os
from datetime import date, timedelta

# Dossier racine du projet (où se trouve ce fichier)
RACINE_PROJET = os.path.dirname(os.path.abspath(__file__))
DOSSIER_PROMPTS = os.path.join(RACINE_PROJET, "prompts")
DOSSIER_OUTPUT = os.path.join(RACINE_PROJET, "output")


def charger_prompt(nom_fichier: str) -> str:
    """
    Charge le contenu texte d'un fichier prompt depuis le dossier `prompts/`.

    Exemple : charger_prompt("agent_saisonnalite.md")

    Lève une exception claire si le fichier n'existe pas, car un prompt
    manquant est une erreur de configuration bloquante (pas une erreur
    "récupérable" comme un appel API qui échoue).
    """
    chemin = os.path.join(DOSSIER_PROMPTS, nom_fichier)
    if not os.path.isfile(chemin):
        raise FileNotFoundError(
            f"Prompt introuvable : {chemin}. "
            f"Vérifie que le fichier existe dans le dossier prompts/."
        )
    with open(chemin, "r", encoding="utf-8") as f:
        return f.read()


def charger_style_guide() -> str:
    """Raccourci pour charger le guide de style, utilisé par plusieurs agents."""
    return charger_prompt("style_guide.md")


def date_lundi_semaine_courante() -> date:
    """Retourne la date du lundi de la semaine en cours."""
    aujourd_hui = date.today()
    return aujourd_hui - timedelta(days=aujourd_hui.weekday())


def nom_dossier_semaine(lundi: date = None) -> str:
    """
    Génère le nom de dossier de la semaine au format `semaine_JJ_mois_AAAA`,
    ex: `semaine_28_juin_2026`. L'année est incluse pour ne pas écraser le
    dossier de la même semaine calendaire l'année suivante. Utilisé pour
    nommer le dossier local et le dossier Google Drive créés chaque semaine.
    """
    if lundi is None:
        lundi = date_lundi_semaine_courante()
    mois_fr = [
        "janvier", "fevrier", "mars", "avril", "mai", "juin",
        "juillet", "aout", "septembre", "octobre", "novembre", "decembre",
    ]
    return f"semaine_{lundi.day:02d}_{mois_fr[lundi.month - 1]}_{lundi.year}"


def chemin_dossier_semaine(lundi: date = None) -> str:
    """Retourne le chemin local complet du dossier de la semaine, dans output/."""
    return os.path.join(DOSSIER_OUTPUT, nom_dossier_semaine(lundi))


def assurer_dossier(chemin: str) -> str:
    """Crée le dossier (et ses parents) s'il n'existe pas encore, puis le retourne."""
    os.makedirs(chemin, exist_ok=True)
    return chemin
