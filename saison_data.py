# -*- coding: utf-8 -*-
"""
saison_data.py — Base de données des produits de saison (fruits & légumes), France.

Chaque produit est une fiche complète utilisée par l'Agent 1 (Saisonnalité) pour
sélectionner les 2 produits vedettes de la semaine en fonction du mois en cours.

Structure d'une fiche :
{
    "type": "fruit" ou "legume",
    "saison": [liste des mois de pleine saison en France, 1=janvier ... 12=décembre],
    "varietes": [liste de variétés connues],
    "origine": "résumé de l'origine géographique/historique du produit",
    "nutrition": "résumé des apports nutritionnels clés",
    "conservation": "conseils de conservation",
    "anecdote_historique": "anecdote ou fait culturel/historique",
    "recette_emblematique": {
        "nom": "nom de la recette classique",
        "description": "description courte",
    },
    "accords_suggeres": [liste d'ingrédients qui se marient bien avec le produit],
}

----------------------------------------------------------------------
COMMENT ÉTENDRE CETTE BASE DE DONNÉES :
----------------------------------------------------------------------
1. Ajoutez une nouvelle entrée dans le dictionnaire PRODUITS ci-dessous.
2. La clé du dictionnaire doit être le nom du produit en minuscules, sans accent
   si possible (ex: "peche", "chataigne") pour éviter les soucis d'encodage
   dans les noms de fichiers générés (slides, photos, dossiers Drive).
3. Respectez impérativement les mêmes clés que les fiches existantes :
   type, saison, varietes, origine, nutrition, conservation,
   anecdote_historique, recette_emblematique, accords_suggeres.
4. Le champ "saison" est une liste d'entiers (1 à 12) représentant les mois
   de pleine saison en France métropolitaine.
5. Aucune autre modification de code n'est nécessaire : la fonction
   `produits_du_mois()` et `choisir_produits_vedettes()` lisent
   automatiquement ce dictionnaire.
"""

import random

PRODUITS = {
    "peche": {
        "type": "fruit",
        "saison": [6, 7, 8, 9],
        "varietes": ["Pêche jaune", "Pêche blanche", "Pêche plate (Paraguayo)", "Pêche de vigne"],
        "origine": "Originaire de Chine, cultivée en France depuis l'Antiquité, aujourd'hui surtout dans le Sud (Rhône, Roussillon).",
        "nutrition": "Riche en vitamine C, bêta-carotène et fibres ; environ 40 kcal/100g ; bonne source de potassium.",
        "conservation": "À température ambiante 2-3 jours pour mûrir, puis au réfrigérateur jusqu'à 5 jours. Sortir 30 min avant dégustation.",
        "anecdote_historique": "Surnommée « pomme de Perse » par les Romains, la pêche a transité par la Perse avant d'arriver en Europe via la Route de la Soie.",
        "recette_emblematique": {
            "nom": "Pêches au sirop ou tarte aux pêches",
            "description": "La tarte aux pêches classique avec pâte sablée et crème d'amande.",
        },
        "accords_suggeres": ["verveine", "amande", "thym citron", "burrata", "romarin"],
    },
    "fraise": {
        "type": "fruit",
        "saison": [4, 5, 6, 7],
        "varietes": ["Gariguette", "Mara des bois", "Charlotte", "Ciflorette"],
        "origine": "Hybridée en Europe au 18e siècle, la fraise moderne vient du croisement d'espèces américaines et chiliennes.",
        "nutrition": "Très riche en vitamine C (plus que l'orange à poids égal), faible en calories (~32 kcal/100g), antioxydants.",
        "conservation": "Au réfrigérateur, non lavée, dans une boîte aérée, 2-3 jours maximum. Laver juste avant consommation.",
        "anecdote_historique": "Louis XIV en était si friand qu'on cultivait des fraisiers dans les jardins de Versailles spécialement pour lui.",
        "recette_emblematique": {
            "nom": "Fraises à la chantilly ou tarte aux fraises",
            "description": "Le grand classique français de la pâtisserie de printemps.",
        },
        "accords_suggeres": ["basilic", "poivre noir", "balsamique", "mascarpone", "rhubarbe"],
    },
    "tomate": {
        "type": "legume",
        "saison": [6, 7, 8, 9],
        "varietes": ["Cœur de bœuf", "Ananas", "Noire de Crimée", "Cerise", "Roma"],
        "origine": "Originaire d'Amérique du Sud, rapportée en Europe au 16e siècle, longtemps cultivée comme plante ornementale avant d'être mangée.",
        "nutrition": "Riche en lycopène (antioxydant puissant, surtout cuite), vitamine C, faible en calories (~18 kcal/100g).",
        "conservation": "À température ambiante, jamais au réfrigérateur (altère le goût et la texture), à consommer rapidement une fois mûre.",
        "anecdote_historique": "Considérée comme toxique en Europe jusqu'au 18e siècle car proche de la famille des solanacées vénéneuses.",
        "recette_emblematique": {
            "nom": "Tomates farcies ou salade caprese",
            "description": "Le plat d'été emblématique, simple et généreux.",
        },
        "accords_suggeres": ["basilic", "burrata", "huile d'olive", "ail confit", "olives noires"],
    },
    "courgette": {
        "type": "legume",
        "saison": [6, 7, 8, 9],
        "varietes": ["Verte de Milan", "Ronde de Nice", "Jaune d'Or", "Blanche"],
        "origine": "Originaire d'Amérique centrale, la courgette est introduite en Europe via l'Italie au 19e siècle.",
        "nutrition": "Très peu calorique (~17 kcal/100g), riche en eau, potassium et vitamine C, bonne source de fibres douces.",
        "conservation": "Au réfrigérateur dans le bac à légumes, 4-5 jours. Évite l'humidité excessive qui la fait pourrir vite.",
        "anecdote_historique": "Le mot « courgette » est un diminutif de « courge » inventé en France ; les Italiens l'appellent « zucchina ».",
        "recette_emblematique": {
            "nom": "Ratatouille ou courgettes farcies",
            "description": "Le légume d'été universel, base de la cuisine provençale.",
        },
        "accords_suggeres": ["menthe", "feta", "citron", "pignons de pin", "curry"],
    },
    "abricot": {
        "type": "fruit",
        "saison": [6, 7, 8],
        "varietes": ["Bergeron", "Rouge du Roussillon", "Orangé de Provence"],
        "origine": "Originaire d'Asie centrale (Arménie historiquement créditée), introduit en France au 15e siècle.",
        "nutrition": "Riche en bêta-carotène (provitamine A), fibres, environ 48 kcal/100g, bon pour la peau et la vision.",
        "conservation": "À température ambiante pour mûrir, puis réfrigérateur 3-4 jours max. Très fragile une fois mûr.",
        "anecdote_historique": "Son nom latin Prunus armeniaca lui vient de l'Arménie, longtemps considérée comme son pays d'origine.",
        "recette_emblematique": {
            "nom": "Confiture d'abricots ou tarte aux abricots",
            "description": "Le fruit star des confitures d'été en France.",
        },
        "accords_suggeres": ["romarin", "amande", "miel", "lavande", "pistache"],
    },
    "melon": {
        "type": "fruit",
        "saison": [6, 7, 8, 9],
        "varietes": ["Charentais", "Cantaloup", "Galia", "Jaune Canari"],
        "origine": "Originaire d'Afrique, popularisé en France via le Comtat puis la Charente au 18e siècle.",
        "nutrition": "Très hydratant (90% d'eau), riche en vitamine C et bêta-carotène, environ 34 kcal/100g.",
        "conservation": "Entier à température ambiante, coupé au réfrigérateur recouvert de film, 2-3 jours.",
        "anecdote_historique": "Le melon de Cavaillon doit sa renommée à Alexandre Dumas qui l'échangeait contre ses livres pour la bibliothèque locale.",
        "recette_emblematique": {
            "nom": "Melon au jambon de Bayonne ou au porto",
            "description": "L'entrée d'été incontournable des tables françaises.",
        },
        "accords_suggeres": ["jambon cru", "menthe", "feta", "basilic", "porto"],
    },
    "figue": {
        "type": "fruit",
        "saison": [8, 9, 10],
        "varietes": ["Violette de Solliès", "Bourjassotte noire", "Col de Dame", "Verte"],
        "origine": "Originaire du Moyen-Orient, cultivée en Méditerranée depuis l'Antiquité, emblématique du Sud-Est de la France.",
        "nutrition": "Riche en fibres, calcium, potassium, environ 67 kcal/100g fraîche, naturellement sucrée.",
        "conservation": "Au réfrigérateur, très fragile, à consommer dans les 2 jours après achat.",
        "anecdote_historique": "Symbole de fertilité et d'abondance dans la mythologie grecque, associée à Dionysos.",
        "recette_emblematique": {
            "nom": "Figues rôties au miel et fromage de chèvre",
            "description": "L'association sucrée-salée classique de la cuisine méditerranéenne.",
        },
        "accords_suggeres": ["chèvre", "miel", "jambon cru", "noix", "balsamique"],
    },
    "raisin": {
        "type": "fruit",
        "saison": [9, 10],
        "varietes": ["Chasselas", "Muscat", "Italia", "Alphonse Lavallée"],
        "origine": "Cultivé en France depuis l'époque romaine, le raisin de table est distinct du raisin de cuve.",
        "nutrition": "Riche en antioxydants (resvératrol), vitamine K, environ 70 kcal/100g, sucres naturels.",
        "conservation": "Au réfrigérateur dans son sac perforé, jusqu'à 1 semaine. Rincer juste avant consommation.",
        "anecdote_historique": "Le Chasselas de Moissac bénéficie d'une AOC, rare pour un fruit de table en France.",
        "recette_emblematique": {
            "nom": "Tarte aux raisins ou raisins au fromage",
            "description": "Le fruit de fin d'été par excellence, souvent associé aux plateaux de fromage.",
        },
        "accords_suggeres": ["roquefort", "noix", "comté", "cannelle", "vin blanc"],
    },
    "poire": {
        "type": "fruit",
        "saison": [9, 10, 11, 12, 1],
        "varietes": ["Williams", "Comice", "Conférence", "Passe-Crassane"],
        "origine": "Cultivée en Europe depuis l'Antiquité grecque, la poire compte plus de 1500 variétés répertoriées en France.",
        "nutrition": "Riche en fibres (notamment dans la peau), vitamine C, environ 57 kcal/100g.",
        "conservation": "À température ambiante pour finir de mûrir, puis réfrigérateur, jusqu'à 1 semaine.",
        "anecdote_historique": "La poire Williams a été créée en Angleterre en 1765 puis exportée mondialement, notamment pour l'eau-de-vie.",
        "recette_emblematique": {
            "nom": "Poires Belle-Hélène ou poires pochées au vin",
            "description": "Dessert classique français inventé en l'honneur d'Offenbach.",
        },
        "accords_suggeres": ["chocolat", "roquefort", "cannelle", "vanille", "noix de pécan"],
    },
    "pomme": {
        "type": "fruit",
        "saison": [9, 10, 11, 12, 1, 2],
        "varietes": ["Golden", "Granny Smith", "Reinette", "Pink Lady", "Reine des Reinettes"],
        "origine": "Originaire d'Asie centrale (Kazakhstan), la pomme est le fruit le plus cultivé en France.",
        "nutrition": "Riche en fibres (pectine), vitamine C dans la peau, environ 52 kcal/100g.",
        "conservation": "Au réfrigérateur ou cave fraîche, peut se conserver plusieurs semaines selon la variété.",
        "anecdote_historique": "La Reinette du Mans et la Reine des Reinettes étaient déjà cultivées sous Louis XV dans les vergers royaux.",
        "recette_emblematique": {
            "nom": "Tarte Tatin",
            "description": "Née d'un accident de cuisson dans un hôtel de Lamotte-Beuvron en Sologne.",
        },
        "accords_suggeres": ["cannelle", "caramel", "boudin noir", "roquefort", "calvados"],
    },
    "chataigne": {
        "type": "fruit",
        "saison": [10, 11, 12],
        "varietes": ["Marron de Lyon", "Châtaigne d'Ardèche", "Bouche de Bétizac"],
        "origine": "Arbre emblématique des Cévennes et de l'Ardèche, surnommé « l'arbre à pain » car il nourrissait les populations rurales.",
        "nutrition": "Riche en glucides complexes et fibres, sans gluten, environ 180 kcal/100g (bien plus énergétique que les autres fruits).",
        "conservation": "Au réfrigérateur 1 semaine, ou au congélateur après cuisson, plusieurs mois.",
        "anecdote_historique": "Pendant des siècles, la châtaigne fut l'aliment de base des Cévenols, remplaçant le pain en période de famine.",
        "recette_emblematique": {
            "nom": "Marrons grillés ou crème de marrons",
            "description": "L'incontournable de l'hiver, vendue dans les rues en cornets fumants.",
        },
        "accords_suggeres": ["chocolat", "vanille", "champignons", "porc", "romarin"],
    },
    "endive": {
        "type": "legume",
        "saison": [10, 11, 12, 1, 2, 3],
        "varietes": ["Endive blanche classique", "Endive rouge (Flash)"],
        "origine": "Découverte par accident au 19e siècle dans une cave de Schaerbeek, en Belgique, par un cultivateur qui y oubliait des racines de chicorée.",
        "nutrition": "Très peu calorique (~17 kcal/100g), riche en fibres et en intybine (légère amertume digestive).",
        "conservation": "Au réfrigérateur, à l'abri de la lumière (sinon elle verdit et devient plus amère), 1 semaine.",
        "anecdote_historique": "Appelée « chicon » dans le Nord de la France, l'endive est cultivée à l'obscurité totale, ce qui explique sa couleur pâle.",
        "recette_emblematique": {
            "nom": "Endives au jambon, gratinées",
            "description": "Le plat familial d'hiver le plus connu de France.",
        },
        "accords_suggeres": ["jambon", "comté", "noix", "orange", "roquefort"],
    },
    "poireau": {
        "type": "legume",
        "saison": [10, 11, 12, 1, 2, 3],
        "varietes": ["Poireau gros long d'hiver", "Poireau de Créances", "Bleu de Solaise"],
        "origine": "Cultivé depuis l'Égypte antique, le poireau est un légume rustique typique des potagers français d'hiver.",
        "nutrition": "Riche en fibres prébiotiques, vitamine K, faible en calories (~29 kcal/100g), effet diurétique reconnu.",
        "conservation": "Au réfrigérateur dans un linge humide ou sac perforé, jusqu'à 1 semaine.",
        "anecdote_historique": "Surnommé « asperge du pauvre » au Moyen Âge, il était la base de l'alimentation paysanne en hiver.",
        "recette_emblematique": {
            "nom": "Soupe poireaux-pommes de terre",
            "description": "Le velouté réconfortant de tous les foyers français en hiver.",
        },
        "accords_suggeres": ["pomme de terre", "crème fraîche", "muscade", "saumon fumé", "vinaigrette"],
    },
    "asperge": {
        "type": "legume",
        "saison": [4, 5, 6],
        "varietes": ["Asperge blanche", "Asperge verte", "Asperge violette"],
        "origine": "Cultivée par les Grecs et Romains, l'asperge est aujourd'hui star des Landes, du Val de Loire et de Provence.",
        "nutrition": "Riche en folates (vitamine B9), fibres, effet diurétique notable, environ 20 kcal/100g.",
        "conservation": "Au réfrigérateur debout dans un verre d'eau comme un bouquet, ou emballée dans un linge humide, 3-4 jours.",
        "anecdote_historique": "Louis XIV exigeait des asperges fraîches toute l'année, ce qui a motivé la construction de serres chauffées à Versailles.",
        "recette_emblematique": {
            "nom": "Asperges à la vinaigrette ou sauce hollandaise",
            "description": "L'entrée de printemps classique des tables françaises.",
        },
        "accords_suggeres": ["œuf mollet", "parmesan", "vinaigrette à l'échalote", "jambon cru", "beurre citronné"],
    },
    "cerise": {
        "type": "fruit",
        "saison": [5, 6, 7],
        "varietes": ["Bigarreau", "Burlat", "Griotte", "Reverchon"],
        "origine": "Originaire d'Asie Mineure, rapportée à Rome puis répandue en Europe, la cerise est emblématique de la vallée du Rhône.",
        "nutrition": "Riche en antioxydants (anthocyanes), mélatonine naturelle, environ 63 kcal/100g.",
        "conservation": "Au réfrigérateur avec la queue, dans une boîte aérée, 3-5 jours.",
        "anecdote_historique": "« Le Temps des Cerises », chanson de 1866, est devenue un hymne de la Commune de Paris en 1871.",
        "recette_emblematique": {
            "nom": "Clafoutis aux cerises",
            "description": "Le dessert limousin traditionnel, cerises non dénoyautées selon la tradition.",
        },
        "accords_suggeres": ["amande", "chocolat noir", "kirsch", "thym", "vanille"],
    },
    "nectarine": {
        "type": "fruit",
        "saison": [6, 7, 8],
        "varietes": ["Nectarine jaune", "Nectarine blanche"],
        "origine": "Mutation naturelle de la pêche à peau lisse, cultivée en France notamment dans la vallée du Rhône.",
        "nutrition": "Riche en vitamine C et bêta-carotène, environ 44 kcal/100g, peau comestible riche en fibres.",
        "conservation": "À température ambiante pour mûrir puis réfrigérateur 3-5 jours.",
        "anecdote_historique": "Son nom vient du latin nectar, « boisson des dieux », en référence à sa chair juteuse et sucrée.",
        "recette_emblematique": {
            "nom": "Salade de nectarines fraîches ou nectarines grillées",
            "description": "Souvent consommée nature ou en dessert d'été léger.",
        },
        "accords_suggeres": ["basilic", "burrata", "amande", "miel", "thym citron"],
    },
    "brugnon": {
        "type": "fruit",
        "saison": [6, 7, 8],
        "varietes": ["Brugnon jaune", "Brugnon blanc"],
        "origine": "Proche cousin de la nectarine, le brugnon a un noyau adhérent à la chair (contrairement à la nectarine), cultivé surtout dans le Sud-Est.",
        "nutrition": "Riche en vitamine C, potassium, environ 48 kcal/100g.",
        "conservation": "À température ambiante puis réfrigérateur, 3-5 jours.",
        "anecdote_historique": "Le terme « brugnon » viendrait de « prune », car ce fruit fut longtemps confondu avec une variété de prune juteuse.",
        "recette_emblematique": {
            "nom": "Tarte aux brugnons",
            "description": "Variante estivale des tartes aux fruits à noyau.",
        },
        "accords_suggeres": ["amande", "romarin", "miel", "vanille", "thym citron"],
    },
    "myrtille": {
        "type": "fruit",
        "saison": [7, 8, 9],
        "varietes": ["Myrtille sauvage des Vosges", "Myrtille cultivée (Bluecrop)"],
        "origine": "Cueillie sauvage dans les forêts des Vosges et du Massif Central depuis des siècles, aussi cultivée depuis le 20e siècle.",
        "nutrition": "Très riche en antioxydants (anthocyanes), bonne pour la vision, environ 38 kcal/100g.",
        "conservation": "Au réfrigérateur, non lavée, jusqu'à 1 semaine ; se congèle très bien.",
        "anecdote_historique": "Les pilotes de la RAF pendant la Seconde Guerre mondiale consommaient de la confiture de myrtille, croyant qu'elle améliorait leur vision nocturne.",
        "recette_emblematique": {
            "nom": "Tarte aux myrtilles vosgienne",
            "description": "Spécialité régionale incontournable de l'Est de la France.",
        },
        "accords_suggeres": ["citron", "amande", "chèvre frais", "cannelle", "miel"],
    },
    "prune": {
        "type": "fruit",
        "saison": [7, 8, 9],
        "varietes": ["Reine-Claude", "Mirabelle", "Quetsche", "Prune d'Ente"],
        "origine": "La Mirabelle de Lorraine et la Quetsche d'Alsace sont des emblèmes régionaux français, cultivées depuis le Moyen Âge.",
        "nutrition": "Riche en fibres, vitamine K, effet légèrement laxatif connu, environ 46 kcal/100g.",
        "conservation": "À température ambiante pour mûrir puis réfrigérateur, 4-5 jours.",
        "anecdote_historique": "La prune d'Ente séchée donne le pruneau d'Agen, séché selon une méthode introduite par les Croisés au retour du Moyen-Orient.",
        "recette_emblematique": {
            "nom": "Tarte aux quetsches ou eau-de-vie de mirabelle",
            "description": "Spécialités emblématiques de l'Est de la France.",
        },
        "accords_suggeres": ["cannelle", "amande", "armagnac", "vanille", "noisette"],
    },
    "betterave": {
        "type": "legume",
        "saison": [9, 10, 11, 12, 1, 2],
        "varietes": ["Betterave rouge classique", "Betterave Chioggia", "Betterave jaune"],
        "origine": "Cultivée depuis l'Antiquité pour ses feuilles, la racine n'est consommée couramment que depuis le 19e siècle.",
        "nutrition": "Riche en nitrates naturels (bons pour la circulation), fer, fibres, environ 43 kcal/100g.",
        "conservation": "Au réfrigérateur crue, jusqu'à 2 semaines ; cuite, 3-4 jours.",
        "anecdote_historique": "La betterave a aussi donné naissance au sucre de betterave, développé sous Napoléon pour contourner le blocus continental sur le sucre de canne.",
        "recette_emblematique": {
            "nom": "Betteraves en salade avec vinaigrette",
            "description": "L'accompagnement bistrot classique, souvent déjà cuite chez le primeur.",
        },
        "accords_suggeres": ["chèvre", "noix", "orange", "cumin", "vinaigre de cidre"],
    },
    "radis": {
        "type": "legume",
        "saison": [4, 5, 6, 7],
        "varietes": ["Radis rose de Pâques", "Radis noir", "Radis blanc (Daikon)"],
        "origine": "Cultivé depuis l'Égypte antique, le radis rose est un classique du jardin potager français de printemps.",
        "nutrition": "Très peu calorique (~16 kcal/100g), riche en vitamine C, effet légèrement piquant dû aux glucosinolates.",
        "conservation": "Au réfrigérateur, fanes retirées, dans un sac perforé, jusqu'à 1 semaine.",
        "anecdote_historique": "Le radis beurre, servi avec du beurre et du sel, est l'apéritif de jardin le plus ancien et le plus simple de la cuisine française.",
        "recette_emblematique": {
            "nom": "Radis au beurre et fleur de sel",
            "description": "L'apéritif printanier le plus simple et le plus traditionnel.",
        },
        "accords_suggeres": ["beurre", "fleur de sel", "ciboulette", "fromage frais", "vinaigrette"],
    },
    "epinard": {
        "type": "legume",
        "saison": [3, 4, 5, 10, 11],
        "varietes": ["Épinard à feuilles lisses", "Épinard à feuilles gaufrées"],
        "origine": "Originaire de Perse, introduit en Europe au Moyen Âge via l'Espagne mauresque.",
        "nutrition": "Riche en fer (bien que moins qu'on ne le croit), folates, vitamine K, environ 23 kcal/100g.",
        "conservation": "Au réfrigérateur, non lavé, dans un sac perforé, 2-3 jours maximum (se flétrit vite).",
        "anecdote_historique": "Le mythe de Popeye, qui tirerait sa force des épinards, vient d'une erreur de calcul de teneur en fer publiée au 19e siècle.",
        "recette_emblematique": {
            "nom": "Épinards à la crème",
            "description": "L'accompagnement bistrot classique, souvent servi avec des œufs pochés.",
        },
        "accords_suggeres": ["œuf poché", "muscade", "parmesan", "pignons de pin", "ail"],
    },
    "haricot_vert": {
        "type": "legume",
        "saison": [6, 7, 8, 9],
        "varietes": ["Haricot vert filet", "Haricot beurre (jaune)", "Mangetout"],
        "origine": "Originaire d'Amérique centrale, rapporté par les conquistadors espagnols puis répandu en Europe au 16e siècle.",
        "nutrition": "Riche en fibres, vitamine C, faible en calories (~31 kcal/100g).",
        "conservation": "Au réfrigérateur dans un sac perforé, 3-4 jours ; se congèle très bien blanchi.",
        "anecdote_historique": "Catherine de Médicis aurait contribué à introduire le haricot vert à la cour de France au 16e siècle.",
        "recette_emblematique": {
            "nom": "Haricots verts à l'ail et au beurre",
            "description": "L'accompagnement d'été le plus courant des tables familiales françaises.",
        },
        "accords_suggeres": ["ail", "amandes effilées", "échalote", "tomate", "vinaigrette à l'échalote"],
    },
    "coing": {
        "type": "fruit",
        "saison": [10, 11],
        "varietes": ["Coing de Provence", "Coing du Portugal", "Coing Champion"],
        "origine": "Originaire du Caucase, le coing était déjà cultivé en Grèce antique, symbole d'amour et de fertilité.",
        "nutrition": "Riche en pectine et en fibres, immangeable cru (très astringent), environ 57 kcal/100g cuit.",
        "conservation": "À température ambiante dans un endroit frais et aéré, plusieurs semaines (son parfum embaume la pièce).",
        "anecdote_historique": "Le mot « marmelade » vient du portugais « marmelo », qui signifie coing, premier fruit utilisé pour cette préparation.",
        "recette_emblematique": {
            "nom": "Gelée ou pâte de coing",
            "description": "La confiserie d'automne traditionnelle, souvent servie avec les fromages.",
        },
        "accords_suggeres": ["cannelle", "vanille", "fromages affinés", "miel", "orange"],
    },
    "kiwi": {
        "type": "fruit",
        "saison": [11, 12, 1, 2, 3],
        "varietes": ["Hayward (vert)", "Kiwi jaune (Gold)"],
        "origine": "Originaire de Chine, popularisé sous le nom commercial « kiwi » en Nouvelle-Zélande au 20e siècle ; la France (Adour) est aujourd'hui un grand producteur européen.",
        "nutrition": "Très riche en vitamine C (plus que l'orange), fibres, environ 61 kcal/100g.",
        "conservation": "À température ambiante pour mûrir, puis réfrigérateur jusqu'à 2 semaines.",
        "anecdote_historique": "Initialement appelé « groseille de Chine », il fut rebaptisé « kiwi » en référence à l'oiseau emblématique néo-zélandais pour faciliter son export.",
        "recette_emblematique": {
            "nom": "Salade de fruits ou kiwi nature à la cuillère",
            "description": "Souvent consommé simplement coupé en deux, à la petite cuillère.",
        },
        "accords_suggeres": ["citron vert", "menthe", "fromage de chèvre frais", "miel", "gingembre"],
    },
    "clementine": {
        "type": "fruit",
        "saison": [11, 12, 1],
        "varietes": ["Clémentine de Corse", "Clémentine sans pépins"],
        "origine": "Créée en 1902 par le Père Clément, missionnaire en Algérie, par croisement entre mandarine et orange amère.",
        "nutrition": "Riche en vitamine C, faible en calories (~47 kcal/100g), facile à peler.",
        "conservation": "À température ambiante ou réfrigérateur, jusqu'à 2 semaines.",
        "anecdote_historique": "La Clémentine de Corse bénéficie d'une IGP, seule clémentine produite en France métropolitaine.",
        "recette_emblematique": {
            "nom": "Clémentines au sirop ou nature à Noël",
            "description": "Le fruit emblématique des étals et chaussettes de Noël en France.",
        },
        "accords_suggeres": ["chocolat noir", "cannelle", "fenouil", "datte", "amande"],
    },
}


def produits_du_mois(mois: int) -> dict:
    """
    Retourne le sous-dictionnaire des produits dont la fiche indique
    le mois donné (1-12) comme mois de pleine saison.
    """
    return {nom: fiche for nom, fiche in PRODUITS.items() if mois in fiche["saison"]}


def choisir_produits_vedettes(mois: int, nombre: int = 2) -> dict:
    """
    Sélectionne `nombre` produits vedettes parmi ceux en pleine saison pour le
    mois donné. Si moins de `nombre` produits sont disponibles pour ce mois,
    retourne tous les produits disponibles.

    Utilisé par l'Agent 1 (Saisonnalité) comme source de vérité.
    """
    disponibles = produits_du_mois(mois)
    if len(disponibles) <= nombre:
        return disponibles
    noms_choisis = random.sample(list(disponibles.keys()), nombre)
    return {nom: disponibles[nom] for nom in noms_choisis}
