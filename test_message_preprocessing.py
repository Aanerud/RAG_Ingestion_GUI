import unittest
from message_preprocessing import extract_notes, extract_dates, preprocess_message, preprocess_email
from unittest.mock import Mock

class TestMessagePreprocessing(unittest.TestCase):
    
    def test_extract_notes(self):
        text = "My favorite food is pizza. I love swimming."
        notes = extract_notes(text)
        self.assertIn('pizza', notes)
        self.assertIn('swimming', notes)

    def test_extract_dates(self):
        text = "My birthday is on 12/12/1990."
        dates = extract_dates(text)
        self.assertEqual(len(dates), 1)

    def test_preprocess_message(self):
        mock_api = Mock()
        mock_api.embed_text.return_value = [0.1, 0.2, 0.3]
        message = {
            'text': "My favorite food is pizza. My birthday is on 12/12/1990.",
            'handle': {'address': 'sender@example.com'},
            'dateCreated': 1633920317533,
            'isFromMe': True
        }
        processed_message = preprocess_message(message, mock_api)
        self.assertIn('pizza', processed_message['notes'])
        self.assertEqual(len(processed_message['dates']), 1)
        self.assertEqual(processed_message['sender'], 'sender@example.com')

    def test_preprocess_email(self):
        mock_api = Mock()
        mock_api.embed_text.return_value = [0.1, 0.2, 0.3]
        email = {
            'body': "My favorite food is pizza. My birthday is on 12/12/1990.",
            'sender': 'sender@example.com',
            'received': '2023-08-01T00:00:00',
            'unread': True
        }
        processed_email = preprocess_email(email, mock_api)
        self.assertIn('pizza', processed_email['notes'])
        self.assertEqual(len(processed_email['dates']), 1)
        self.assertEqual(processed_email['sender'], 'sender@example.com')

if __name__ == '__main__':
    unittest.main()
