import imaplib
import email
import time
import tomllib
from datetime import datetime, timezone
import uuid
from email.header import decode_header
from db.db_utils import insert_email_record

CONFIG_FILE = "imap_config.toml"

def load_imap_config(config_file=CONFIG_FILE):
    with open(config_file, "rb") as f:
        config = tomllib.load(f)
    return config["IMAP"]

def decode_subject(subject_str):
    """
    Dekodiert einen oft kodierten "Subject"-Header in einen lesbaren String.
    Beispiel: '=?utf-8?B?w5ZmZm51bmdzemVpdGVuIA==?=' wird dekodiert.
    """
    try:
        dh = decode_header(subject_str)
        decoded_parts = []
        for part, enc in dh:
            if isinstance(part, bytes):
                # Falls Encoding vorhanden, dekodiere, ansonsten standardmäßig utf-8 verwenden
                decoded_parts.append(part.decode(enc if enc else "utf-8"))
            else:
                decoded_parts.append(part)
        return "".join(decoded_parts)
    except Exception as e:
        print(f"Fehler beim Dekodieren des Betreffs: {e}")
        return subject_str

def process_new_emails():
    imap_conf = load_imap_config()

    try:
        mail = imaplib.IMAP4_SSL(imap_conf["server"], imap_conf["port"])
        mail.login(imap_conf["username"], imap_conf["password"])
        mail.select("inbox")

        status, data = mail.search(None, 'UNSEEN')
        if status != "OK":
            print("Keine neuen E-Mails gefunden.")
            mail.logout()
            return

        email_ids = data[0].split()
        if not email_ids:
            print("Keine neuen E-Mails gefunden.")
            mail.logout()
            return

        print(f"{len(email_ids)} neue E-Mail(s) gefunden!")
        for eid in email_ids:
            status, msg_data = mail.fetch(eid, "(RFC822)")
            if status != "OK":
                print(f"Fehler beim Abrufen der E-Mail: {eid}")
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            mail_from = msg.get("From", "unbekannt")
            raw_subject = msg.get("Subject", "kein Betreff")
            mail_subject = decode_subject(raw_subject)

            mail_body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition", "")):
                        charset = part.get_content_charset() or "utf-8"
                        mail_body = part.get_payload(decode=True).decode(charset, errors="replace")
                        break
            else:
                charset = msg.get_content_charset() or "utf-8"
                mail_body = msg.get_payload(decode=True).decode(charset, errors="replace")

            mail_date = datetime.now(timezone.utc).isoformat()

            mail_id = str(uuid.uuid4())
            mail_record = {
                "id": mail_id,
                "sender": mail_from,
                "subject": mail_subject,
                "body": mail_body,
                "date_received": mail_date,
                "status": "NEW"
            }

            insert_email_record(mail_record)
            print(f"E-Mail {eid.decode('utf-8')} gespeichert als {mail_id}")

            mail.store(eid, "+FLAGS", "\\Seen")

        mail.logout()

    except Exception as e:
        print(f"Fehler: {e}")

if __name__ == "__main__":
    while True:
        process_new_emails()
        time.sleep(30)
