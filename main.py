# -*- coding: utf-8 -*-
"""
main.py — Point d'entrée du pipeline hebdomadaire de l'agence.

Orchestre les 8 agents CrewAI en Process.sequential :
1. Charge les variables d'environnement (.env en local, secrets GitHub en CI)
2. Détermine les produits de saison du mois en cours
3. Prépare l'arborescence locale de sortie (output/semaine_JJ_mois_AAAA/...)
4. Construit et exécute le Crew CrewAI
5. Affiche le résultat final dans les logs

Déclenché chaque lundi 6h heure de Paris (4h UTC) par .github/workflows/agence.yml, ou
manuellement via `python main.py` ou `workflow_dispatch` sur GitHub Actions.
"""

import json
import os
import re
import sys
from datetime import date

from dotenv import load_dotenv
from crewai import Crew, Process

from saison_data import produits_du_mois
from utils import (
    date_lundi_semaine_courante,
    chemin_dossier_semaine,
    assurer_dossier,
)

FICHIER_HISTORIQUE = "historique_produits.json"
NB_SEMAINES_HISTORIQUE = 8  # fenêtre transmise à l'agent Saisonnalité


def charger_historique() -> list:
    """Retourne la liste des entrées {semaine, produits} déjà publiées."""
    if not os.path.exists(FICHIER_HISTORIQUE):
        return []
    with open(FICHIER_HISTORIQUE, encoding="utf-8") as f:
        return json.load(f)


def extraire_produits_choisis(texte: str, produits_disponibles: dict) -> list:
    """
    Cherche dans le texte de sortie de l'Agent Saisonnalité les noms de
    produits (clés de produits_disponibles) qui y apparaissent, et retourne
    les deux premiers trouvés — suffisant pour mettre à jour l'historique.
    """
    trouves = []
    for nom in produits_disponibles:
        motif = nom.replace("_", r"[\s_-]?")
        if re.search(rf"\b{motif}\b", texte, re.IGNORECASE) and nom not in trouves:
            trouves.append(nom)
        if len(trouves) == 2:
            break
    return trouves


def sauvegarder_historique(historique: list, date_lundi: str, nouveaux_produits: list) -> None:
    """Ajoute la semaine courante à l'historique et réécrit le fichier."""
    if not nouveaux_produits:
        return
    historique.append({"semaine": date_lundi, "produits": nouveaux_produits})
    with open(FICHIER_HISTORIQUE, "w", encoding="utf-8") as f:
        json.dump(historique, f, ensure_ascii=False, indent=2)


def preparer_arborescence_locale(dossier_semaine: str) -> None:
    """
    Crée l'arborescence locale attendue dans output/semaine_JJ_mois_AAAA/ avant
    de lancer le Crew, afin que les outils (tools/visuels.py, etc.) puissent
    écrire directement dans les bons sous-dossiers.
    """
    assurer_dossier(dossier_semaine)
    assurer_dossier(os.path.join(dossier_semaine, "stories"))
    assurer_dossier(os.path.join(dossier_semaine, "carousels"))
    assurer_dossier(os.path.join(dossier_semaine, "photos_ingredients"))
    assurer_dossier(os.path.join(dossier_semaine, "legendes_et_briefs"))


def verifier_variables_environnement_requises() -> None:
    """
    Vérifie la présence des variables d'environnement indispensables avant
    de lancer le pipeline, pour échouer immédiatement avec un message clair
    plutôt qu'au milieu de l'exécution du Crew (qui coûte du temps et des
    appels API inutiles).
    """
    # GOOGLE_DRIVE_FOLDER_ID est volontairement absent de cette liste : sous
    # le scope drive.file, le dossier racine de l'agence est retrouvé ou
    # créé automatiquement par tools/drive.py (_obtenir_ou_creer_dossier_racine).
    # Cette variable reste utilisable en override optionnel si on veut fixer
    # un dossier précis, mais n'est plus indispensable.
    variables_requises = [
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "EMAIL_SENDER",
        "EMAIL_RECEIVER",
        "EMAIL_PASSWORD",
        "GOOGLE_OAUTH_TOKEN_JSON",
    ]
    manquantes = [nom for nom in variables_requises if not os.environ.get(nom)]
    if manquantes:
        print(
            "ERREUR DE CONFIGURATION : variables d'environnement manquantes : "
            f"{', '.join(manquantes)}.\n"
            "Vérifie ton fichier .env en local, ou les GitHub Secrets en CI "
            "(voir les instructions en bas de ce fichier)."
        )
        sys.exit(1)


def main() -> None:
    load_dotenv()  # ne fait rien en CI (pas de fichier .env), utile en local
    verifier_variables_environnement_requises()

    # Import différé : tasks.py importe agents.py, qui construit le LLM et
    # lit les clés API. On veut que la vérification ci-dessus s'exécute
    # avant, pour un message d'erreur plus lisible en cas d'oubli.
    from tasks import creer_taches
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

    aujourd_hui = date.today()
    lundi = date_lundi_semaine_courante()
    dossier_semaine = chemin_dossier_semaine(lundi)
    preparer_arborescence_locale(dossier_semaine)

    produits_disponibles = produits_du_mois(aujourd_hui.month)
    if not produits_disponibles:
        print(
            f"ERREUR : aucun produit de saison trouvé pour le mois {aujourd_hui.month}. "
            "Vérifie saison_data.py."
        )
        sys.exit(1)

    historique = charger_historique()
    semaines_recentes = historique[-NB_SEMAINES_HISTORIQUE:]

    taches = creer_taches(
        produits_disponibles=produits_disponibles,
        date_lundi=lundi.strftime("%d/%m/%Y"),
        historique_produits=semaines_recentes,
    )

    equipe = Crew(
        agents=[
            agent_saisonnalite,
            agent_cuisinier,
            agent_redaction,
            agent_design_slides,
            agent_design_stories,
            agent_photo_ingredients,
            agent_briefs_video,
            agent_email_coach,
        ],
        tasks=taches,
        process=Process.sequential,
        verbose=True,
    )

    print(f"=== Lancement du pipeline hebdomadaire — semaine du {lundi.strftime('%d/%m/%Y')} ===")
    try:
        resultat = equipe.kickoff()
        print("=== Pipeline terminé avec succès ===")
        print(resultat)

        # Mise à jour de l'historique produits pour éviter les répétitions
        # la semaine suivante. On cherche les noms de produits dans la sortie
        # de la première tâche (Agent Saisonnalité).
        texte_saisonnalite = resultat.tasks_output[0].raw if resultat.tasks_output else ""
        produits_choisis = extraire_produits_choisis(texte_saisonnalite, produits_disponibles)
        sauvegarder_historique(historique, lundi.strftime("%d/%m/%Y"), produits_choisis)
        if produits_choisis:
            print(f"Historique mis à jour : {produits_choisis}")

        usage = equipe.usage_metrics
        if usage:
            pourcentage_cache = (
                100 * usage.cached_prompt_tokens / usage.prompt_tokens
                if usage.prompt_tokens
                else 0
            )
            print(
                "=== Usage tokens (vérification du prompt caching) ===\n"
                f"Prompt tokens          : {usage.prompt_tokens}\n"
                f"  dont tokens en cache  : {usage.cached_prompt_tokens} "
                f"({pourcentage_cache:.1f}% du prompt servi depuis le cache)\n"
                f"Tokens d'écriture cache : {usage.cache_creation_tokens}\n"
                f"Completion tokens      : {usage.completion_tokens}\n"
                f"Total tokens           : {usage.total_tokens}\n"
                f"Requêtes réussies      : {usage.successful_requests}"
            )
    except Exception as erreur:
        # Une erreur inattendue et non gérée localement par un agent/outil
        # (ex: clé API invalide, crash CrewAI) doit faire échouer le run
        # GitHub Actions pour alerter le coach, contrairement aux échecs
        # "attendus" (Gemini indisponible, visuel raté) qui sont eux gérés
        # à l'intérieur des outils et simplement notés dans le planning.
        print(f"ERREUR CRITIQUE : le pipeline s'est interrompu — {erreur}")
        sys.exit(1)


if __name__ == "__main__":
    main()


# ----------------------------------------------------------------------
# CONFIGURATION DES GITHUB SECRETS (à faire une seule fois par dépôt)
# ----------------------------------------------------------------------
# Dans GitHub : Settings > Secrets and variables > Actions > New repository
# secret. Ajouter les secrets suivants (voir README.md pour le détail de
# chaque procédure d'obtention) :
#
#   ANTHROPIC_API_KEY          → clé API Claude (console.anthropic.com)
#   GEMINI_API_KEY              → clé API Gemini (aistudio.google.com/app/apikey)
#   EMAIL_SENDER                → adresse Gmail d'envoi
#   EMAIL_RECEIVER               → adresse Gmail de réception du récap
#   EMAIL_PASSWORD               → mot de passe d'application Gmail (pas le
#                                  mot de passe principal du compte)
#   GOOGLE_OAUTH_TOKEN_JSON       → contenu JSON du token OAuth2, généré une
#                                  seule fois en local via
#                                  `python autoriser_google_drive.py`
#   GOOGLE_DRIVE_FOLDER_ID        → optionnel : sous le scope drive.file, le
#                                  dossier racine "AgenceInstagram" est
#                                  retrouvé ou créé automatiquement. Ne
#                                  fixer ce secret que si tu veux forcer un
#                                  dossier précis.
#
# Une fois les secrets configurés, le workflow .github/workflows/agence.yml
# s'exécute automatiquement chaque lundi à 6h heure de Paris (4h UTC), et peut aussi être
# déclenché manuellement depuis l'onglet "Actions" du dépôt GitHub grâce à
# `workflow_dispatch` (bouton "Run workflow"), sans attendre le lundi.
# ----------------------------------------------------------------------
