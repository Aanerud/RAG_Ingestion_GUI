import win32com.client
import re
from datetime import datetime

def init_outlook():
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    accounts = win32com.client.Dispatch("Outlook.Application").Session.Accounts
    return accounts, outlook

def get_emails(accounts, outlook, monitored_subjects, ignored_senders):
    raw_emails = []
    for account in accounts:
        if str(account).lower() == EMAILADDRESS.lower():
            folders = outlook.Folders(account.DeliveryStore.DisplayName)
            specific_folder = folders.Folders
            for folder in specific_folder:
                if folder.name == "Inbox":
                    messages = folder.Items
                    for single in messages:
                        for subject in monitored_subjects:
                            if subject.strip() in single.Subject.lower():
                                for sender in ignored_senders:
                                    try:
                                        if single.SenderName == sender.lower():
                                            continue
                                    except AttributeError:
                                        pass
                                try:
                                    send = single.Sender
                                except AttributeError:
                                    try:
                                        send = single.SenderName
                                    except AttributeError:
                                        send = single.SenderEmailAddress

                                loc = re.search("Confidentiality Notice", single.Body)
                                email_start = re.search("From:\s", single.Body)
                                if email_start and not loc:
                                    end = email_start.start()
                                elif loc and not email_start:
                                    end = loc.start()
                                elif email_start and loc:
                                    end = min(email_start.start(), loc.start())
                                else:
                                    end = None

                                if end:
                                    body = single.Body[:end]
                                else:
                                    body = single.Body

                                body = body.replace("\r", "").replace("\n\n", "\n").strip()
                                raw_emails.append({
                                    "body": body,
                                    "subject": single.Subject,
                                    "sender": send,
                                    "received": single.ReceivedTime,
                                    "unread": single.Unread
                                })
    return raw_emails

def main():
    EMAILADDRESS = ""
    IGNOREDSENDER = [""]
    monitored_subjects = ["subject1", "subject2"]

    accounts, outlook = init_outlook()
    emails = get_emails(accounts, outlook, monitored_subjects, IGNORESENDER)
    print(emails)

if __name__ == "__main__":
    main()
