# Formats de stories disponibles

Ce fichier liste tous les formats de stories utilisables chaque semaine.
L'agent Stories pioche les 6 formats les plus pertinents pour les produits
de la semaine — il ne les applique pas mécaniquement dans l'ordre, il choisit.

**Pour ajouter un format** : copie un bloc existant, change le nom et la
description, sauvegarde le fichier. Il sera pris en compte dès le prochain run.

---

## TEASER
**Quand l'utiliser** : toujours en début de semaine (lundi) pour annoncer les
deux produits vedettes.
**Type outil** : `teaser`
**Contenu** : titre accrocheur + courte phrase présentant les 2 produits. Donne
envie de suivre le contenu de la semaine.

---

## LE SAVIEZ-VOUS
**Quand l'utiliser** : quand la fiche produit contient une anecdote historique
ou un fait nutritionnel vraiment surprenant.
**Type outil** : `info`
**Contenu** : titre court + une seule information marquante — pas de liste,
une seule chose bien choisie.

---

## SONDAGE
**Quand l'utiliser** : pour créer de l'engagement et tester les préférences
de la communauté. Fonctionne très bien en milieu de semaine.
**Type outil** : `sondage`
**Contenu** : une question avec exactement 2 options courtes dans `options_sondage`.

---

## TIP RAPIDE
**Quand l'utiliser** : quand il y a un conseil pratique court et utile à donner
(conservation, achat au marché, erreur à éviter).
**Type outil** : `tip`
**Contenu** : 1 phrase maximum, affichée en très grande typographie — aller
droit au but.

---

## QUESTION OUVERTE
**Quand l'utiliser** : pour inviter la communauté à répondre librement et
générer des commentaires.
**Type outil** : `question`
**Contenu** : une question ouverte liée au produit ou à la recette.

---

## RECAP SEMAINE
**Quand l'utiliser** : toujours en fin de semaine (dimanche) pour clore le
cycle.
**Type outil** : `recap`
**Contenu** : titre + courte synthèse des 2 produits. Passer
`couleur_accent_secondaire` avec la couleur du second produit.

---

## L'ERREUR À ÉVITER
**Quand l'utiliser** : quand il y a une erreur très courante sur ce produit
(ex : mettre la tomate au frigo, trop cuire les framboises, éplucher la
courgette inutilement). Fort potentiel de partage.
**Type outil** : `info`
**Contenu** : titre "L'erreur que tout le monde fait avec [produit]" + la
correction en 1-2 phrases. Ton bienveillant, jamais condescendant.

---

## COMMENT CHOISIR AU MARCHÉ
**Quand l'utiliser** : quand il y a des critères visuels ou tactiles précis
pour choisir ce produit (couleur, fermeté, odeur, taille idéale).
**Type outil** : `tip`
**Contenu** : titre "Comment choisir [produit]" + 2-3 critères courts et
concrets que n'importe qui peut appliquer en rayon ou au marché.

---

## LE GESTE DU CHEF
**Quand l'utiliser** : quand la recette de la semaine implique une technique
précise accessible à un amateur (émulsionner, émoncer, caraméliser, déglacer…).
**Type outil** : `info`
**Contenu** : titre "Le geste du chef" + explication de la technique en
2-3 phrases simples, avec le résultat attendu.

---

## MYTHE OU RÉALITÉ
**Quand l'utiliser** : quand il existe une idée reçue populaire sur ce produit
ou cette recette (ex : "les pâtes font grossir", "le citron conserve les
aliments"). Fort taux de tap forward (les gens vont sur la slide suivante pour
avoir la réponse).
**Type outil** : `sondage`
**Contenu** : titre "Mythe ou réalité ?" + l'affirmation à tester dans les
options_sondage ("Mythe" / "Réalité"). Le corps révèle la vérité.

---

## QU'EST-CE QUE TU EN FAIS ?
**Quand l'utiliser** : pour inverser la dynamique et demander à la communauté
leurs propres recettes avec ce produit. Génère des réponses en DM et des
partages.
**Type outil** : `question`
**Contenu** : titre "Et toi, qu'est-ce que tu fais avec [produit] ?" + une
courte phrase d'invitation. Mentionner qu'on lira les réponses.

---

## CE QUE J'AI APPRIS EN BRIGADE
**Quand l'utiliser** : quand il y a un lien entre le produit/la recette et
une expérience personnelle en restaurant. Humanise le créateur, fidélise
l'audience.
**Type outil** : `info`
**Contenu** : titre "Ce que j'ai appris en brigade" + une anecdote courte et
concrète liée au produit de la semaine. Ton personnel, authentique.

---

## MARCHÉ OU SUPERMARCHÉ ?
**Quand l'utiliser** : quand le produit a une différence notable de qualité
ou de prix selon le circuit d'achat.
**Type outil** : `tip`
**Contenu** : titre "Marché ou supermarché ?" + une recommandation claire
et pratique, sans jugement. Préciser la saison et pourquoi maintenant c'est
important.

---
<!-- Ajoute tes nouveaux formats ici, en suivant la même structure -->
