# -*- coding: utf-8 -*-
"""
tools/visuels.py — Génération des visuels (carousels, stories, photos ingrédients).

Trois familles d'outils :
1. Construction du HTML (via tools/templates.py, déterministe, sans LLM)
   puis capture en PNG via Playwright, pour les carousels (1080x1080) et
   les stories (1080x1920). Les agents fournissent le texte déjà rédigé
   (titre, corps) ; la mise en page HTML/CSS est fixe et ne consomme pas
   de tokens supplémentaires.
2. Génération de photos d'ingrédients via l'API Gemini (gemini-2.5-flash-
   image, alias "Nano Banana"), avec sauvegarde directe en PNG.

Chaque outil est conçu pour ne JAMAIS lever d'exception bloquante : en cas
d'échec (HTML invalide, navigateur indisponible, API Gemini en erreur), il
retourne une chaîne de texte décrivant clairement l'échec, afin que l'agent
appelant puisse continuer le pipeline et que l'échec soit noté dans le
planning envoyé au coach.
"""

import os
import tempfile
import traceback

from crewai.tools import tool
from playwright.sync_api import sync_playwright

from utils import chemin_dossier_semaine, assurer_dossier
from tools.templates import construire_html_slide, construire_html_story

# Dimensions standard des formats produits par l'agence
LARGEUR_CAROUSEL, HAUTEUR_CAROUSEL = 1080, 1080
LARGEUR_STORY, HAUTEUR_STORY = 1080, 1920


def _capturer_html_vers_png(html: str, chemin_sortie: str, largeur: int, hauteur: int) -> None:
    """
    Capture un fragment HTML autonome en image PNG via Playwright (Chromium
    headless). Fonction interne, utilisée par les outils publics ci-dessous.

    Le HTML est écrit dans un fichier temporaire puis chargé via `goto()`
    (et non `set_content()`) : Chromium bloque l'accès aux ressources
    locales (`file://...`, utilisées pour les photos de fond) quand le
    document est chargé sans origine file:// — `set_content()` charge la
    page sur "about:blank" et déclenche ce blocage silencieusement (fond
    noir au lieu de l'image).
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as fichier_temp:
        fichier_temp.write(html)
        chemin_html_temp = fichier_temp.name

    try:
        with sync_playwright() as playwright:
            navigateur = playwright.chromium.launch()
            page = navigateur.new_page(viewport={"width": largeur, "height": hauteur})
            page.goto(f"file://{chemin_html_temp}", wait_until="networkidle")
            page.screenshot(path=chemin_sortie)
            navigateur.close()
    finally:
        os.remove(chemin_html_temp)


@tool("generer_slide_png")
def generer_slide_png(
    nom_dossier_carousel: str,
    numero_slide: int,
    titre: str,
    corps: str,
    couleur_accent: str,
) -> str:
    """
    Génère le PNG d'UNE slide de carousel (format 1080x1080) à partir du
    texte déjà rédigé (titre + corps). La mise en page HTML/CSS est
    construite par un template Python fixe (tools/templates.py), pas par le
    LLM : aucun coût ni risque d'erreur de format pour la mise en page.
    Sauvegarde dans output/<semaine>/carousels/<nom_dossier_carousel>/slide_NN.png.

    Pour les slides 1 à 3, si la photo Gemini de CE carousel a été générée
    avec succès au préalable (Agent 6, qui doit s'exécuter avant cet
    outil, et nomme ses fichiers "<nom_dossier_carousel>_ingredients.png"),
    elle est automatiquement utilisée comme fond — l'image panoramique
    unique est découpée en 3 tranches verticales égales, une par slide
    (effet de panoramique en swipant le carousel, pas la même image
    répétée 3 fois). Si la photo est absente (échec Gemini), la slide
    utilise le fond crème teinté standard — aucune action requise de
    l'agent dans ce cas.

    À appeler une fois par slide (6 appels par carousel, 24 au total).

    Args:
        nom_dossier_carousel: ex. "produit1_recette_classique" — sert aussi
            à retrouver la photo d'ingrédients spécifique à ce carousel
        numero_slide: numéro de la slide, de 1 à 6
        titre: titre de la slide (déjà rédigé par l'Agent Rédaction)
        corps: texte du corps de la slide, une ligne par paragraphe
        couleur_accent: couleur hexadécimale du produit (guide de style)

    Retourne un message de confirmation, ou un message "ERREUR:" explicite
    en cas d'échec (le pipeline continue malgré l'échec d'une slide isolée).
    """
    dossier_cible = os.path.join(chemin_dossier_semaine(), "carousels", nom_dossier_carousel)
    assurer_dossier(dossier_cible)

    nom_fichier = f"slide_{numero_slide:02d}.png"
    chemin_sortie = os.path.join(dossier_cible, nom_fichier)

    chemin_photo_fond = None
    if numero_slide <= 3:
        chemin_photo_candidat = os.path.join(
            chemin_dossier_semaine(), "photos_ingredients", f"{nom_dossier_carousel}_ingredients.png"
        )
        if os.path.isfile(chemin_photo_candidat):
            chemin_photo_fond = chemin_photo_candidat

    try:
        html_slide = construire_html_slide(titre, corps, couleur_accent, chemin_photo_fond, numero_slide)
        _capturer_html_vers_png(html_slide, chemin_sortie, LARGEUR_CAROUSEL, HAUTEUR_CAROUSEL)
        return f"Slide '{nom_dossier_carousel}/{nom_fichier}' générée avec succès."
    except Exception as erreur:
        # On continue malgré l'échec : une slide en erreur ne doit pas
        # bloquer la génération des autres ni du reste du pipeline.
        traceback.print_exc()
        return f"ERREUR: génération de '{nom_dossier_carousel}/{nom_fichier}' échouée — {erreur}"


@tool("generer_story_png")
def generer_story_png(
    nom_fichier: str,
    titre: str,
    corps: str,
    couleur_accent: str,
    type_story: str = "info",
    options_sondage: list = None,
    couleur_accent_secondaire: str = None,
) -> str:
    """
    Génère le PNG d'UNE story (format 1080x1920) à partir du texte déjà
    rédigé (titre + corps). La mise en page HTML/CSS est construite par un
    template Python fixe (tools/templates.py), pas par le LLM. Sauvegarde
    dans output/<semaine>/stories/<nom_fichier>.

    À appeler une fois par story (6 appels au total pour la semaine).

    Args:
        nom_fichier: ex. "story_01_lundi_teaser.png"
        titre: titre/accroche de la story
        corps: texte du corps, une ligne par paragraphe
        couleur_accent: couleur hexadécimale du produit concerné
        type_story: un de "teaser", "info", "sondage", "tip", "question",
            "recap" — adapte la mise en page (voir tools/templates.py)
        options_sondage: pour type_story="sondage", liste de 2 choix de
            réponse
        couleur_accent_secondaire: pour type_story="recap", couleur du
            second produit de la semaine

    Retourne un message de confirmation, ou un message "ERREUR:" explicite
    en cas d'échec (le pipeline continue malgré l'échec d'une story isolée).
    """
    dossier_cible = os.path.join(chemin_dossier_semaine(), "stories")
    assurer_dossier(dossier_cible)

    chemin_sortie = os.path.join(dossier_cible, nom_fichier)
    try:
        html_story = construire_html_story(
            titre, corps, couleur_accent, type_story, options_sondage, couleur_accent_secondaire
        )
        _capturer_html_vers_png(html_story, chemin_sortie, LARGEUR_STORY, HAUTEUR_STORY)
        return f"Story '{nom_fichier}' générée avec succès."
    except Exception as erreur:
        traceback.print_exc()
        return f"ERREUR: génération de '{nom_fichier}' échouée — {erreur}"


# Nom du modèle Gemini de génération d'image ("Nano Banana"), choisi plutôt
# qu'Imagen 3 : même clé API et même SDK que le reste du projet (pas de
# classe séparée ImageGenerationModel), moins coûteux, qualité équivalente
# pour des photos de type flat lay produit.
MODELE_GEMINI_IMAGE = "gemini-2.5-flash-image"


@tool("generer_photo_ingredient")
def generer_photo_ingredient(prompt_anglais: str, nom_fichier: str) -> str:
    """
    Appelle l'API Gemini (modèle gemini-2.5-flash-image, alias "Nano
    Banana") pour générer une photo à partir d'un prompt en anglais (flat
    lay food photography), puis sauvegarde directement le résultat en PNG
    dans output/<semaine>/photos_ingredients/<nom_fichier>.

    Génération et sauvegarde sont volontairement fusionnées dans un seul
    outil : les données binaires de l'image ne doivent jamais transiter en
    base64 par le contexte du LLM (un aller-retour generer → sauvegarder
    forcerait l'agent à recopier l'image entière dans sa réponse pour la
    repasser à l'outil suivant, ce qui peut faire exploser le nombre de
    tokens du prompt — déjà observé en pratique avec des prompts dépassant
    1 million de tokens). Le LLM ne voit ici qu'un message de statut court.

    Le ratio 16:9 est imposé via `image_config` (paramètre d'API), PAS via
    le texte du prompt : ce modèle ignore silencieusement les indications
    de ratio écrites dans le prompt (ex. "21:9 panoramic") et générait par
    défaut une image carrée 1024x1024 — repérée comme la cause du flou des
    photos en fond de slides (une image carrée étirée 3x en largeur pour
    l'effet panoramique). En 16:9 (1344x768, résolution native maximale de
    ce modèle), l'agrandissement nécessaire est moindre et le cadrage
    correspond réellement à une scène large.

    Args:
        prompt_anglais: prompt de génération d'image, en anglais
        nom_fichier: ex. "produit1_ingredients.png"

    Retourne un message de confirmation, ou un message "ERREUR:" explicite
    en cas d'échec (quota, réseau, indisponibilité du modèle). Le pipeline
    doit interpréter un retour préfixé "ERREUR:" comme un échec non
    bloquant : il continue sans la photo et le signale dans le planning.
    """
    try:
        from google import genai
        from google.genai import types

        cle_api = os.environ.get("GEMINI_API_KEY")
        if not cle_api:
            return "ERREUR: variable d'environnement GEMINI_API_KEY manquante."

        client = genai.Client(api_key=cle_api)
        reponse = client.models.generate_content(
            model=MODELE_GEMINI_IMAGE,
            contents=prompt_anglais,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(aspect_ratio="16:9"),
            ),
        )

        donnees_image = None
        for partie in reponse.candidates[0].content.parts:
            donnees_inline = getattr(partie, "inline_data", None)
            if donnees_inline is not None and donnees_inline.data:
                donnees_image = donnees_inline.data
                break

        if donnees_image is None:
            return "ERREUR: Gemini (Nano Banana) n'a retourné aucune image."

        dossier_cible = os.path.join(chemin_dossier_semaine(), "photos_ingredients")
        assurer_dossier(dossier_cible)
        chemin_sortie = os.path.join(dossier_cible, nom_fichier)
        with open(chemin_sortie, "wb") as f:
            f.write(donnees_image)

        return f"Photo '{nom_fichier}' générée et sauvegardée avec succès dans {chemin_sortie}."

    except Exception as erreur:
        traceback.print_exc()
        return f"ERREUR: génération/sauvegarde de '{nom_fichier}' échouée — {erreur}"
