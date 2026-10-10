# Split Eval — Exécution SMTP/IMAP sur Debian FOG

**État : première implémentation CLI à tester ; pas encore une installation sur FOG.** Le script `server/split_eval_sender.py` est versionné sur GitHub. Aucune commande n'a été exécutée sur `192.168.224.240`.

## Architecture

1. Depuis https://stephjoncheray.github.io/split-eval/ : importer les PDF et les contacts PRONOTE, vérifier toutes les correspondances, télécharger le ZIP confidentiel.
2. Transférer manuellement ce ZIP depuis un ordinateur autorisé vers une session SSH du serveur Debian (ex. `scp`). Ne **pas** ouvrir de service de dépôt de fichiers sur Internet.
3. Sur le serveur : lancer une simulation, vérifier le CSV, puis autoriser explicitement un envoi SMTP avec archivage IMAP facultatif.
4. Rapatrier le journal CSV sur un poste autorisé et supprimer le ZIP du serveur après vérification.

## Pré-requis et sécurité

- Autorisation de la direction et validation DSI/DPO pour la méthode de diffusion et l'emploi du serveur FOG ; le service FOG est critique.
- Compte Linux spécifique non privilégié, répertoire de travail `chmod 700` ; ne pas exécuter en root.
- Python 3.11 standard (pas de dépendance pip pour le script).
- Connectivité sortante vers `smtp.education.gouv.fr:587` et `imap.education.gouv.fr:993`, TLS vérifié.
- Accès SSH au serveur réservé aux administrateurs ; aucun nouveau port Apache, aucune règle NFS ou FOG modifiée.
- Ne jamais placer le ZIP, le journal ou un mot de passe dans un dépôt GitHub, même privé.
- La version web publique utilise encore des bibliothèques CDN : **ne pas utiliser de véritables fichiers scolaires avant audit de confidentialité et auto-hébergement**.

## Installation prudente — à exécuter seulement après validation

Sur le serveur Debian :

```bash
sudo install -d -m 700 -o root -g root /opt/split-eval
sudo install -d -m 700 -o root -g root /var/lib/split-eval
```

Le script peut être téléchargé depuis le dépôt public par une méthode de déploiement vérifiée, puis copié dans `/opt/split-eval/split_eval_sender.py`. Le répertoire de campagnes sera propriété du compte dédié une fois celui-ci créé. Éviter toute création de compte non approuvée ou modification de configuration FOG lors des premiers essais.

Commandes **d'exemple** après copie des fichiers, exécutées depuis un compte disposant des permissions nécessaires :

```bash
python3 /opt/split-eval/split_eval_sender.py \
 /chemin/prive/campagne.zip \
 --sender prenom.nom@ac-corse.fr \
 --report /chemin/prive/simulation.csv \
 --simulate
```

Puis, après contrôle manuel de la campagne et autorisation institutionnelle :

```bash
python3 /opt/split-eval/split_eval_sender.py \
 /chemin/prive/campagne.zip \
 --sender prenom.nom@ac-corse.fr \
 --report /chemin/prive/envoi-reel.csv \
 --send --confirm ENVOYER --authorized
```

Un mot de passe est demandé au clavier uniquement au moment de l'envoi réel (pas d'argument en ligne de commande ni fichier de configuration). Les logs n'incluent pas le mot de passe.

## État des capacités

| Fonction | Statut |
| --- | --- |
| Contrôler `campagne.json` et les PDF du ZIP | Implémenté, non testé sur FOG |
| Simuler et produire un CSV | Implémenté, non testé sur FOG |
| Transmettre avec TLS SMTP 587 | Implémenté, test de bout en bout requis |
| Copier chaque message accepté dans IMAP « Envoyés » | Implémenté, sélection du dossier à confirmer en test |
| Priorité + demande d'accusé de lecture | Pris en charge dans MIME |
| Demande DSN / notification de distribution | Non implémentée, dépend des capacités du relais |
| Courriel récapitulatif automatique | Non implémenté ; CSV local disponible |
| Reprise sécurisée d'une campagne interrompue | Non implémentée : **risque de doublons si l'envoi est relancé** |
| Transfert web direct depuis GitHub Pages | Non implémenté ; transfert manuel du ZIP |
| Port réseau/API sur FOG | Aucun |
| Preuve de réception ou de lecture | Jamais garantie par un simple envoi SMTP |

**Important :** après un envoi partiel ou une interruption, ne jamais relancer toute la campagne sans rapprochement individuel avec le journal et la boîte « Envoyés ». Un `SMTP ACCEPTÉ` prouve uniquement l'acceptation par le relais.

## Prochaine recette

Effectuer d'abord un import de ZIP synthétique sans élève réel. Vérifier CSV, intégrité des pièces et en-têtes MIME. Tester ensuite un **unique** message à une adresse institutionnelle autorisée et contrôler le dossier IMAP « Envoyés ». Ne pas lancer de campagne de 470 élèves tant que ces tests et la prévention des doublons n'ont pas été validés.
