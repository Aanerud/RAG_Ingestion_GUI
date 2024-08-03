import re
from datetime import datetime
from dateutil.parser import parse as date_parse

def extract_notes(text):
    notes = []
    favorite_foods = re.findall(r'\bfavorite food is (\w+)\b', text, re.IGNORECASE)
    hobbies = re.findall(r'\bI love (\w+)\b', text, re.IGNORECASE)
    if favorite_foods:
        notes.extend(favorite_foods)
    if hobbies:
        notes.extend(hobbies)
    return notes

def extract_dates(text):
    dates = []
    date_patterns = re.findall(r'\b\d{1,2}[\/\-\.\s]\d{1,2}[\/\-\.\s]\d{2,4}\b', text)
    for date_str in date_patterns:
        try:
            dates.append(date_parse(date_str).date())
        except ValueError:
            continue
    return dates

def preprocess_message(message, api):
    text = message['text']
    embedding = api.embed_text(text)
    notes = extract_notes(text)
    dates = extract_dates(text)
    return {
        'text': text,
        'message_vector': embedding,
        'sender': message.get('sender', 'unknown'),
        'date_sent': datetime.fromtimestamp(message['date_sent'] / 1000),
        'is_from_me': message.get('is_from_me', False),
        'notes': notes,
        'dates': dates
    }

def preprocess_email(email, api):
    text = email['body']
    embedding = api.embed_text(text)
    notes = extract_notes(text)
    dates = extract_dates(text)
    return {
        'text': text,
        'message_vector': embedding,
        'sender': email['sender'],
        'date_sent': email['received'],
        'is_from_me': False,
        'notes': notes,
        'dates': dates
    }
