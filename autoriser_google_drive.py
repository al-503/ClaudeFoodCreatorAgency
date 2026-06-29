# -*- coding: utf-8 -*-
"""
autoriser_google_drive.py — Script à exécuter UNE SEULE FOIS en local pour
autoriser l'agence à accéder à ton Google Drive via OAuth2.

Pourquoi ce script existe :
Certains comptes Google Cloud appliquent par défaut une politique
d'organisation qui interdit la création de clés de compte de service
("Disable service account key creation"). Pour contourner ce blocage, ce
script utilise une autorisation OAuth2 utilisateur classique à la place :
tu autorises l'application une seule fois dans ton navigateur, et un token
de rafraîchissement est généré, valable indéfiniment (sauf révocation
manuelle de ta part).

Utilisation :
1. Dans Google Cloud Console > APIs & Services > Credentials,
   clique sur "Create Credentials" > "OAuth client ID", choisis le type
   d'application "Application de bureau" (Desktop app), puis télécharge
   le fichier JSON généré.
2. Renomme ce fichier `credentials_oauth.json` et place-le à la racine du
   projet (ce fichier est listé dans .gitignore : il ne sera jamais commité).
3. Lance : python autoriser_google_drive.py
4. Une page de ton navigateur s'ouvre automatiquement : connecte-toi avec
   le compte Google dédié au projet, puis accepte les permissions Drive.
5. Le script affiche le contenu JSON du token généré : copie-le tel quel
   dans la variable GOOGLE_OAUTH_TOKEN_JSON de ton fichier .env, et dans le
   secret GitHub du même nom pour l'automatisation via GitHub Actions.
"""

import sys

from google_auth_oauthlib.flow import InstalledAppFlow

# Scope volontairement restreint à drive.file (et non drive complet) : ce
# scope n'est pas classé "restreint" par Google, donc pas de vérification
# d'application requise ni d'expiration du refresh token à 7 jours, ce qui
# est indispensable pour un cron hebdomadaire fiable. En contrepartie,
# l'application ne voit que les fichiers/dossiers qu'elle crée elle-même
# (voir tools/drive.py, _obtenir_ou_creer_dossier_racine).
SCOPES_DRIVE = ["https://www.googleapis.com/auth/drive.file"]
FICHIER_CREDENTIALS_OAUTH = "credentials_oauth.json"


def main() -> None:
    try:
        flow = InstalledAppFlow.from_client_secrets_file(FICHIER_CREDENTIALS_OAUTH, SCOPES_DRIVE)
    except FileNotFoundError:
        print(
            f"ERREUR : fichier '{FICHIER_CREDENTIALS_OAUTH}' introuvable.\n"
            "Télécharge tes identifiants OAuth (type 'Application de bureau') "
            "depuis Google Cloud Console > APIs & Services > Credentials, et "
            f"place le fichier JSON téléchargé à la racine du projet sous le "
            f"nom '{FICHIER_CREDENTIALS_OAUTH}'."
        )
        sys.exit(1)

    # Ouvre une page dans le navigateur par défaut pour l'autorisation
    credentials = flow.run_local_server(port=0)

    token_json = credentials.to_json()
    print("\n=== Autorisation réussie ===")
    print(
        "Copie la ligne JSON ci-dessous dans GOOGLE_OAUTH_TOKEN_JSON de ton "
        "fichier .env, et dans le secret GitHub du même nom :\n"
    )
    print(token_json)


if __name__ == "__main__":
    main()
