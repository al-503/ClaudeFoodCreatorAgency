# -*- coding: utf-8 -*-
"""
tasks.py — Définition des tâches CrewAI exécutées en Process.sequential.

Chaque tâche est liée à son agent (voir agents.py) et reçoit en `context`
les tâches précédentes dont elle dépend, afin que CrewAI propage
automatiquement leurs sorties dans le contexte du LLM.

La fonction `creer_taches` est appelée depuis main.py avec les données
dynamiques de la semaine (produits disponibles selon le mois, date du
lundi), car ces informations ne sont connues qu'à l'exécution.

Ordre d'exécution : la génération des photos d'ingrédients (Agent 6) a été
déplacée avant la génération des carousels (Agent 4), pour que les photos
existent déjà sur disque quand les slides 1-3 de chaque carousel en ont
besoin comme fond (voir tools/visuels.py::generer_slide_png).

Deux optimisations de coût (voir CHANGELOG mental, pas de fichier dédié) :
- La sauvegarde des légendes/briefs n'est plus une tâche LLM à part avec
  appel d'outil (l'agent devait retaper un texte déjà généré — payé deux
  fois en tokens de sortie). C'est maintenant un callback Python
  (tools/post_traitement.py) attaché directement aux tâches de rédaction
  concernées, qui découpe le texte déjà produit sans aucun appel LLM
  supplémentaire.
- La génération des 24 slides n'est plus une seule tâche (CrewAI réenvoie
  tout l'historique de la tâche à chaque appel d'outil, donc une croissance
  qui était quadratique sur 24 étapes) mais 4 tâches d'une carousel chacune
  (6 étapes), ce qui réduit nettement le volume total de contexte réenvoyé.

La liste de courses (legendes_et_briefs/liste_courses.md) suit le même
principe que les légendes/briefs : un callback Python (sans appel LLM)
extrait les blocs '**Ingrédients :**' déjà présents dans les sorties de
l'Agent Saisonnalité (recettes classiques) et de l'Agent Cuisinier
(recettes créatives) et les concatène en une liste brute, non triée — le
tri par rayon est laissé au coach.
"""

import json

from crewai import Task

from agents import (
    agent_saisonnalite,
    agent_cuisinier,
    agent_redaction,
    agent_design_slides,
    agent_design_stories,
    agent_photo_ingredients,
    agent_briefs_video,
    agent_email_coach,
)
from tools.post_traitement import (
    sauvegarder_legendes,
    sauvegarder_briefs,
    sauvegarder_ingredients_classiques,
    sauvegarder_ingredients_creatifs,
)

NOMS_CAROUSELS = [
    "produit1_recette_classique",
    "produit1_recette_creative",
    "produit2_recette_classique",
    "produit2_recette_creative",
]


def creer_taches(produits_disponibles: dict, date_lundi: str, historique_produits: list = None) -> list:
    """
    Construit la liste ordonnée des 11 tâches de la semaine (8 tâches
    "métier" historiques, sauf que la génération des slides est éclatée en
    4 tâches — une par carousel — au lieu d'une seule).

    Args:
        produits_disponibles: dict des produits en pleine saison ce mois-ci
            (sortie de `saison_data.produits_du_mois`), injecté dans la
            description de la tâche 1 pour que l'agent choisisse parmi eux.
        date_lundi: date du lundi de la semaine en cours, format "JJ/MM/AAAA",
            utilisée dans le planning et l'email final.
        historique_produits: liste des dernières semaines {semaine, produits},
            transmise à l'agent Saisonnalité pour éviter les répétitions.
    """
    historique_produits = historique_produits or []
    bloc_historique = ""
    if historique_produits:
        lignes = "\n".join(
            f"  - Semaine du {e['semaine']} : {', '.join(e['produits'])}"
            for e in historique_produits
        )
        bloc_historique = (
            f"\n\nProduits déjà publiés ces dernières semaines (à éviter "
            f"absolument pour varier le contenu) :\n{lignes}"
        )

    # ------------------------------------------------------------------
    # Tâche 1 — Saisonnalité
    # ------------------------------------------------------------------
    tache_saisonnalite = Task(
        description=(
            "Voici les produits actuellement en pleine saison en France "
            f"ce mois-ci : {json.dumps(produits_disponibles, ensure_ascii=False)}"
            f"{bloc_historique}\n\n"
            "Choisis exactement 2 produits vedettes parmi cette liste, en "
            "suivant scrupuleusement tes instructions. Pour chaque recette "
            "emblématique (fournie seulement par son nom et sa description, "
            "sans ingrédients), ajoute de ta propre connaissance culinaire "
            "la liste des ingrédients avec quantités pour 4 personnes, "
            "précédée EXACTEMENT de l'étiquette '**Ingrédients :**' sur sa "
            "propre ligne puis d'une liste à puces (une ligne par "
            "ingrédient, format '- quantité ingrédient'). Cette étiquette "
            "exacte est lue automatiquement par un programme pour "
            "construire la liste de courses de la semaine : un format qui "
            "diffère fait échouer cette sauvegarde automatique."
        ),
        expected_output=(
            "Les fiches complètes des 2 produits vedettes (PRODUIT 1 et "
            "PRODUIT 2), chacune avec saison, variétés, origine, "
            "nutrition, conservation, anecdote historique, recette "
            "emblématique (incluant son bloc '**Ingrédients :**' avec "
            "quantités), accords suggérés, plus une courte justification "
            "du choix."
        ),
        agent=agent_saisonnalite,
        callback=sauvegarder_ingredients_classiques,
    )

    # ------------------------------------------------------------------
    # Tâche 2 — Cuisinier Créatif
    # ------------------------------------------------------------------
    tache_cuisinier = Task(
        description=(
            "À partir des 2 produits vedettes choisis, invente une recette "
            "créative originale par produit, en respectant strictement tes "
            "règles de chef : jamais la recette emblématique classique, "
            "jamais une recette déjà inventée pour ce produit, maximum 8 "
            "ingrédients, maximum 30 minutes, association inattendue mais "
            "cohérente. Précède la liste d'ingrédients de chaque recette "
            "EXACTEMENT de l'étiquette '**Ingrédients :**' sur sa propre "
            "ligne, suivie d'une liste à puces avec quantités pour 4 "
            "personnes (format '- quantité ingrédient') — cette étiquette "
            "exacte est lue automatiquement par un programme pour "
            "construire la liste de courses de la semaine : un format qui "
            "diffère fait échouer cette sauvegarde automatique."
        ),
        expected_output=(
            "2 fiches recette créative complètes (RECETTE PRODUIT 1 et "
            "RECETTE PRODUIT 2) : nom instagrammable, concept, bloc "
            "'**Ingrédients :**' avec quantités, étapes numérotées, tip du "
            "chef, variante."
        ),
        agent=agent_cuisinier,
        context=[tache_saisonnalite],
        callback=sauvegarder_ingredients_creatifs,
    )

    # ------------------------------------------------------------------
    # Tâche 3 — Rédaction
    # ------------------------------------------------------------------
    tache_redaction = Task(
        description=(
            "À partir des fiches produits et des recettes créatives, "
            "rédige pour chacun des 2 produits : le post photo produit "
            "Instagram (titre, 150-200 mots, une question ouverte en fin "
            "de texte, 12 hashtags), la légende courte TikTok (100 mots "
            "max, accroche, 3 hashtags), le carousel 6 slides de la "
            "recette emblématique classique, et le carousel 6 slides de la "
            "recette créative du chef. Respecte scrupuleusement le guide "
            "de style fourni — aucun terme technique (\"CTA\", \"hook\", "
            "etc.) ne doit jamais apparaître dans le texte final, écris "
            "directement la phrase elle-même.\n\n"
            "Format obligatoire : précède CHAQUE section d'un titre "
            "Markdown de niveau 2 EXACT (deux dièses, un espace, puis le "
            "titre, rien d'autre sur la ligne) : '## PRODUIT 1 — POST "
            "INSTAGRAM', '## PRODUIT 1 — TIKTOK', '## PRODUIT 1 — CAROUSEL "
            "CLASSIQUE (6 slides)', '## PRODUIT 1 — CAROUSEL CRÉATIF (6 "
            "slides)', puis les 4 mêmes titres pour PRODUIT 2. Ce format "
            "est lu automatiquement par un programme juste après ta tâche "
            "pour sauvegarder les légendes : un titre qui ne correspond pas "
            "exactement à ce format fait échouer cette sauvegarde "
            "automatique."
        ),
        expected_output=(
            "Tous les textes structurés par produit et par type de "
            "contenu, prêts à l'emploi, chacun précédé de son titre "
            "Markdown '## ...' exact comme précisé ci-dessus."
        ),
        agent=agent_redaction,
        context=[tache_saisonnalite, tache_cuisinier],
        callback=sauvegarder_legendes,
    )

    # ------------------------------------------------------------------
    # Tâche 4 — Photo Ingrédients (déplacée avant les carousels : les
    # slides 1-3 de chaque carousel utilisent cette photo comme fond)
    # ------------------------------------------------------------------
    tache_photo_ingredients = Task(
        description=(
            "Pour chacun des 4 carousels de la semaine (produit1_recette_"
            "classique, produit1_recette_creative, produit2_recette_"
            "classique, produit2_recette_creative), rédige un prompt Gemini "
            "précis en anglais représentant les ingrédients RÉELS et "
            "SPÉCIFIQUES de cette recette précise (classique ou créative — "
            "ils diffèrent, ne réutilise pas le même prompt pour les deux), "
            "en flat lay food photography (format paysage, lumière "
            "naturelle, fond marbre ou ardoise, props céramique et lin, vue "
            "de dessus, tons pastels, style éditorial). Appelle l'outil "
            "`generer_photo_ingredient` avec ce prompt et le nom de fichier "
            "cible '<nom_dossier_carousel>_ingredients.png' (ex. "
            "produit1_recette_classique_ingredients.png) — un seul appel "
            "par carousel, qui génère ET sauvegarde l'image en une fois, "
            "soit 4 appels au total. Ne demande jamais à voir le contenu de "
            "l'image générée, l'outil ne renvoie qu'un message de statut "
            "court. Si Gemini échoue pour un carousel, continue sans "
            "bloquer et signale clairement l'échec et son motif : les "
            "slides correspondantes utiliseront alors le fond crème teinté "
            "standard à la place de la photo."
        ),
        expected_output=(
            "Un récapitulatif des 4 photos (générées avec succès ou en "
            "échec, avec motif de l'échec le cas échéant)."
        ),
        agent=agent_photo_ingredients,
        context=[tache_saisonnalite, tache_cuisinier],
    )

    # ------------------------------------------------------------------
    # Tâches 5a-5d — Générateur Slides (carousels), une tâche par carousel
    # plutôt qu'une seule tâche de 24 appels d'outil : CrewAI réenvoie tout
    # l'historique de la tâche à chaque appel, donc le coût croît avec le
    # carré du nombre d'étapes — 4 tâches de 6 étapes coûtent nettement
    # moins au total qu'une tâche de 24 étapes, même en comptant le
    # backstory ré-envoyé 4 fois au lieu d'une.
    # ------------------------------------------------------------------
    taches_design_slides = []
    for nom_carousel in NOMS_CAROUSELS:
        taches_design_slides.append(
            Task(
                description=(
                    f"À partir du texte du carousel '{nom_carousel}' (6 "
                    "slides) rédigé par l'Agent Rédaction, et de la couleur "
                    "accent du produit concerné (guide de style), extrait "
                    "pour chaque slide un titre court et le corps (texte "
                    "déjà rédigé, ne reformule pas). Pour chaque slide, "
                    "appelle IMMÉDIATEMENT l'outil `generer_slide_png` (un "
                    "appel par slide, jamais plusieurs slides dans un même "
                    "appel) avec "
                    f"nom_dossier_carousel='{nom_carousel}', numero_slide "
                    "(1 à 6), titre, corps et couleur_accent — l'outil "
                    "construit lui-même le HTML/CSS et intègre "
                    "automatiquement la photo d'ingrédients spécifique à ce "
                    "carousel en fond des slides 1 à 3 si elle est "
                    "disponible. N'écris jamais de HTML toi-même. "
                    f"Occupe-toi UNIQUEMENT du carousel '{nom_carousel}' "
                    "(6 appels d'outil), pas des 3 autres carousels de la "
                    "semaine."
                ),
                expected_output=(
                    f"Un récapitulatif des 6 slides générées pour "
                    f"'{nom_carousel}', avec mention explicite des "
                    "éventuels échecs de génération."
                ),
                agent=agent_design_slides,
                context=[tache_redaction, tache_photo_ingredients],
            )
        )

    # ------------------------------------------------------------------
    # Tâche 6 — Générateur Stories
    # ------------------------------------------------------------------
    tache_design_stories = Task(
        description=(
            "À partir des fiches des 2 produits vedettes et de leurs "
            "recettes, rédige le texte (titre + corps) des 6 stories de la "
            "semaine : teaser lundi, le saviez-vous mardi, sondage "
            "mercredi, tip vendredi, question ouverte samedi, recap "
            "dimanche. Pour chaque story, appelle IMMÉDIATEMENT l'outil "
            "`generer_story_png` (un appel par story, jamais plusieurs "
            "stories dans un même appel) avec nom_fichier, titre, corps, "
            "couleur_accent, type_story (teaser/info/sondage/tip/"
            "question/recap), et selon le cas options_sondage ou "
            "couleur_accent_secondaire (pour le recap). N'écris jamais de "
            "HTML toi-même, l'outil construit la mise en page. Noms de "
            "fichiers dans l'ordre : story_01_lundi_teaser.png à "
            "story_06_dimanche_recap.png — soit 6 appels d'outil au total."
        ),
        expected_output=(
            "Un récapitulatif des 6 stories générées, avec mention "
            "explicite des éventuels échecs de génération."
        ),
        agent=agent_design_stories,
        context=[tache_saisonnalite, tache_cuisinier],
    )

    # ------------------------------------------------------------------
    # Tâche 7 — Briefs Vidéo (reel principal + reel satellite)
    # ------------------------------------------------------------------
    tache_briefs_video = Task(
        description=(
            "Pour le produit vedette n°1, rédige le brief complet du reel "
            "principal (45-60s, concept, 8-10 plans détaillés, setup, "
            "musique, textes écran, légendes Instagram et TikTok) en te "
            "basant sur sa recette créative. Puis rédige le brief du reel "
            "satellite (20-30s, recette complémentaire inédite à inventer, "
            "4-5 plans, légendes Instagram avec rappel du reel principal et "
            "TikTok). Les deux légendes TikTok doivent rappeler : exporter "
            "sans watermark, poster 3h après Instagram.\n\n"
            "Format obligatoire : précède le brief du reel principal par le "
            "titre Markdown EXACT '## REEL PRINCIPAL' (deux dièses, un "
            "espace, rien d'autre sur la ligne), et le brief du reel "
            "satellite par '## REEL SATELLITE'. Ce format est lu "
            "automatiquement par un programme juste après ta tâche pour "
            "sauvegarder les 2 briefs : un titre qui ne correspond pas "
            "exactement à ce format fait échouer cette sauvegarde "
            "automatique."
        ),
        expected_output=(
            "Les 2 briefs complets et structurés, chacun précédé de son "
            "titre Markdown '## REEL PRINCIPAL' / '## REEL SATELLITE' exact "
            "comme précisé ci-dessus."
        ),
        agent=agent_briefs_video,
        context=[tache_saisonnalite, tache_cuisinier],
        callback=sauvegarder_briefs,
    )

    # ------------------------------------------------------------------
    # Tâche 8 — Email Coach (orchestration finale)
    # ------------------------------------------------------------------
    tache_email_coach = Task(
        description=(
            f"La semaine en cours commence le lundi {date_lundi}. Dans cet "
            "ordre précis : 1) appelle l'outil `enregistrer_planning` avec "
            "date_semaine, une liste structurée `planning` (un dict par "
            "créneau lundi à dimanche : jour, heure, plateforme, type, "
            "statut — signale clairement tout échec de génération dans le "
            "statut) et une liste `checklist` de courtes chaînes ; 2) "
            "appelle `uploader_dossier_drive` pour uploader le dossier "
            "complet de la semaine sur Google Drive ; 3) appelle "
            "`envoyer_email_recap` avec seulement date_semaine et le lien "
            "Drive obtenu à l'étape 2 (ou le message d'erreur si l'upload a "
            "échoué). N'écris jamais de HTML toi-même : les outils "
            "construisent le planning et l'email à partir des données "
            "structurées que tu leur fournis."
        ),
        expected_output=(
            "Confirmation de l'upload Drive (ou message d'erreur "
            "explicite) et confirmation de l'envoi de l'email "
            "récapitulatif au coach."
        ),
        agent=agent_email_coach,
        context=[
            tache_saisonnalite,
            tache_cuisinier,
            tache_redaction,
            tache_photo_ingredients,
            *taches_design_slides,
            tache_design_stories,
            tache_briefs_video,
        ],
    )

    return [
        tache_saisonnalite,
        tache_cuisinier,
        tache_redaction,
        tache_photo_ingredients,
        *taches_design_slides,
        tache_design_stories,
        tache_briefs_video,
        tache_email_coach,
    ]
