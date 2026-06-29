# 🌿 Agence Instagram/TikTok Automatisée — Créateur Food Saison

Agence de communication 100% automatisée pour un créateur de contenu food spécialisé fruits et légumes de saison en France. Une équipe de 8 agents IA (CrewAI + Claude) produit chaque semaine l'intégralité du contenu Instagram/TikTok : posts, carousels, stories, photos d'ingrédients, briefs vidéo, et un email récapitulatif avec planning de publication.

## Sommaire

1. [Architecture](#architecture)
2. [Installation](#installation)
3. [Configuration des API](#configuration-des-api)
4. [Configuration Google Drive API](#configuration-google-drive-api)
5. [Configuration Gmail SMTP](#configuration-gmail-smtp)
6. [GitHub Secrets](#github-secrets)
7. [Premier test manuel](#premier-test-manuel)
8. [Fonctionnement hebdomadaire](#fonctionnement-hebdomadaire)
9. [Étendre la base de données produits](#étendre-la-base-de-données-produits)

---

## Architecture

```
mon_agence/
├── main.py              ← point d'entrée, orchestration CrewAI
├── agents.py            ← définition des 8 agents
├── tasks.py             ← définition des tâches CrewAI
├── tools/               ← outils custom (visuels, Drive, email)
├── utils.py             ← chargeur de prompts depuis prompts/*.md
├── saison_data.py       ← base de données des produits de saison
├── prompts/             ← prompts métier de chaque agent (français)
└── .github/workflows/   ← déclenchement automatique cron
```

Les 8 agents s'exécutent en séquence (`Process.sequential`) :

| # | Agent | Rôle |
|---|-------|------|
| 1 | Saisonnalité | Choisit 2 produits vedettes du mois |
| 2 | Cuisinier créatif | Invente 2 recettes originales |
| 3 | Rédaction | Écrit posts, légendes, carousels |
| 4 | Générateur slides | Génère le HTML → PNG des carousels |
| 5 | Générateur stories | Génère le HTML → PNG des 6 stories |
| 6 | Photo ingrédients | Génère 2 photos via Gemini Imagen 3 |
| 7 | Briefs vidéo | Rédige les briefs reels principal/satellite |
| 8 | Email coach | Upload Drive + envoi email récapitulatif |

---

## Installation

### Pré-requis

- Python 3.11+
- Un compte Google Cloud avec l'API Drive activée
- Une clé API Anthropic (Claude)
- Une clé API Google Gemini
- Un compte Gmail avec un mot de passe d'application (App Password)

### Étapes

```bash
# 1. Cloner le dépôt
git clone <votre-repo>
cd mon_agence

# 2. Créer un environnement virtuel
python3.11 -m venv venv
source venv/bin/activate   # Windows : venv\Scripts\activate

# 3. Installer les dépendances Python
pip install -r requirements.txt

# 4. Installer le navigateur headless pour Playwright (génération des visuels)
playwright install chromium

# 5. Copier le fichier d'environnement
cp .env.example .env
```

Puis éditez `.env` avec vos propres clés (voir sections suivantes).

---

## Configuration des API

### Clé Anthropic (Claude)

1. Créez un compte sur https://console.anthropic.com
2. Générez une clé API dans "API Keys"
3. Renseignez-la dans `.env` : `ANTHROPIC_API_KEY=sk-ant-...`

### Clé Gemini (Imagen 3)

1. Rendez-vous sur https://aistudio.google.com/app/apikey
2. Générez une clé API Gemini
3. Renseignez-la dans `.env` : `GEMINI_API_KEY=AI...`

> ⚠️ L'accès à Imagen 3 peut nécessiter un projet Google Cloud avec facturation activée selon votre quota. Si l'appel échoue, le pipeline continue sans la photo (voir gestion d'erreurs dans `tools/visuels.py`).

---

## Configuration Google Drive API

L'agence utilise une **autorisation OAuth2 utilisateur** (et non un compte
de service) pour accéder à Google Drive. Pourquoi : certains comptes
Google Cloud appliquent par défaut une politique d'organisation qui
interdit la création de clés de compte de service ("Disable service
account key creation"), ce qui bloque l'approche classique. L'OAuth2
utilisateur contourne ce blocage : une seule autorisation manuelle dans le
navigateur, puis tout se rafraîchit automatiquement, y compris en CI.

Le scope demandé est volontairement `drive.file` et non `drive` complet :
ce dernier est classé "scope restreint" par Google, ce qui impose soit une
vérification officielle de l'application, soit une expiration du refresh
token au bout de 7 jours tant que l'app reste en statut "Testing" —
incompatible avec un cron hebdomadaire fiable. Avec `drive.file`, aucune de
ces contraintes ne s'applique. En contrepartie, l'application ne voit que
les fichiers/dossiers qu'elle a elle-même créés : le dossier racine de
l'agence ("AgenceInstagram") est donc retrouvé ou créé automatiquement par
le code (`tools/drive.py`), pas configuré manuellement.

1. Allez sur https://console.cloud.google.com/
2. Créez un nouveau projet (ou réutilisez un projet existant)
3. Activez l'API "Google Drive API" (menu *APIs & Services* → *Library*)
4. Configurez l'écran de consentement OAuth (*APIs & Services* → *OAuth consent screen*) :
   - Type d'utilisateur : **"External"**
   - Renseignez nom de l'app, email d'assistance et email développeur
   - Section "Test users" : ajoutez votre propre adresse Gmail dédiée au projet
5. Allez dans *APIs & Services* → *Credentials* → *Create Credentials* → *OAuth client ID*
   - Type d'application : **"Desktop app"** (application de bureau)
   - Téléchargez le fichier JSON généré
6. Renommez ce fichier `credentials_oauth.json` et placez-le à la racine du projet (déjà listé dans `.gitignore`, il ne sera jamais commité)
7. Lancez le script d'autorisation unique :
   ```bash
   python autoriser_google_drive.py
   ```
   Une page de votre navigateur s'ouvre : connectez-vous avec le compte Google dédié au projet, passez l'avertissement "Google n'a pas vérifié cette application" (normal pour un usage personnel, via "Paramètres avancés" → "Accéder à... (non sécurisé)"), puis acceptez les permissions Drive.
8. Le script affiche un JSON en sortie : copiez-le tel quel dans `.env` sous `GOOGLE_OAUTH_TOKEN_JSON`

> Ce script n'est à exécuter qu'une seule fois (sauf si vous révoquez l'accès manuellement). Le token se rafraîchit automatiquement à chaque run du pipeline, en local comme sur GitHub Actions. `GOOGLE_DRIVE_FOLDER_ID` est optionnel : ne le renseignez que si vous voulez forcer un dossier racine précis (qui doit alors avoir été créé par l'application elle-même).

---

## Configuration Gmail SMTP

L'envoi d'email utilise un mot de passe d'application Gmail (et non votre mot de passe principal) :

1. Activez la validation en 2 étapes sur votre compte Google : https://myaccount.google.com/security
2. Allez sur https://myaccount.google.com/apppasswords
3. Générez un mot de passe d'application pour "Mail"
4. Renseignez dans `.env` :
   - `EMAIL_SENDER=votre@gmail.com`
   - `EMAIL_RECEIVER=votre@gmail.com` (peut être la même adresse ou une autre)
   - `EMAIL_PASSWORD=xxxx xxxx xxxx xxxx` (le mot de passe d'application, avec ou sans espaces)

---

## GitHub Secrets

Pour que le workflow GitHub Actions (`.github/workflows/agence.yml`) fonctionne, ajoutez les secrets suivants dans votre dépôt GitHub :

`Settings` → `Secrets and variables` → `Actions` → `New repository secret`

| Nom du secret | Valeur |
|---|---|
| `ANTHROPIC_API_KEY` | Votre clé API Anthropic |
| `GEMINI_API_KEY` | Votre clé API Gemini |
| `EMAIL_SENDER` | Adresse Gmail d'envoi |
| `EMAIL_RECEIVER` | Adresse Gmail de réception |
| `EMAIL_PASSWORD` | Mot de passe d'application Gmail |
| `GOOGLE_OAUTH_TOKEN_JSON` | Contenu JSON du token OAuth2, généré via `python autoriser_google_drive.py` |
| `GOOGLE_DRIVE_FOLDER_ID` | Optionnel : voir section Google Drive API ci-dessus |

---

## Premier test manuel

### En local

```bash
source venv/bin/activate
python main.py
```

Le pipeline complet s'exécute : sélection des produits, recettes, rédaction, génération des visuels, photos, briefs vidéo, upload Drive et envoi de l'email récapitulatif. Les fichiers générés localement sont stockés dans `output/` (ignoré par git).

### Sur GitHub Actions (sans attendre le lundi)

1. Allez dans l'onglet `Actions` de votre dépôt GitHub
2. Sélectionnez le workflow `Agence Instagram — Lundi matin`
3. Cliquez sur `Run workflow` (bouton disponible grâce à `workflow_dispatch`)
4. Suivez l'exécution dans les logs

---

## Fonctionnement hebdomadaire

Chaque lundi à 6h heure de Paris (`cron: '0 4 * * 1'` en UTC), GitHub Actions déclenche automatiquement `main.py` qui :

1. Sélectionne les 2 produits vedettes de la semaine selon le mois en cours
2. Génère 2 recettes créatives inédites
3. Rédige tous les textes (posts, légendes, carousels)
4. Génère les visuels (carousels + stories) en PNG via Playwright
5. Génère les photos d'ingrédients via Gemini Imagen 3
6. Rédige les briefs vidéo (reel principal + satellite)
7. Uploade tout le dossier sur Google Drive
8. Envoie un email récapitulatif avec planning et lien Drive

Si une étape échoue (ex : Gemini indisponible), le pipeline **continue** et note l'échec dans `planning_coach.md` plutôt que d'interrompre toute la semaine.

---

## Étendre la base de données produits

Voir les instructions en commentaire en tête de [saison_data.py](saison_data.py). En résumé : ajoutez une entrée dans le dictionnaire `PRODUITS` avec les mêmes clés que les fiches existantes (`saison`, `varietes`, `origine`, `nutrition`, `conservation`, `anecdote_historique`, `recette_emblematique`, `accords_suggeres`).
