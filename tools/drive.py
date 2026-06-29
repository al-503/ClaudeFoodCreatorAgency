# -*- coding: utf-8 -*-
"""
tools/drive.py — Upload du dossier hebdomadaire vers Google Drive.

Utilise une autorisation OAuth2 utilisateur (et non un compte de service)
pour uploader récursivement le dossier local de la semaine
(output/semaine_JJ_mois_AAAA/) dans un dossier racine Drive dédié à l'agence.

Pourquoi OAuth2 plutôt qu'un compte de service : certains comptes Google
Cloud appliquent par défaut une politique d'organisation qui interdit la
création de clés de compte de service ("Disable service account key
creation"), bloquant l'approche classique. L'autorisation OAuth2
utilisateur contourne ce blocage : elle se fait une seule fois en local via
`python autoriser_google_drive.py` (voir ce script et le README.md, section
"Configuration Google Drive API"), puis le token généré se rafraîchit
automatiquement à chaque run, y compris en CI.

Pourquoi le scope `drive.file` plutôt que `drive` complet : le scope
`drive` est classé "restreint" par Google et impose soit une vérification
de l'application, soit une expiration du refresh token au bout de 7 jours
tant que l'app reste en statut "Testing" — incompatible avec un cron
hebdomadaire fiable. Le scope `drive.file` n'a pas ces contraintes, en
contrepartie l'application ne voit que les fichiers/dossiers qu'elle a
elle-même créés (pas l'ensemble du Drive de l'utilisateur). C'est pour
cette raison que le dossier racine de l'agence est recherché puis créé
automatiquement par le code ci-dessous, plutôt que configuré une fois pour
toutes via un ID de dossier créé manuellement par l'utilisateur (qui serait
invisible pour l'app sous ce scope).
"""

import os
import json
import traceback

from crewai.tools import tool
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES_DRIVE = ["https://www.googleapis.com/auth/drive.file"]
TYPE_DOSSIER_DRIVE = "application/vnd.google-apps.folder"
NOM_DOSSIER_RACINE_AGENCE = "AgenceInstagram"


def _construire_service_drive():
    """
    Construit le client Google Drive API à partir d'un token OAuth2
    utilisateur, lu dans la variable d'environnement
    GOOGLE_OAUTH_TOKEN_JSON. Rafraîchit automatiquement le token d'accès
    s'il est expiré (le refresh_token, lui, n'expire pas sauf révocation
    manuelle par l'utilisateur, ou expiration à 7 jours si l'app Google
    Cloud associée est restée en statut "Testing" avec un scope restreint
    — non applicable ici puisqu'on utilise `drive.file`).
    """
    token_json = os.environ.get("GOOGLE_OAUTH_TOKEN_JSON")
    if not token_json:
        raise RuntimeError("Variable d'environnement GOOGLE_OAUTH_TOKEN_JSON manquante.")

    infos_token = json.loads(token_json)
    credentials = Credentials.from_authorized_user_info(infos_token, scopes=SCOPES_DRIVE)

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    return build("drive", "v3", credentials=credentials)


def _obtenir_ou_creer_dossier(service, nom_dossier: str, id_parent: str = None) -> str:
    """
    Recherche un dossier par nom (et par parent si précisé) parmi les
    fichiers déjà créés par l'application, et retourne son ID s'il existe.
    Sinon le crée.

    Centralise la logique de "find-or-create" utilisée à la fois pour le
    dossier racine de l'agence, le dossier de la semaine, et les
    sous-dossiers de carousels — c'est ce qui rend les relances multiples
    du pipeline dans la même semaine idempotentes côté Drive : sans cette
    recherche préalable, chaque relance créerait un nouveau dossier portant
    le même nom (Drive autorise les doublons de nom) au lieu de réutiliser
    celui déjà existant.
    """
    requete = (
        f"name = '{nom_dossier}' "
        f"and mimeType = '{TYPE_DOSSIER_DRIVE}' "
        "and trashed = false"
    )
    if id_parent:
        requete += f" and '{id_parent}' in parents"

    resultats = service.files().list(q=requete, fields="files(id, name)").execute()
    dossiers_trouves = resultats.get("files", [])
    if dossiers_trouves:
        return dossiers_trouves[0]["id"]

    metadonnees = {"name": nom_dossier, "mimeType": TYPE_DOSSIER_DRIVE}
    if id_parent:
        metadonnees["parents"] = [id_parent]
    dossier = service.files().create(body=metadonnees, fields="id").execute()
    return dossier["id"]


def _obtenir_ou_creer_dossier_racine(service) -> str:
    """
    Résout le dossier racine de l'agence (nommé "AgenceInstagram"), via
    GOOGLE_DRIVE_FOLDER_ID si fixé, sinon via recherche-ou-création.

    Sous le scope `drive.file`, la recherche ne porte que sur les fichiers
    que l'application a elle-même créés : un dossier créé manuellement par
    l'utilisateur via l'interface Drive ne serait pas trouvé ici, ce qui
    est le comportement attendu et la raison pour laquelle ce dossier
    racine est entièrement géré par le code plutôt que par configuration
    manuelle (voir GOOGLE_DRIVE_FOLDER_ID, devenu optionnel).
    """
    id_force = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")
    if id_force:
        return id_force

    id_dossier = _obtenir_ou_creer_dossier(service, NOM_DOSSIER_RACINE_AGENCE)
    print(
        f"Dossier racine '{NOM_DOSSIER_RACINE_AGENCE}' résolu sur Drive "
        f"(id: {id_dossier}). Tu peux optionnellement fixer "
        f"GOOGLE_DRIVE_FOLDER_ID={id_dossier} dans .env pour éviter une "
        f"recherche à chaque run, mais ce n'est pas obligatoire."
    )
    return id_dossier


def _obtenir_ou_creer_fichier(service, chemin_local: str, id_parent: str) -> str:
    """
    Uploade un fichier local dans le dossier Drive id_parent. Si un fichier
    du même nom existe déjà dans ce dossier (relance du pipeline dans la
    même semaine), remplace son CONTENU en place (files().update) plutôt
    que de créer un doublon — l'ID et le lien Drive restent stables entre
    deux relances.
    """
    nom_fichier = os.path.basename(chemin_local)
    requete = (
        f"name = '{nom_fichier}' "
        f"and '{id_parent}' in parents "
        "and trashed = false"
    )
    resultats = service.files().list(q=requete, fields="files(id, name)").execute()
    fichiers_trouves = resultats.get("files", [])
    media = MediaFileUpload(chemin_local, resumable=True)

    if fichiers_trouves:
        id_existant = fichiers_trouves[0]["id"]
        fichier = service.files().update(fileId=id_existant, media_body=media).execute()
        return fichier["id"]

    metadonnees = {"name": nom_fichier, "parents": [id_parent]}
    fichier = service.files().create(body=metadonnees, media_body=media, fields="id").execute()
    return fichier["id"]


def _uploader_dossier_recursif(service, chemin_local: str, id_parent_drive: str) -> int:
    """
    Reproduit récursivement l'arborescence de chemin_local dans Drive sous
    id_parent_drive. Retourne le nombre de fichiers uploadés avec succès.
    Les sous-dossiers vides ou les fichiers en échec n'interrompent pas
    le reste de l'upload. Réutilise les sous-dossiers et fichiers déjà
    existants (voir _obtenir_ou_creer_dossier / _obtenir_ou_creer_fichier)
    pour rester idempotent sur des relances répétées.
    """
    nb_fichiers_uploades = 0
    for entree in sorted(os.listdir(chemin_local)):
        chemin_entree = os.path.join(chemin_local, entree)
        if os.path.isdir(chemin_entree):
            try:
                id_sous_dossier = _obtenir_ou_creer_dossier(service, entree, id_parent_drive)
                nb_fichiers_uploades += _uploader_dossier_recursif(
                    service, chemin_entree, id_sous_dossier
                )
            except Exception:
                traceback.print_exc()
        else:
            try:
                _obtenir_ou_creer_fichier(service, chemin_entree, id_parent_drive)
                nb_fichiers_uploades += 1
            except Exception:
                traceback.print_exc()
    return nb_fichiers_uploades


@tool("uploader_dossier_drive")
def uploader_dossier_drive(chemin_local_racine: str, nom_dossier_semaine: str) -> str:
    """
    Uploade récursivement le dossier local de la semaine vers le dossier
    racine Drive de l'agence ("AgenceInstagram", retrouvé ou créé
    automatiquement), en recréant l'arborescence (stories/, carousels/,
    photos_ingredients/, legendes_et_briefs/, planning_coach.md).

    Idempotent sur des relances répétées dans la même semaine : le dossier
    "semaine_JJ_mois_AAAA" et chaque sous-dossier/fichier sont recherchés avant
    d'être créés, et un fichier déjà présent voit son contenu remplacé en
    place plutôt que dupliqué. Relancer le pipeline plusieurs fois la même
    semaine met donc à jour le même dossier Drive (même lien stable) au
    lieu d'empiler des dossiers/fichiers en double.

    Args:
        chemin_local_racine: chemin local du dossier de la semaine
            (ex. output/semaine_28_juin)
        nom_dossier_semaine: nom du dossier à créer ou réutiliser sur Drive
            (ex. "semaine_28_juin")

    Retourne le lien Google Drive du dossier en cas de succès, ou un
    message "ERREUR:" explicite en cas d'échec (le pipeline doit alors
    continuer et envoyer l'email en signalant l'échec d'upload).
    """
    try:
        service = _construire_service_drive()
        id_dossier_racine = _obtenir_ou_creer_dossier_racine(service)
        id_dossier_semaine = _obtenir_ou_creer_dossier(service, nom_dossier_semaine, id_dossier_racine)
        nb_fichiers = _uploader_dossier_recursif(service, chemin_local_racine, id_dossier_semaine)
        lien_drive = f"https://drive.google.com/drive/folders/{id_dossier_semaine}"
        return f"{nb_fichiers} fichiers uploadés avec succès. Lien Drive : {lien_drive}"
    except Exception as erreur:
        traceback.print_exc()
        return f"ERREUR: upload Google Drive échoué — {erreur}"
