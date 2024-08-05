import numpy as np

def preprocess_contact(contact):
    # Prepare the contact information in vCard format
    contact_info = {
        'id': contact['id'],
        'firstName': contact.get('firstName', ''),
        'lastName': contact.get('lastName', ''),
        'displayName': contact.get('displayName', ''),
        'company': contact.get('company', ''),
        'title': contact.get('title', ''),
        'emails': [email['address'] for email in contact.get('emails', [])],
        'phoneNumbers': [phone['address'] for phone in contact.get('phoneNumbers', [])],
        'addresses': [{'type': addr.get('type', ''), 'address': addr.get('address', '')} for addr in contact.get('addresses', [])],
        'socialProfiles': [{'platform': profile.get('platform', ''), 'url': profile.get('url', '')} for profile in contact.get('socialProfiles', [])],
        'urls': [{'type': url.get('type', ''), 'url': url.get('url', '')} for url in contact.get('urls', [])],
        'notes': "",
        'vectorized_notes': np.random.rand(1536).tolist(),  # Initialize with random values
        'contactInfo': contact  # Store the full vCard information dynamically
    }
    return contact_info

def format_message(message, person_name):
    from_name = "me" if message['isFromMe'] else person_name
    text = message.get('text', '')
    return f"From: {from_name}\nText: {text}\n"
