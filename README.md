# Split Eval

Projet indépendant de découpage et de préparation de l'envoi des restitutions individuelles des évaluations nationales.

## Modules prévus

- **05 — Fichiers PDF** : import et découpage des restitutions individuelles.
- **06 — Contacts PRONOTE** : import des coordonnées des responsables.
- **07 — Destinataires** : rapprochement contrôlé des élèves, PDF et destinataires.
- **08 — Diffusion SMTP** : préparation de campagne en un clic, simulation, confirmation explicite avant envoi via API HTTPS authentifiée.
- **09 — Historique** : suivi des tentatives, erreurs, exclusions et acceptations SMTP.

Les **analyses statistiques DEPP** ne font pas partie de ce dépôt.

## Statut

Initialisation du dépôt : **les sources de l'application ne sont pas encore publiées**. Le code historique doit être extrait et audité avant publication.

## Confidentialité

Ce dépôt est public. Ne jamais y ajouter de PDF nominatif, export PRONOTE, fichiers de résultats, identité ou contact d'élèves ou de parents, mot de passe ou secret SMTP.

GitHub Pages ne permet pas d'envoyer des emails via SMTP : l'envoi réel nécessite un serveur applicatif institutionnel sécurisé. « Préparer la campagne » ne signifie **pas** « Envoyer ».
