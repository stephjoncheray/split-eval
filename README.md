# Split Eval — V3 unifiée (édition GitHub Pages)

Application publique de préparation des restitutions individuelles des évaluations nationales, sans analyse statistique DEPP.

## Fonctionnalités accessibles depuis le navigateur

1. **Documents PDF** : import multi-PDF, reconnaissance des pages selon les formats pris en charge, correction manuelle et export ZIP.
2. **Import PRONOTE** : contacts au format CSV/Excel, avec rapprochement des noms et prénoms.
3. **Destinataires** : validation, exclusions et vérification des adresses électroniques.
4. **Préparation SMTP** : export local d'un ZIP confidentiel contenant les pièces jointes, un manifeste JSON des messages et le journal de préparation.
5. **Historique** : pas de journal serveur sur GitHub Pages ; le journal de préparation figure dans le ZIP.

## Accès

GitHub Pages (si activé dans **Settings → Pages**, branche `main`, racine `/`) :
https://stephjoncheray.github.io/split-eval/

L'application est dans un **index.html autonome** (CSS et JavaScript de la V3 intégrés directement). Le dépôt conserve ses autres fichiers historiques, qui ne sont pas requis par la page publiée.

## Limitations

**Aucun courrier n'est envoyé par GitHub Pages.** L'envoi SMTP réel nécessite une passerelle HTTPS institutionnelle authentifiée. Le bouton d'envoi réel est désactivé ; le bouton de préparation produit un ZIP local.

**Confidentialité** : la page fait actuellement appel à des bibliothèques externes depuis cdnjs. Ne chargez pas de documents scolaires nominatifs avant audit des dépendances, auto-hébergement et validation de sécurité. Un ZIP téléchargé contient des données personnelles et doit être protégé puis supprimé après traitement.

Le traitement PDF dépend d'une couche texte exploitable et des mises en page prévues par le parseur ; il faut contrôler les correspondances avant tout envoi.

La syntaxe JavaScript a été vérifiée, mais la recette graphique dans un navigateur et le déploiement effectif de Pages restent à confirmer.
