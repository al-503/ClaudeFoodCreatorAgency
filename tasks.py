# -*- coding: utf-8 -*-
"""
tasks.py — Définition des tâches CrewAI exécutées en Process.sequential.

Chaque tâche est liée à son agent (voir agents.py) et reçoit en `context`
les tâches précédentes dont elle dépend, afin que CrewAI propage
automatiquement leurs sorties dans le contexte du LLM.

La fonction `creer_taches` est appelée depuis main.py avec le mois en cours
et la date du lundi — le choix des produits de saison est délégué à l'Agent
Cuisinier Saisonnier (tâche 1), qui n'a plus besoin de saison_data.py.

Ordre d'exécution : la génération des photos d'ingrédients (tâche 3) a été
placée avant la génération des carousels (tâches 4a-4d), pour que les photos
existent déjà sur disque quand les slides 1-3 en ont besoin comme fond.

Optimisations de coût :
- L'Agent Cuisinier Saisonnier remplace deux agents séparés (Saisonnalité +
  Cuisinier) : une seule tâche génère fiches produits + recettes classiques
  + recettes créatives, sans passer par saison_data.py.
- Sauvegarde légendes/briefs/liste de courses via callbacks Python (zéro
  coût LLM supplémentaire).
- Slides éclatées en 4 tâches d'une carousel chacune (coût quadratique
  évité vs une seule tâche de 24 appels d'outil).
"""

from crewai import Task

from agents import (
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
    sauvegarder_tous_les_ingredients,
)

NOMS_CAROUSELS = [
    "produit1_recette_classique",
    "produit1_recette_creative",
    "produit2_recette_classique",
    "produit2_recette_creative",
]

MOIS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


def creer_taches(mois: int, date_lundi: str, historique_produits: list = None) -> list:
    """
    Construit la liste ordonnée des 10 tâches de la semaine.

    Args:
        mois: numéro du mois en cours (1=janvier … 12=décembre), utilisé
            pour que l'Agent Cuisinier Saisonnier sache quels produits sont
            de saison sans passer par saison_data.py.
        date_lundi: date du lundi de la semaine en cours, format "JJ/MM/AAAA",
            utilisée dans le planning et l'email final.
        historique_produits: liste des dernières semaines {semaine, produits},
            transmise à l'agent pour éviter les répétitions.
    """
    historique_produits = historique_produits or []
    mois_nom = MOIS_FR[mois - 1]
    annee = date_lundi.split("/")[2]

    bloc_historique = ""
    if historique_produits:
        lignes = "\n".join(
            f"  - Semaine du {e['semaine']} : {', '.join(e['produits'])}"
            for e in historique_produits
        )
        bloc_historique = (
            f"\n\nProduits déjà publiés ces dernières semaines "
            f"(à éviter absolument pour varier le contenu) :\n{lignes}"
        )

    # ------------------------------------------------------------------
    # Tâche 1 — Chef Cuisinier Saisonnier
    # Remplace les deux anciennes tâches Saisonnalité + Cuisinier.
    # ------------------------------------------------------------------
    tache_cuisinier = Task(
        description=(
            f"Nous sommes au mois de {mois_nom} {annee} en France."
            f"{bloc_historique}\n\n"
            "Choisis 2 produits de saison, génère leurs fiches complètes "
            "(saison, variétés, origine, nutrition, conservation, anecdote "
            "historique, accords suggérés), leur recette classique ET leur "
            "recette créative, en suivant scrupuleusement tes instructions. "
            "Pour chaque liste d'ingrédients (classique ET créative), utilise "
            "EXACTEMENT l'étiquette '**Ingrédients :**' sur sa propre ligne "
            "suivie d'une liste à puces '- quantité ingrédient' pour 4 "
            "personnes — lue automatiquement pour la liste de courses. "
            "Commence ta réponse par la section '## PRODUITS CHOISIS' avec "
            "les noms exacts des 2 produits choisis — lue automatiquement "
            "pour mettre à jour l'historique."
        ),
        expected_output=(
            "Section '## PRODUITS CHOISIS' suivie des fiches complètes des "
            "2 produits (PRODUIT 1 et PRODUIT 2), chacune avec recette "
            "classique (incluant '**Ingrédients :**') et recette créative "
            "(incluant '**Ingrédients :**')."
        ),
        agent=agent_cuisinier,
        callback=sauvegarder_tous_les_ingredients,
    )

    # ------------------------------------------------------------------
    # Tâche 2 — Rédaction
    # ------------------------------------------------------------------
    tache_redaction = Task(
        description=(
            "À partir des fiches produits et des 4 recettes (classique + "
            "créative pour chacun des 2 produits), rédige pour chacun des "
            "4 carousels : le texte des 6 slides, une légende Instagram SEO "
            "(150-200 mots, 12 hashtags, question ouverte finale) et une "
            "légende TikTok SEO (80 mots max, accroche choc ligne 1, 3-5 "
            "hashtags) — en suivant scrupuleusement tes instructions. Aucun "
            "terme technique (\"CTA\", \"hook\"…) ne doit apparaître dans "
            "le texte final.\n\n"
            "Format obligatoire — précède CHAQUE section d'un titre "
            "Markdown de niveau 2 EXACT :\n"
            "Slides : '## PRODUIT 1 — CAROUSEL CLASSIQUE (6 slides)', "
            "'## PRODUIT 1 — CAROUSEL CRÉATIF (6 slides)', mêmes pour "
            "PRODUIT 2.\n"
            "Légendes : '## PRODUIT 1 — CLASSIQUE — INSTAGRAM', "
            "'## PRODUIT 1 — CLASSIQUE — TIKTOK', "
            "'## PRODUIT 1 — CRÉATIF — INSTAGRAM', "
            "'## PRODUIT 1 — CRÉATIF — TIKTOK', mêmes pour PRODUIT 2.\n"
            "Ces titres exacts sont lus automatiquement par un programme — "
            "un titre qui dévie fait échouer la sauvegarde automatique."
        ),
        expected_output=(
            "12 sections (4 × slides + 4 × Instagram + 4 × TikTok), "
            "chacune précédée de son titre Markdown exact, textes finaux "
            "prêts à l'emploi."
        ),
        agent=agent_redaction,
        context=[tache_cuisinier],
        callback=sauvegarder_legendes,
    )

    # ------------------------------------------------------------------
    # Tâche 3 — Photo Ingrédients (avant les carousels : les slides 1-3
    # utilisent cette photo comme fond)
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
            "bloquer et signale clairement l'échec et son motif."
        ),
        expected_output=(
            "Un récapitulatif des 4 photos (générées avec succès ou en "
            "échec, avec motif de l'échec le cas échéant)."
        ),
        agent=agent_photo_ingredients,
        context=[tache_cuisinier],
    )

    # ------------------------------------------------------------------
    # Tâches 4a-4d — Générateur Slides (carousels), une tâche par carousel
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
    # Tâche 5 — Générateur Stories
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
        context=[tache_cuisinier],
    )

    # ------------------------------------------------------------------
    # Tâche 6 — Brief Vidéo (guide de tournage générique)
    # ------------------------------------------------------------------
    tache_briefs_video = Task(
        description=(
            "À partir de la fiche du produit vedette n°1 et de ses recettes, "
            "rédige le guide de tournage vidéo de la semaine en suivant "
            "scrupuleusement tes instructions. Le guide doit être générique "
            "(utilisable quelle que soit la recette choisie le jour J) et "
            "inclure des éléments textuels concrets tirés de la fiche produit "
            "(anecdote, saisonnalité, question communauté) ainsi que les "
            "légendes Instagram et TikTok.\n\n"
            "Format obligatoire : commence ta réponse par le titre Markdown "
            "EXACT '## BRIEF VIDÉO' (deux dièses, un espace, rien d'autre "
            "sur la ligne). Ce titre est lu automatiquement par un programme "
            "pour sauvegarder le brief dans 'brief_video.md'."
        ),
        expected_output=(
            "Le guide de tournage complet (5 blocs + légendes), précédé du "
            "titre Markdown '## BRIEF VIDÉO' exact."
        ),
        agent=agent_briefs_video,
        context=[tache_cuisinier],
        callback=sauvegarder_briefs,
    )

    # ------------------------------------------------------------------
    # Tâche 7 — Email Coach (orchestration finale)
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
            tache_cuisinier,
            tache_redaction,
            tache_photo_ingredients,
            *taches_design_slides,
            tache_design_stories,
            tache_briefs_video,
        ],
    )

    return [
        tache_cuisinier,
        tache_redaction,
        tache_photo_ingredients,
        *taches_design_slides,
        tache_design_stories,
        tache_briefs_video,
        tache_email_coach,
    ]
