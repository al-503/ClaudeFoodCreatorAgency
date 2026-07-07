# -*- coding: utf-8 -*-
"""
agents.py — Définition des 8 agents CrewAI de l'agence.

Chaque agent reçoit son "backstory" (instructions métier détaillées) depuis
un fichier Markdown du dossier prompts/, chargé via `utils.charger_prompt`.
Le LLM utilisé par tous les agents est Claude (claude-sonnet-4-6) via
litellm, configuré une seule fois dans `LLM_CLAUDE` ci-dessous.
"""

import os

from crewai import Agent, LLM

from utils import charger_prompt, charger_style_guide
from tools import (  # noqa: F401
    generer_slide_png,
    generer_story_png,
    generer_photo_ingredient,
    uploader_dossier_drive,
    enregistrer_planning,
    envoyer_email_recap,
)

# ----------------------------------------------------------------------
# Configuration du LLM (Claude via litellm, utilisé par CrewAI)
# ----------------------------------------------------------------------
# Le préfixe "anthropic/" indique à litellm quel fournisseur utiliser.
# La clé API est lue automatiquement depuis ANTHROPIC_API_KEY si non fournie
# explicitement, mais on la passe ici pour un message d'erreur plus clair
# en cas d'oubli de configuration.
LLM_CLAUDE = LLM(
    model="anthropic/claude-sonnet-4-6",
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
    temperature=0.7,
)

# Le guide de style est partagé par plusieurs agents (rédaction, design,
# stories, briefs vidéo) : on le charge une seule fois ici.
GUIDE_DE_STYLE = charger_style_guide()


# ----------------------------------------------------------------------
# Agent 1 — Chef Cuisinier Saisonnier (choix produits + fiches + recettes)
# ----------------------------------------------------------------------
agent_cuisinier = Agent(
    role="Chef cuisinier saisonnier — expert produits et recettes",
    goal=(
        "Choisir chaque semaine les 2 produits de saison les plus pertinents "
        "pour le contenu Instagram/TikTok, fournir leurs fiches complètes, "
        "et inventer une recette créative originale par produit en plus de "
        "la recette emblématique classique."
    ),
    backstory=charger_prompt("agent_cuisinier.md") + "\n\n" + GUIDE_DE_STYLE,
    llm=LLM_CLAUDE,
    verbose=True,
    allow_delegation=False,
)


# ----------------------------------------------------------------------
# Agent 3 — Rédaction
# ----------------------------------------------------------------------
agent_redaction = Agent(
    role="Rédactrice en chef de l'agence",
    goal=(
        "Rédiger l'ensemble des textes de la semaine (posts, légendes "
        "TikTok, carousels) en respectant scrupuleusement le guide de style."
    ),
    backstory=charger_prompt("agent_redaction.md") + "\n\n" + GUIDE_DE_STYLE,
    llm=LLM_CLAUDE,
    verbose=True,
    allow_delegation=False,
)


# ----------------------------------------------------------------------
# Agent 4 — Générateur Slides (carousels)
# ----------------------------------------------------------------------
agent_design_slides = Agent(
    role="Directrice artistique — carousels Instagram",
    goal=(
        "Transformer les textes des 4 carousels en HTML autonome puis en "
        "PNG (1080x1080), avec une charte graphique minimaliste moderne."
    ),
    backstory=charger_prompt("agent_claude_design.md") + "\n\n" + GUIDE_DE_STYLE,
    llm=LLM_CLAUDE,
    tools=[generer_slide_png],
    verbose=True,
    allow_delegation=False,
)


# ----------------------------------------------------------------------
# Agent 5 — Générateur Stories
# ----------------------------------------------------------------------
agent_design_stories = Agent(
    role="Directrice artistique — stories Instagram",
    goal=(
        "Concevoir et générer en PNG les 6 stories de la semaine "
        "(1080x1920), pensées pour la lecture mobile verticale."
    ),
    backstory=charger_prompt("agent_stories.md") + "\n\n" + GUIDE_DE_STYLE,
    llm=LLM_CLAUDE,
    tools=[generer_story_png],
    verbose=True,
    allow_delegation=False,
)


# ----------------------------------------------------------------------
# Agent 6 — Photo Ingrédients
# ----------------------------------------------------------------------
agent_photo_ingredients = Agent(
    role="Photographe culinaire éditoriale",
    goal=(
        "Rédiger des prompts Gemini précis et générer une photo flat lay "
        "par produit vedette, sans jamais bloquer le pipeline en cas "
        "d'échec de l'API."
    ),
    backstory=charger_prompt("agent_gemini_photo.md"),
    llm=LLM_CLAUDE,
    tools=[generer_photo_ingredient],
    verbose=True,
    allow_delegation=False,
)


# ----------------------------------------------------------------------
# Agent 7 — Briefs Vidéo (reel principal + reel satellite)
# ----------------------------------------------------------------------
agent_briefs_video = Agent(
    role="Réalisatrice vidéo Instagram/TikTok",
    goal=(
        "Rédiger le brief complet du reel principal (45-60s) et du reel "
        "satellite (20-30s) du produit vedette n°1, avec plans détaillés "
        "et légendes prêtes à l'emploi."
    ),
    backstory=charger_prompt("agent_reel_principal.md") + "\n\n" + GUIDE_DE_STYLE,
    llm=LLM_CLAUDE,
    verbose=True,
    allow_delegation=False,
)


# ----------------------------------------------------------------------
# Agent 8 — Email Coach
# ----------------------------------------------------------------------
agent_email_coach = Agent(
    role="Coordinatrice opérationnelle de l'agence",
    goal=(
        "Uploader le dossier Drive hebdomadaire et envoyer l'email "
        "récapitulatif au coach avec les produits de la semaine et la "
        "liste de courses."
    ),
    backstory=charger_prompt("agent_email.md"),
    llm=LLM_CLAUDE,
    tools=[uploader_dossier_drive, envoyer_email_recap],
    verbose=True,
    allow_delegation=False,
)
