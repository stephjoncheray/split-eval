#!/usr/bin/env python3
"""Split Eval: execution locale de campagnes sur serveur Debian.
Aucune API reseau. Aucun stockage durable des PDF.
Usage: python3 split_eval_sender.py campagne.zip --simulate
       python3 split_eval_sender.py campagne.zip --send --confirm ENVOYER
"""
import argparse
import csv
import getpass
import hashlib
import imaplib
import io
import json
import os
from pathlib import Path
import re
import smtplib
import ssl
import sys
import zipfile
from datetime import datetime, timezone
from email.message import EmailMessage
from email.policy import SMTP
from email.utils import formatdate, make_msgid

SMTP_HOST = "smtp.education.gouv.fr"
SMTP_PORT = 587
IMAP_HOST = "imap.education.gouv.fr"
IMAP_PORT = 993
MAX_ZIP_BYTES = 250 * 1024 * 1024
MAX_FILES = 3500
MAX_PDF_BYTES = 20 * 1024 * 1024
EMAIL = re.compile(r"^[^\s@<>;,]+@[^\s@<>;,]+\.[^\s@<>;,]+$")


def load_campaign(path):
    path = Path(path)
    if not path.is_file() or path.stat().st_size > MAX_ZIP_BYTES:
        raise ValueError("Archive absente ou trop volumineuse")
    with zipfile.ZipFile(path) as z:
        entries = z.infolist()
        if sum(x.file_size for x in entries) > MAX_ZIP_BYTES * 2:\n            raise ValueError("Contenu decompresse trop volumineux")\n        if len(entries) > MAX_FILES:
            raise ValueError("Trop de fichiers dans le ZIP")
        names = [x.filename for x in entries]
        if len(names) != len(set(names)) or "campagne.json" not in names:
            raise ValueError("Manifest manquant ou doublons de chemins")
        for item in entries:
            parts = item.filename.replace("\\", "/").split("/")
            if item.filename.startswith("/") or ".." in parts or "\\" in item.filename or item.flag_bits & 1:
                raise ValueError("Chemin dangereux ou entree chiffree")
        if z.getinfo("campagne.json").file_size > 5 * 1024 * 1024:
            raise ValueError("Manifest trop volumineux")
        manifest = json.loads(z.read("campagne.json"))
        messages = manifest.get("messages")
        if not isinstance(messages, list) or not messages:
            raise ValueError("Campagne sans messages")
        if len(messages) > 1200:
            raise ValueError("Trop de messages")
        for m in messages:
            if m.get("statut") != "PREPARE_NON_ENVOYE":
                raise ValueError("Statut initial invalide")
            recipients = m.get("to")
            if not isinstance(recipients, list) or not recipients or len(recipients) > 5 or any(not isinstance(x, str) or not EMAIL.fullmatch(x) for x in recipients):
                raise ValueError("Destinataire invalide")
            attachments = m.get("attachments")
            if not isinstance(attachments, list) or not attachments:
                raise ValueError("Message sans PDF")
            for name in attachments:
                if not isinstance(name, str) or not name.startswith("pieces_jointes/") or not name.endswith(".pdf") or name not in names:
                    raise ValueError("Reference de piece jointe invalide")
                if z.getinfo(name).file_size > MAX_PDF_BYTES:
                    raise ValueError("PDF trop volumineux")
            if not isinstance(m.get("subject"), str) or not isinstance(m.get("body"), str) or len(m["subject"]) > 500 or len(m["body"]) > 20000:
                raise ValueError("Sujet ou message invalide")
        return manifest


def build_email(z, entry, sender, opts, domain):
    email = EmailMessage(policy=SMTP)
    email["From"] = sender
    email["To"] = ", ".join(entry["to"])
    email["Subject"] = " ".join(entry["subject"].splitlines())
    email["Date"] = formatdate(localtime=False)
    email["Message-ID"] = make_msgid(domain=domain)
    priority = opts.get("priorite", "normal")
    if priority == "high":
        email["X-Priority"] = "1"
        email["Importance"] = "high"
    elif priority == "low":
        email["X-Priority"] = "5"
        email["Importance"] = "low"
    if opts.get("accuse_lecture"):
        email["Disposition-Notification-To"] = sender
    email.set_content(entry["body"])
    for name in entry["attachments"]:
        data = z.read(name)
        if not data.startswith(b"%PDF-"):
            raise ValueError("Piece jointe non PDF")
        email.add_attachment(data, maintype="application", subtype="pdf", filename=name.rsplit("/", 1)[-1])
    return email


def sent_mailbox(imap):
    code, folders = imap.list()
    if code != "OK":
        raise RuntimeError("Liste des dossiers IMAP indisponible")
    # Selection explicite plutot que risquer un mauvais dossier.
    print("Dossiers IMAP disponibles :")
    for raw in folders:
        print("  ", raw.decode(errors="replace"))
    selected = input("Nom exact du dossier Envoyes (laisser vide pour ne pas archiver) : ").strip()
    if not selected:
        return None
    # Verifie l'existence et les droits, sans creer de dossier.
    code, _ = imap.select(selected, readonly=False)
    if code != "OK":
        raise RuntimeError("Dossier IMAP inaccessible en ecriture")
    imap.close()
    return selected


def execute(args):
    manifest = load_campaign(args.zip)
    opts = manifest.get("options_envoi") or {}
    sender = args.sender
    if not EMAIL.fullmatch(sender):
        raise ValueError("Adresse expediteur invalide")
    report = Path(args.report).resolve()
    if report.exists():
        raise ValueError("Le journal existe deja : refus de l'ecraser")
    if args.send and args.confirm != "ENVOYER":
        raise ValueError("Confirmation requise: --confirm ENVOYER")
    if args.send and not args.authorized:
        raise ValueError("Confirmez l'autorisation institutionnelle avec --authorized")
    password = getpass.getpass("Mot de passe academique (jamais stocke) : ") if args.send else None
    context = ssl.create_default_context()
    smtp = None
    imap = None
    mailbox = None
    results = []
    try:
        if args.send:
            smtp = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
            smtp.ehlo()
            smtp.starttls(context=context)
            smtp.ehlo()
            smtp.login(sender, password)
            if opts.get("copie_dans_envoyes"):
                try:
                    imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, ssl_context=context, timeout=30)
                    imap.login(sender, password)
                    mailbox = sent_mailbox(imap)
                except Exception as exc:
                    print("Archivage IMAP indisponible :", exc, file=sys.stderr)
                    if imap:
                        try: imap.logout()
                        except Exception: pass
                    imap = None
                    mailbox = None
        with zipfile.ZipFile(args.zip) as z:
            for index, m in enumerate(manifest["messages"], 1):
                line = {"index": index, "date_utc": datetime.now(timezone.utc).isoformat(), "eleve": str(m.get("eleve", {})), "destinataires": ";".join(m["to"]), "message_id": "", "smtp": "NON_ENVOYE", "imap": "NON_TENTE", "detail": ""}
                try:
                    msg = build_email(z, m, sender, opts, sender.split("@")[-1])
                    line["message_id"] = str(msg["Message-ID"])
                    raw = msg.as_bytes()
                    if args.send:
                        refused = smtp.sendmail(sender, m["to"], raw)
                        if refused:
                            line["smtp"] = "PARTIEL"
                            line["detail"] = str(refused)
                        else:
                            line["smtp"] = "ACCEPTE_PAR_RELAIS"
                        if mailbox and not refused:
                            try:
                                code, _ = imap.append(mailbox, "\\Seen", imaplib.Time2Internaldate(datetime.now().timestamp()), raw)
                                line["imap"] = "COPIE_OK" if code == "OK" else "COPIE_ERREUR"
                            except Exception as exc:
                                line["imap"] = "COPIE_ERREUR"
                                line["detail"] += " IMAP:" + str(exc)
                    else:
                        line["smtp"] = "SIMULATION"
                    print(f"{index}/{len(manifest['messages'])} : {line['smtp']} / {line['imap']}")
                except Exception as exc:
                    line["smtp"] = "ERREUR"
                    line["detail"] = str(exc)[:500]
                results.append(line)
    finally:
        if smtp:
            try: smtp.quit()
            except Exception: pass
        if imap:
            try: imap.logout()
            except Exception: pass
        # Journal indispensable meme si la campagne est interrompue.
        report.parent.mkdir(parents=True, exist_ok=True)
        with report.open("x", encoding="utf-8-sig", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=["index", "date_utc", "eleve", "destinataires", "message_id", "smtp", "imap", "detail"], delimiter=";")
            writer.writeheader()
            writer.writerows(results)
        try: os.chmod(report, 0o600)
        except OSError: pass
        print("Journal :", report)
    return 0 if all(x["smtp"] in ("SIMULATION", "ACCEPTE_PAR_RELAIS") for x in results) else 2


def main():
    p = argparse.ArgumentParser(description="Execution locale Split Eval sur serveur institutionnel")
    p.add_argument("zip")
    p.add_argument("--sender", required=True, help="Adresse academique expediteur")
    p.add_argument("--report", required=True, help="Journal CSV de sortie, inexistant")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--simulate", action="store_true")
    mode.add_argument("--send", action="store_true")
    p.add_argument("--confirm", default="")
    p.add_argument("--authorized", action="store_true")
    args = p.parse_args()
    try:
        return execute(args)
    except (ValueError, OSError, RuntimeError, smtplib.SMTPException, imaplib.IMAP4.error, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        print("Erreur :", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
