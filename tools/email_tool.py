# -*- coding: utf-8 -*-
"""
tools/email_tool.py — Planning hebdomadaire et envoi de l'email récapitulatif.

Deux outils, volontairement séparés et à arguments structurés courts
(jamais un long bloc de texte libre en un seul argument) :
1. `enregistrer_planning` : écrit planning_coach.md à partir de données
   structurées (liste de dicts), pour qu'il soit inclus dans l'upload
   Drive.
2. `envoyer_email_recap` : relit ce fichier déjà écrit sur disque et
   construit l'email HTML via un template Python (tools/templates.py),
   sans jamais demander au LLM de produire le HTML complet de l'email —
   un précédent test a montré qu'un tel argument volumineux fait échouer
   l'appel d'outil de façon répétée (champ manquant côté LLM).

Utilise un mot de passe d'application Gmail (et non le mot de passe
principal du compte), voir README.md section "Configuration Gmail SMTP".
"""

import os
import smtplib
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from crewai.tools import tool

from utils import chemin_dossier_semaine
from tools.templates import construire_markdown_planning, construire_html_email

SERVEUR_SMTP_GMAIL = "smtp.gmail.com"
PORT_SMTP_SSL = 465
NOM_FICHIER_PLANNING = "planning_coach.md"


@tool("enregistrer_planning")
def enregistrer_planning(date_semaine: str, planning: list, checklist: list) -> str:
    """
    Écrit le fichier planning_coach.md à la racine du dossier de la
    semaine, à partir de données structurées (pas de texte libre long).

    Args:
        date_semaine: ex. "28/06/2026"
        planning: liste de dicts, un par ligne de planning, avec les clés
            "jour", "heure", "plateforme", "type", "statut"
            (ex. {"jour": "Lundi", "heure": "18h", "plateforme": "Instagram",
            "type": "Story teaser", "statut": "Prêt"})
        checklist: liste de chaînes courtes, ex.
            ["2 sessions cuisine", "2 sessions photo", "4 publications TikTok"]

    Retourne un message de confirmation, ou un message "ERREUR:" explicite.
    À appeler AVANT `uploader_dossier_drive`, pour que ce fichier soit
    inclus dans l'upload.
    """
    try:
        contenu = construire_markdown_planning(date_semaine, planning, checklist)
        chemin = os.path.join(chemin_dossier_semaine(), NOM_FICHIER_PLANNING)
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(contenu)
        return f"'{NOM_FICHIER_PLANNING}' enregistré avec succès dans {chemin}."
    except Exception as erreur:
        traceback.print_exc()
        return f"ERREUR: enregistrement de '{NOM_FICHIER_PLANNING}' échoué — {erreur}"


@tool("envoyer_email_recap")
def envoyer_email_recap(date_semaine: str, lien_drive: str) -> str:
    """
    Envoie l'email récapitulatif hebdomadaire au coach via SMTP Gmail. Le
    contenu HTML est construit automatiquement à partir du fichier
    planning_coach.md déjà écrit par `enregistrer_planning` (qui doit donc
    être appelé avant cet outil) : aucun contenu HTML à fournir ici.

    Args:
        date_semaine: ex. "28/06/2026"
        lien_drive: URL du dossier Drive de la semaine, ou message
            "ERREUR: ..." si l'upload a échoué (l'email le signale alors
            clairement au lieu d'afficher un bouton cassé)

    Retourne un message de confirmation, ou un message "ERREUR:" explicite
    en cas d'échec (identifiants invalides, serveur SMTP indisponible...).
    """
    expediteur = os.environ.get("EMAIL_SENDER")
    destinataire = os.environ.get("EMAIL_RECEIVER")
    mot_de_passe = os.environ.get("EMAIL_PASSWORD")

    if not all([expediteur, destinataire, mot_de_passe]):
        return (
            "ERREUR: variables d'environnement EMAIL_SENDER, EMAIL_RECEIVER "
            "ou EMAIL_PASSWORD manquantes."
        )

    chemin_planning = os.path.join(chemin_dossier_semaine(), NOM_FICHIER_PLANNING)
    contenu_planning = ""
    if os.path.isfile(chemin_planning):
        with open(chemin_planning, "r", encoding="utf-8") as f:
            contenu_planning = f.read()

    contenu_html = construire_html_email(date_semaine, lien_drive, contenu_planning)

    # Une version texte brut en plus du HTML : un email HTML sans
    # alternative texte est un signal classique de spam pour de nombreux
    # filtres (dont ceux des FAI français comme SFR/Orange).
    #
    # Le lien Drive lui-même n'apparaît JAMAIS ici (ni en HTML, ni en texte
    # brut) : un email contenant une URL drive.google.com, même en texte
    # brut sans aucun HTML, a été testé et rejeté par le filtre anti-spam
    # de SFR (550 rejected per spam policy) — ce domaine est un vecteur de
    # phishing trop courant. Voir tools/templates.py::construire_html_email
    # pour le détail de ce diagnostic.
    upload_ok = bool(lien_drive) and not lien_drive.startswith("ERREUR")
    ligne_drive = (
        "Disponible dans ton dossier Drive habituel (AgenceInstagram), "
        "sous-dossier de cette semaine."
        if upload_ok
        else "Le dossier Drive n'a pas pu être uploadé automatiquement cette "
        "semaine — à faire manuellement."
    )
    contenu_texte = (
        f"Bonjour,\n\n"
        f"Le dossier de la semaine du {date_semaine} est prêt.\n\n"
        f"Dossier Drive : {ligne_drive}\n\n"
        f"{contenu_planning}"
    )

    message = MIMEMultipart("alternative")
    # Subject volontairement sobre et personnel (pas de formulation type
    # notification automatique "votre document est prêt") : ce type de
    # phrase déclenche les filtres anti-phishing de certains FAI (SFR
    # notamment), voir aussi construire_html_email dans tools/templates.py.
    message["Subject"] = f"Planning de la semaine du {date_semaine}"
    message["From"] = expediteur
    message["To"] = destinataire
    # Ordre important : la partie texte brut doit être attachée AVANT le
    # HTML (le client mail affiche la dernière partie qu'il sait rendre).
    message.attach(MIMEText(contenu_texte, "plain", "utf-8"))
    message.attach(MIMEText(contenu_html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL(SERVEUR_SMTP_GMAIL, PORT_SMTP_SSL) as serveur:
            serveur.login(expediteur, mot_de_passe)
            serveur.sendmail(expediteur, destinataire, message.as_string())
        return f"Email envoyé avec succès à {destinataire}."
    except Exception as erreur:
        traceback.print_exc()
        return f"ERREUR: envoi de l'email échoué — {erreur}"
