# -*- coding: utf-8 -*-
"""
tools/post_traitement.py — Sauvegarde des légendes et briefs vidéo via
callback CrewAI, sans appel LLM supplémentaire.

Avant cette version, sauvegarder ces textes nécessitait deux tâches CrewAI
dédiées où l'agent devait RETAPER le texte déjà généré comme argument d'un
outil (`enregistrer_contenu_texte`) — un texte déjà payé une fois comme
sortie de la tâche de rédaction était donc regénéré une seconde fois comme
sortie de la tâche de sauvegarde (les tokens de sortie sont les plus chers
côté facturation Claude). Ici, on récupère directement le texte brut déjà
produit (`TaskOutput.raw`) via le paramètre `callback` de `Task` (CrewAI
l'appelle automatiquement avec la sortie, juste après la fin de la tâche,
donc avant que la tâche suivante ne démarre) et on le découpe nous-mêmes en
Python — coût zéro, aucun aller-retour LLM.

Contrepartie : ce découpage repose sur des titres Markdown stricts
("## PRODUIT 1 — POST INSTAGRAM", "## REEL PRINCIPAL", etc.) que les
prompts des agents concernés imposent désormais explicitement. Si un titre
attendu est introuvable (agent qui dévie du format), le fichier
correspondant n'est simplement pas écrit et un avertissement est affiché
sur la sortie standard — comme pour tout le reste du pipeline, un échec
partiel ne doit jamais bloquer la suite.
"""

import os
import re

from utils import chemin_dossier_semaine, assurer_dossier

NOM_SOUS_DOSSIER = "legendes_et_briefs"


def _decouper_sections_markdown(texte: str) -> dict:
    """
    Découpe un texte en sections délimitées par des titres Markdown de
    niveau 2 ("## Titre"), retourne {titre: corps}. Les titres apparaissant
    plusieurs fois écrasent les précédents (ne devrait pas arriver avec des
    prompts bien structurés).
    """
    morceaux = re.split(r"^##[ \t]+(.+?)[ \t]*$", texte, flags=re.MULTILINE)
    sections = {}
    for i in range(1, len(morceaux), 2):
        titre = morceaux[i].strip()
        corps = morceaux[i + 1].strip() if i + 1 < len(morceaux) else ""
        sections[titre] = corps
    return sections


def _trouver_section(sections: dict, *mots_cles: str) -> str | None:
    """
    Cherche la première section dont le titre contient tous les mots-clés
    donnés, insensible à la casse et aux variantes de tiret (-, —, –).
    """
    for titre, corps in sections.items():
        titre_normalise = titre.upper().replace("—", "-").replace("–", "-")
        if all(mot.upper() in titre_normalise for mot in mots_cles):
            return corps
    return None


def _ecrire_fichier_legende(nom_fichier: str, contenu: str) -> None:
    dossier_cible = os.path.join(chemin_dossier_semaine(), NOM_SOUS_DOSSIER)
    assurer_dossier(dossier_cible)
    chemin_sortie = os.path.join(dossier_cible, nom_fichier)
    with open(chemin_sortie, "w", encoding="utf-8") as f:
        f.write(contenu)


def _sauvegarder_sections(texte_brut: str, fichiers_attendus: list, nom_source: str) -> None:
    sections = _decouper_sections_markdown(texte_brut)
    for nom_fichier, mots_cles in fichiers_attendus:
        corps = _trouver_section(sections, *mots_cles)
        if corps:
            _ecrire_fichier_legende(nom_fichier, corps)
        else:
            print(
                f"AVERTISSEMENT post-traitement : section {mots_cles} introuvable "
                f"dans la sortie de {nom_source} — '{nom_fichier}' non sauvegardé."
            )


def sauvegarder_legendes(task_output) -> None:
    """
    Callback de `tache_redaction` (voir tasks.py) : extrait les 4 légendes
    (post Instagram + TikTok pour chaque produit) et les écrit directement
    sur disque, sans appel LLM.
    """
    _sauvegarder_sections(
        task_output.raw,
        [
            ("produit1_post_instagram.md", ("PRODUIT 1", "POST INSTAGRAM")),
            ("produit1_legende_tiktok.md", ("PRODUIT 1", "TIKTOK")),
            ("produit2_post_instagram.md", ("PRODUIT 2", "POST INSTAGRAM")),
            ("produit2_legende_tiktok.md", ("PRODUIT 2", "TIKTOK")),
        ],
        "l'Agent Rédaction",
    )


_REGEX_BLOC_INGREDIENTS = re.compile(
    r"\*\*Ingrédients\s*:?\*\*\s*\n((?:[ \t]*[-*•][ \t]*.+\n?)+)",
    flags=re.IGNORECASE,
)


def _extraire_lignes_ingredients(texte: str) -> list:
    """
    Trouve chaque bloc précédé de l'étiquette exacte '**Ingrédients :**'
    et retourne la liste à plat de toutes ses lignes à puces (puce
    retirée, espaces nettoyés). Plusieurs blocs (un par produit) sont
    concaténés dans l'ordre d'apparition.
    """
    lignes = []
    for bloc in _REGEX_BLOC_INGREDIENTS.findall(texte):
        for ligne in bloc.splitlines():
            ligne_nettoyee = re.sub(r"^[ \t]*[-*•][ \t]*", "", ligne).strip()
            if ligne_nettoyee:
                lignes.append(ligne_nettoyee)
    return lignes


def _ajouter_a_liste_courses(lignes: list, nouveau_fichier: bool) -> None:
    dossier_cible = os.path.join(chemin_dossier_semaine(), NOM_SOUS_DOSSIER)
    assurer_dossier(dossier_cible)
    chemin_sortie = os.path.join(dossier_cible, "liste_courses.md")
    mode = "w" if nouveau_fichier else "a"
    with open(chemin_sortie, mode, encoding="utf-8") as f:
        if nouveau_fichier:
            f.write("# Liste de courses (brute, non triée)\n\n")
        for ligne in lignes:
            f.write(f"- {ligne}\n")


def sauvegarder_tous_les_ingredients(task_output) -> None:
    """
    Callback de `tache_cuisinier` (voir tasks.py) : extrait TOUS les blocs
    '**Ingrédients :**' présents dans la sortie (recettes classiques ET
    créatives des 2 produits) et (re)crée `liste_courses.md` depuis zéro.
    """
    lignes = _extraire_lignes_ingredients(task_output.raw)
    if not lignes:
        print(
            "AVERTISSEMENT post-traitement : aucun bloc '**Ingrédients :**' "
            "trouvé dans la sortie de l'Agent Cuisinier Saisonnier — liste "
            "de courses non générée."
        )
    _ajouter_a_liste_courses(lignes, nouveau_fichier=True)


def sauvegarder_ingredients_classiques(task_output) -> None:
    """
    Callback de `tache_saisonnalite` (voir tasks.py) : extrait les
    ingrédients des 2 recettes emblématiques et (re)crée
    `liste_courses.md` avec ces lignes — sans appel LLM. Premier
    callback de la liste de courses dans l'ordre du pipeline, donc il
    recrée le fichier depuis zéro (idempotent en cas de re-run).
    """
    lignes = _extraire_lignes_ingredients(task_output.raw)
    if not lignes:
        print(
            "AVERTISSEMENT post-traitement : aucun bloc '**Ingrédients :**' "
            "trouvé dans la sortie de l'Agent Saisonnalité — liste de "
            "courses incomplète pour les recettes classiques."
        )
    _ajouter_a_liste_courses(lignes, nouveau_fichier=True)


def sauvegarder_ingredients_creatifs(task_output) -> None:
    """
    Callback de `tache_cuisinier` (voir tasks.py) : extrait les
    ingrédients des 2 recettes créatives et les ajoute à la suite de
    `liste_courses.md` (déjà créé par `sauvegarder_ingredients_classiques`
    juste avant dans le pipeline) — sans appel LLM.
    """
    lignes = _extraire_lignes_ingredients(task_output.raw)
    if not lignes:
        print(
            "AVERTISSEMENT post-traitement : aucun bloc '**Ingrédients :**' "
            "trouvé dans la sortie de l'Agent Cuisinier — liste de courses "
            "incomplète pour les recettes créatives."
        )
    _ajouter_a_liste_courses(lignes, nouveau_fichier=False)


def sauvegarder_briefs(task_output) -> None:
    """
    Callback de `tache_briefs_video` (voir tasks.py) : extrait les 2 briefs
    (reel principal + reel satellite) et les écrit directement sur disque,
    sans appel LLM.
    """
    _sauvegarder_sections(
        task_output.raw,
        [
            ("reel_principal_brief.md", ("REEL PRINCIPAL",)),
            ("reel_satellite_brief.md", ("REEL SATELLITE",)),
        ],
        "l'Agent Briefs Vidéo",
    )
