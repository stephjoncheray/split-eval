# Split Eval — Préparation ponctuelle

Application web pour la préparation des restitutions individuelles des évaluations nationales.

## Modules
- **05 — Fichiers PDF** : analyser des pages PDF, vérifier manuellement nom, prénom, classe et discipline, exporter les fiches découpées en ZIP.
- **06 — Contacts PRONOTE** : importer un CSV et repérer les courriels des responsables.
- **07 — Destinataires** : rapprocher les deux sources et exclure les ambiguïtés.
- **08 — Diffusion SMTP** : préparer une campagne temporaire et **exporter un ZIP** contenant chaque pièce jointe PDF, `campagne.json` et `journal.csv`. Champs de configuration SMTP temporaires, **non utilisés pour envoyer** tant qu'aucun backend HTTPS institutionnel n'est déployé.
- **09 — Historique** : événements de session ; journal CSV téléchargeable.

**Ce n'est pas une application d'analyse statistique DEPP.**

## Limites actuelles

1. **Aucun email réel n'est envoyé** et le bouton d'envoi reste désactivé. Aucun destinataire n'est crédité d'un statut « envoyé ».
2. La reconnaissance des identités PDF n'est pas encore automatique : **saisie et validation manuelles obligatoires**.
3. Les bibliothèques PDF sont actuellement téléchargées depuis un CDN. Leur hébergement local et un audit de confidentialité sont **nécessaires avant utilisation avec des documents scolaires nominatifs**.
4. Le ZIP exporté contient **des données personnelles** : protéger l'accès au fichier et le supprimer après usage. L'effacement de la session ne supprime pas les téléchargements.
5. Le traitement est effectué en mémoire dans l'onglet ouvert ; fermeture/rechargement = perte de la campagne non exportée.
6. La préparation permet plusieurs pièces jointes par élève. **Vérifier les associations** avant tout usage opérationnel. Les homonymes et duplications restent un risque.

## SMTP réel — architecture requise

GitHub Pages ne permet pas d'ouvrir une connexion SMTP. Pour envoyer réellement :
- un service institutionnel **HTTPS authentifié**, non ouvert comme relais SMTP arbitraire ;
- configuration du ou des relais autorisés côté serveur, TLS obligatoire ;
- transmission de la campagne uniquement après sélection et confirmation explicites ;
- simulation, limitation de débit, suivi des erreurs, acceptation du serveur SMTP et journal téléchargeable ;
- destruction des fichiers temporaires selon une durée et des mesures de confidentialité vérifiées.

**Aucun identifiant SMTP, PDF, CSV ou journal d'élève ne doit être commité dans GitHub.**

## Hébergement

Le dépôt reste privé. Pour un accès universel, une interface statique auditée pourra être publiée via un second dépôt GitHub Pages public ; **site public ne signifie pas données publiques**, sous réserve que tout traitement demeure local et qu'aucun script tiers ne récupère les fichiers.
