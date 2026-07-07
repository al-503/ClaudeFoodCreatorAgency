# -*- coding: utf-8 -*-
"""
tools/templates.py — Génération déterministe du HTML des slides et stories.

Aucun appel LLM ici : ces fonctions transforment du texte déjà écrit (par
l'Agent Rédaction ou l'Agent Stories) en HTML respectant la charte
graphique de l'agence (voir prompts/style_guide.md), prêt à être capturé
en PNG via Playwright.

Pourquoi des templates Python plutôt que demander à Claude d'écrire le
HTML/CSS à chaque slide : sur 24 slides + 6 stories, faire réécrire le même
CSS à chaque appel d'outil fait grossir le contexte de façon cumulative
(CrewAI renvoie l'historique complet de la tâche à chaque appel) et a un
coût réel constaté bien plus élevé que prévu. Le texte reste écrit par
Claude ; seule la mise en page HTML/CSS, identique à chaque fois, est
déterministe.
"""

import html as html_lib
from pathlib import Path

POLICE_TITRE = "'Playfair Display', Georgia, serif"
POLICE_CORPS = "'Inter', Arial, sans-serif"
FOND_CREME = "#FAFAF7"
TEXTE_SOMBRE = "#2A2A28"
LARGEUR_CAROUSEL = 1080

IMPORT_GOOGLE_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&'
    'family=Inter:wght@400;500;600&display=swap" rel="stylesheet">'
)


def _echapper(texte: str) -> str:
    """Échappe le HTML et convertit les retours à la ligne en paragraphes."""
    lignes = [html_lib.escape(ligne) for ligne in texte.strip().split("\n") if ligne.strip()]
    return "".join(f"<p>{ligne}</p>" for ligne in lignes)


def _chemin_vers_uri_fichier(chemin: str) -> str:
    """Convertit un chemin local en URI file:// utilisable dans un <img src>."""
    return Path(chemin).resolve().as_uri()


def _teinter_fond_creme(couleur_accent: str, intensite: float = 0.08) -> str:
    """
    Calcule une variante du fond crème légèrement teintée par la couleur
    accent du produit (ex: fond crème à peine orangé pour la pêche, à
    peine verdâtre pour la pastèque), plutôt qu'un fond crème neutre
    identique pour tous les produits.

    `intensite` contrôle la force du mélange (0 = crème pur, 1 = couleur
    accent pure) ; une valeur faible garde le fond clair et lisible tout en
    restant visuellement cohérent avec le produit.
    """
    couleur_accent = couleur_accent.lstrip("#")
    r_accent, g_accent, b_accent = (int(couleur_accent[i : i + 2], 16) for i in (0, 2, 4))
    r_creme, g_creme, b_creme = 0xFA, 0xFA, 0xF7

    r = round(r_creme * (1 - intensite) + r_accent * intensite)
    g = round(g_creme * (1 - intensite) + g_accent * intensite)
    b = round(b_creme * (1 - intensite) + b_accent * intensite)
    return f"#{r:02X}{g:02X}{b:02X}"


def construire_html_slide(
    titre: str,
    corps: str,
    couleur_accent: str,
    chemin_photo_fond: str = None,
    numero_slide: int = 1,
) -> str:
    """
    Construit le HTML autonome d'une slide de carousel (1080x1080px).

    Si chemin_photo_fond est fourni (slides 1 à 3 d'un carousel, quand la
    photo Gemini du produit a été générée avec succès) : la photo — une
    seule image panoramique partagée par les 3 slides — est découpée en 3
    tranches verticales égales, une par slide (numero_slide 1, 2 ou 3),
    créant un effet de panoramique en swipant le carousel plutôt que de
    répéter la même image entière 3 fois. Un dégradé sombre en bas assure
    la lisibilité du texte blanc. Sinon (slides 4-6 ou photo absente) :
    fond crème teinté avec titre dans la couleur accent.
    """
    corps_html = _echapper(corps)

    if chemin_photo_fond:
        uri_photo = _chemin_vers_uri_fichier(chemin_photo_fond)
        # L'image fait 3x la largeur de la slide ; on la décale de
        # -(numero_slide - 1) largeur pour révéler le tiers correspondant.
        index_tranche = max(0, min(2, numero_slide - 1))
        decalage_px = index_tranche * LARGEUR_CAROUSEL
        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">{IMPORT_GOOGLE_FONTS}
<style>
  body {{ margin:0; width:1080px; height:1080px; font-family:{POLICE_CORPS}; }}
  .fond {{ position:relative; width:1080px; height:1080px; overflow:hidden; background:#000; }}
  .photo {{ position:absolute; top:0; left:-{decalage_px}px; width:{LARGEUR_CAROUSEL * 3}px;
            height:1080px; object-fit:cover; }}
  .degrade {{ position:absolute; inset:0; background:linear-gradient(to top, rgba(0,0,0,0.78) 0%,
              rgba(0,0,0,0.35) 45%, rgba(0,0,0,0.05) 75%); }}
  .contenu {{ position:absolute; left:80px; right:80px; bottom:80px; color:#FFFFFF; }}
  h1 {{ font-family:{POLICE_TITRE}; font-size:58px; line-height:1.15; margin:0 0 20px 0;
        color:{couleur_accent}; text-shadow:0 2px 12px rgba(0,0,0,0.5); }}
  p {{ font-size:30px; line-height:1.5; margin:0 0 12px 0; }}
</style></head>
<body>
  <div class="fond">
    <img class="photo" src="{uri_photo}">
    <div class="degrade"></div>
    <div class="contenu">
      <h1>{html_lib.escape(titre)}</h1>
      {corps_html}
    </div>
  </div>
</body></html>"""

    fond_teinte = _teinter_fond_creme(couleur_accent)
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">{IMPORT_GOOGLE_FONTS}
<style>
  body {{ margin:0; width:1080px; height:1080px; font-family:{POLICE_CORPS};
          background:{fond_teinte}; }}
  .contenu {{ box-sizing:border-box; width:1080px; height:1080px; padding:80px;
              display:flex; flex-direction:column; justify-content:center; }}
  .barre {{ width:90px; height:8px; background:{couleur_accent}; border-radius:4px; margin-bottom:36px; }}
  h1 {{ font-family:{POLICE_TITRE}; font-size:56px; line-height:1.2; margin:0 0 28px 0;
        color:{couleur_accent}; }}
  p {{ font-size:32px; line-height:1.55; margin:0 0 16px 0; color:{TEXTE_SOMBRE}; }}
</style></head>
<body>
  <div class="contenu">
    <div class="barre"></div>
    <h1>{html_lib.escape(titre)}</h1>
    {corps_html}
  </div>
</body></html>"""


def construire_html_story(
    titre: str,
    corps: str,
    couleur_accent: str,
    type_story: str = "info",
    options_sondage: list = None,
    couleur_accent_secondaire: str = None,
) -> str:
    """
    Construit le HTML autonome d'une story (1080x1920px).

    type_story adapte légèrement la mise en page :
    - "teaser" : titre large sur fond accent, pour le lancement de semaine
    - "info" : label "LE SAVIEZ-VOUS ?" + texte, fond crème
    - "sondage" : question + 2 boutons larges représentant les choix
    - "tip" : très grande typographie, lisible en 2 secondes
    - "question" : question ouverte, fond crème
    - "recap" : moodboard de fin de semaine, deux blocs de couleur si
      couleur_accent_secondaire est fournie (un par produit)
    """
    corps_html = _echapper(corps)
    titre_echappe = html_lib.escape(titre)
    fond_teinte = _teinter_fond_creme(couleur_accent)

    style_commun = f"""
  body {{ margin:0; width:1080px; height:1920px; font-family:{POLICE_CORPS}; }}
  .contenu {{ box-sizing:border-box; width:1080px; height:1920px; padding:100px 80px;
              display:flex; flex-direction:column; justify-content:center; }}
  h1 {{ font-family:{POLICE_TITRE}; line-height:1.2; margin:0 0 32px 0; }}
  p {{ line-height:1.6; margin:0 0 18px 0; }}
"""

    if type_story == "teaser":
        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">{IMPORT_GOOGLE_FONTS}<style>{style_commun}
  .contenu {{ background:{couleur_accent}; align-items:center; text-align:center; }}
  h1 {{ font-size:72px; color:#FFFFFF; }}
  p {{ font-size:34px; color:#FFFFFF; opacity:0.92; }}
</style></head><body><div class="contenu"><h1>{titre_echappe}</h1>{corps_html}</div></body></html>"""

    if type_story == "tip":
        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">{IMPORT_GOOGLE_FONTS}<style>{style_commun}
  .contenu {{ background:{fond_teinte}; align-items:center; text-align:center; }}
  .label {{ font-size:26px; letter-spacing:3px; text-transform:uppercase; color:{couleur_accent};
            margin-bottom:28px; font-weight:600; }}
  h1 {{ font-size:80px; color:{TEXTE_SOMBRE}; }}
</style></head><body><div class="contenu"><div class="label">Tip rapide</div>
<h1>{titre_echappe}</h1></div></body></html>"""

    if type_story == "sondage":
        options = options_sondage or ["Option A", "Option B"]
        boutons = "".join(
            f'<div class="bouton">{html_lib.escape(o)}</div>' for o in options[:2]
        )
        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">{IMPORT_GOOGLE_FONTS}<style>{style_commun}
  .contenu {{ background:{fond_teinte}; }}
  h1 {{ font-size:54px; color:{TEXTE_SOMBRE}; text-align:center; }}
  .boutons {{ margin-top:50px; display:flex; flex-direction:column; gap:28px; }}
  .bouton {{ background:{couleur_accent}; color:#FFFFFF; font-size:34px; font-weight:600;
             text-align:center; padding:34px; border-radius:60px; }}
</style></head><body><div class="contenu"><h1>{titre_echappe}</h1>
<div class="boutons">{boutons}</div></div></body></html>"""

    if type_story == "recap":
        couleur_2 = couleur_accent_secondaire or couleur_accent
        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">{IMPORT_GOOGLE_FONTS}<style>{style_commun}
  .contenu {{ background:{fond_teinte}; }}
  h1 {{ font-size:52px; color:{TEXTE_SOMBRE}; text-align:center; }}
  p {{ font-size:30px; color:{TEXTE_SOMBRE}; }}
  .blocs {{ display:flex; gap:24px; margin:40px 0; }}
  .bloc {{ flex:1; height:200px; border-radius:24px; }}
  .bloc1 {{ background:{couleur_accent}; }}
  .bloc2 {{ background:{couleur_2}; }}
</style></head><body><div class="contenu"><h1>{titre_echappe}</h1>
<div class="blocs"><div class="bloc bloc1"></div><div class="bloc bloc2"></div></div>
{corps_html}</div></body></html>"""

    # "info" et "question" partagent le même gabarit simple
    label = "Le saviez-vous ?" if type_story == "info" else ""
    label_html = (
        f'<div class="label">{html_lib.escape(label)}</div>' if label else ""
    )
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">{IMPORT_GOOGLE_FONTS}<style>{style_commun}
  .contenu {{ background:{fond_teinte}; }}
  .label {{ font-size:26px; letter-spacing:3px; text-transform:uppercase; color:{couleur_accent};
            margin-bottom:24px; font-weight:600; }}
  h1 {{ font-size:52px; color:{TEXTE_SOMBRE}; }}
  p {{ font-size:32px; color:{TEXTE_SOMBRE}; }}
</style></head><body><div class="contenu">{label_html}<h1>{titre_echappe}</h1>
{corps_html}</div></body></html>"""


def construire_markdown_planning(date_semaine: str, planning: list, checklist: list) -> str:
    """
    Construit le contenu Markdown de planning_coach.md à partir de données
    structurées (liste de petits dictionnaires), plutôt que de demander au
    LLM d'écrire un long texte libre en un seul argument d'outil — plus
    fiable pour l'appel d'outil, et plus facile à relire pour le coach.

    Args:
        date_semaine: ex. "28/06/2026"
        planning: liste de dicts {"jour", "heure", "plateforme", "type", "statut"}
        checklist: liste de chaînes, ex. ["2 sessions cuisine", "4 publications TikTok"]
    """
    lignes = [f"# Planning — semaine du {date_semaine}", "", "| Jour | Heure | Plateforme | Type | Statut |", "|---|---|---|---|---|"]
    for item in planning:
        lignes.append(
            f"| {item.get('jour', '')} | {item.get('heure', '')} | "
            f"{item.get('plateforme', '')} | {item.get('type', '')} | {item.get('statut', '')} |"
        )
    lignes.append("")
    lignes.append("## Checklist de la semaine")
    for ligne_checklist in checklist:
        lignes.append(f"- [ ] {ligne_checklist}")
    lignes.append("")
    lignes.append("## Vos idées de reels bonus cette semaine ?")
    lignes.append("_(espace libre pour vos notes)_")
    return "\n".join(lignes)


def construire_html_email(
    date_semaine: str,
    lien_drive: str,
    produit1: str,
    produit2: str,
    liste_courses: str,
) -> str:
    """
    Construit le HTML de l'email récapitulatif hebdomadaire : produits de la
    semaine + liste de courses brute. Déterministe, sans LLM.

    Le lien Drive n'est volontairement JAMAIS affiché dans l'email : testé en
    pratique, une URL drive.google.com est rejetée par le filtre anti-spam de
    SFR (550 rejected per spam policy). Mettre le dossier AgenceInstagram en
    favori navigateur suffit.
    """
    upload_ok = bool(lien_drive) and not lien_drive.startswith("ERREUR")
    lien_html = (
        "Disponible dans ton dossier Drive habituel (AgenceInstagram), "
        "sous-dossier de cette semaine."
        if upload_ok
        else "Le dossier Drive n'a pas pu être uploadé automatiquement cette "
        "semaine — à faire manuellement."
    )

    # Liste de courses : chaque ligne "- ingrédient" → <li>
    lignes_courses = [
        l.lstrip("- ").strip()
        for l in liste_courses.splitlines()
        if l.strip().startswith("-")
    ]
    if lignes_courses:
        items_html = "".join(f"<li>{html_lib.escape(l)}</li>" for l in lignes_courses)
        courses_html = f"<h3>Liste de courses</h3><ul>{items_html}</ul>"
    else:
        courses_html = "<p><em>Liste de courses non disponible.</em></p>"

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;background:#FFFFFF;font-family:Arial,sans-serif;color:{TEXTE_SOMBRE};">
  <div style="max-width:600px;margin:0 auto;padding:24px;">
    <p>Bonjour,</p>
    <p>Le contenu de la semaine du {html_lib.escape(date_semaine)} est prêt.</p>
    <p><strong>Produits de la semaine :</strong> {html_lib.escape(produit1.capitalize())} et {html_lib.escape(produit2.capitalize())}</p>
    <p>Dossier Drive : {lien_html}</p>
    {courses_html}
  </div>
</body></html>"""
