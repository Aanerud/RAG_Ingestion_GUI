import sys
import re
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QTextEdit, QMessageBox, QFileDialog
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from api_client import BlueBubblesAPI
from elasticsearch_client import ElasticsearchClient
from message_preprocessing import preprocess_contact, format_message
import logging
import configparser

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IngestionThread(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, api, es_client):
        super().__init__()
        self.api = api
        self.es_client = es_client

    def run(self):
        try:
            self.ingest_contacts()
            self.log_signal.emit('Ingestion process completed successfully.')
            logger.info('Ingestion process completed successfully.')
        except Exception as e:
            error_msg = f'Error during ingestion process: {str(e)}'
            self.log_signal.emit(error_msg)
            logger.error(error_msg)

    def ingest_contacts(self):
        try:
            contacts = self.api.get_contacts()
            num_contacts = len(contacts['data'])
            self.log_signal.emit(f"Identified {num_contacts} contacts.")
            logger.info(f"Identified {num_contacts} contacts.")
            for contact in contacts['data']:
                unique_id = self.es_client.generate_unique_id(contact)
                contact_info = preprocess_contact(contact)
                contact_info['id'] = unique_id

                self.es_client.create_index()
                self.log_signal.emit(f"Storing contact with ID: {unique_id}")
                logger.info(f"Storing contact with ID: {unique_id}")

                self.es_client.store_contact(contact_info)
                self.log_signal.emit(f"Stored contact with ID: {unique_id}")
                logger.info(f"Stored contact with ID: {unique_id}")

            self.log_signal.emit('Contacts ingestion completed successfully.')
            logger.info('Contacts ingestion completed successfully.')
        except Exception as e:
            logger.error(f'Error during contacts ingestion: {str(e)}')
            raise

class MessageFetchThread(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, api, es_client, query):
        super().__init__()
        self.api = api
        self.es_client = es_client
        self.query = query

    def run(self):
        try:
            self.fetch_messages()
        except Exception as e:
            error_msg = f'Error during message fetch process: {str(e)}'
            self.log_signal.emit(error_msg)
            logger.error(error_msg)

    def fetch_messages(self):
        results = self.es_client.search_contacts(self.query)
        if not results:
            self.log_signal.emit(f"No contacts found for query '{self.query}'.")
            logger.info(f"No contacts found for query '{self.query}'.")
            return

        correct_contact = None
        for result in results:
            if self.query.lower() in [email.lower() for email in result['_source'].get('emails', [])] or \
               self.query.lower() in [phone.lower() for phone in result['_source'].get('phoneNumbers', [])]:
                correct_contact = result['_source']
                break
        
        if not correct_contact:
            self.log_signal.emit(f"No exact contact found for query '{self.query}'.")
            logger.info(f"No exact contact found for query '{self.query}'.")
            return

        person_name = f"{correct_contact.get('firstName', '')} {correct_contact.get('lastName', '')}".strip()
        addresses = correct_contact.get('emails', []) + correct_contact.get('phoneNumbers', [])
        existing_handles = {addr['address']: addr.get('handle') for addr in correct_contact.get('contactInfo', {}).get('emails', []) + correct_contact.get('contactInfo', {}).get('phoneNumbers', [])}
        
        handle_ids = []
        for address in addresses:
            if existing_handles.get(address):
                handle_ids.append(existing_handles[address])
                self.log_signal.emit(f"Found handle for address {address}")
                logger.info(f"Found handle for address {address}")
            else:
                try:
                    handle_response = self.api.get_handle_by_address(address)
                    handle_data = handle_response.get('data', {})
                    if handle_data:
                        handle_ids.append(handle_data['originalROWID'])
                        existing_handles[address] = handle_data['originalROWID']
                        self.log_signal.emit(f"Found handle for address {address}")
                        logger.info(f"Found handle for address {address}")
                    else:
                        self.log_signal.emit(f"Handle not found for address {address}")
                        logger.info(f"Handle not found for address {address}")
                except requests.exceptions.RequestException as e:
                    logger.error(f"Error fetching handle for address {address}: {str(e)}")
        
        if not handle_ids:
            self.log_signal.emit(f"No handle IDs found for query '{self.query}'.")
            logger.info(f"No handle IDs found for query '{self.query}'.")
            return

        logger.info(f"Querying messages for handle IDs: {handle_ids}")

        all_messages = []
        for handle_id in handle_ids:
            offset = 0
            while True:
                try:
                    messages_response = self.api.query_messages_with_pagination(handle_id, offset)
                    messages = messages_response.get('data', [])
                    if not messages:
                        break
                    all_messages.extend(messages)
                    offset += 1000
                except requests.exceptions.RequestException as e:
                    logger.error(f"Error querying messages for handle ID {handle_id}: {str(e)}")
                    break

        # Sort messages by dateCreated and create blobs
        all_messages = sorted(all_messages, key=lambda x: x['dateCreated'], reverse=True)
        blob_size = 1000
        for i in range(0, len(all_messages), blob_size):
            blob_id = f"{correct_contact['id']}_blob_{i // blob_size}"
            blob = "\n".join([format_message(msg, person_name) for msg in all_messages[i:i+blob_size]])
            self.es_client.store_message_blob(blob_id, blob)

        # Update the contact in Elasticsearch with the handle IDs
        self.es_client.update_contact_handles(correct_contact['id'], existing_handles)

        self.log_signal.emit(f"Found {len(all_messages)} messages for query '{self.query}'.")
        logger.info(f"Found {len(all_messages)} messages for query '{self.query}'.")

class MessageDownloadThread(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, es_client, query):
        super().__init__()
        self.es_client = es_client
        self.query = query

    def run(self):
        try:
            self.download_messages()
        except Exception as e:
            error_msg = f'Error during message download process: {str(e)}'
            self.log_signal.emit(error_msg)
            logger.error(error_msg)

    def download_messages(self):
        results = self.es_client.search_contacts(self.query)
        if not results:
            self.log_signal.emit(f"No contacts found for query '{self.query}'.")
            logger.info(f"No contacts found for query '{self.query}'.")
            return

        correct_contact = None
        for result in results:
            if self.query.lower() in [email.lower() for email in result['_source'].get('emails', [])] or \
               self.query.lower() in [phone.lower() for phone in result['_source'].get('phoneNumbers', [])]:
                correct_contact = result['_source']
                break
        
        if not correct_contact:
            self.log_signal.emit(f"No exact contact found for query '{self.query}'.")
            logger.info(f"No exact contact found for query '{self.query}'.")
            return

        blobs = self.es_client.fetch_message_blobs(correct_contact['id'])
        if not blobs:
            self.log_signal.emit(f"No message blobs found for contact '{correct_contact['id']}'.")
            logger.info(f"No message blobs found for contact '{correct_contact['id']}'.")
            return

        file_path, _ = QFileDialog.getSaveFileName(None, "Save Messages As", f"{correct_contact['displayName']}_messages.txt", "Text Files (*.txt)")
        if not file_path:
            self.log_signal.emit("Message download canceled.")
            logger.info("Message download canceled.")
            return

        with open(file_path, 'w', encoding='utf-8') as file:
            for blob in blobs:
                file.write(blob + "\n\n")

        self.log_signal.emit(f"Messages downloaded successfully to {file_path}.")
        logger.info(f"Messages downloaded successfully to {file_path}.")

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('RAG Database Ingestion')
        self.setGeometry(100, 100, 600, 600)
        
        layout = QVBoxLayout()

        self.host_label = QLabel('BlueBubbles Host:')
        layout.addWidget(self.host_label)
        self.host_input = QLineEdit(self)
        layout.addWidget(self.host_input)

        self.password_label = QLabel('BlueBubbles Password:')
        layout.addWidget(self.password_label)
        self.password_input = QLineEdit(self)
        layout.addWidget(self.password_input)
        self.password_input.setEchoMode(QLineEdit.Password)
        
        self.elastic_host_label = QLabel('Elasticsearch Host:')
        layout.addWidget(self.elastic_host_label)
        self.elastic_host_input = QLineEdit(self)
        layout.addWidget(self.elastic_host_input)

        self.log_text = QTextEdit(self)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        self.ingest_button = QPushButton('Create People Containers with BlueBubbles Contacts', self)
        self.ingest_button.clicked.connect(self.start_ingestion)
        layout.addWidget(self.ingest_button)

        self.search_label = QLabel('Search Contacts:')
        layout.addWidget(self.search_label)
        self.search_input = QLineEdit(self)
        layout.addWidget(self.search_input)

        self.search_button = QPushButton('Search', self)
        self.search_button.clicked.connect(self.search_contacts)
        layout.addWidget(self.search_button)

        self.message_label = QLabel('Fetch all iMessages from a given person:')
        layout.addWidget(self.message_label)
        self.message_input = QLineEdit(self)
        layout.addWidget(self.message_input)

        self.message_button = QPushButton('Fetch Messages', self)
        self.message_button.clicked.connect(self.fetch_messages)
        layout.addWidget(self.message_button)

        self.download_button = QPushButton('Download Messages', self)
        self.download_button.clicked.connect(self.download_messages)
        layout.addWidget(self.download_button)

        self.setLayout(layout)
        self.load_config()
        self.show()
        self.validate_inputs()

    def load_config(self):
        """Load configuration from config.ini and populate fields if available."""
        config = configparser.ConfigParser()
        config.read('config.ini')
        if 'BlueBubbles' in config:
            self.host_input.setText(config['BlueBubbles'].get('HOST', ''))
            self.password_input.setText(config['BlueBubbles'].get('PASSWORD', ''))
        if 'Elasticsearch' in config:
            self.elastic_host_input.setText(config['Elasticsearch'].get('HOST', ''))

    def validate_inputs(self):
        self.host_input.textChanged.connect(self.update_ingest_button_state)
        self.password_input.textChanged.connect(self.update_ingest_button_state)
        self.elastic_host_input.textChanged.connect(self.update_ingest_button_state)
        self.update_ingest_button_state()

    def update_ingest_button_state(self):
        if self.host_input.text() and self.password_input.text() and self.elastic_host_input.text():
            self.ingest_button.setEnabled(True)
        else:
            self.ingest_button.setEnabled(False)

    def log(self, message):
        self.log_text.append(message)

    def start_ingestion(self):
        host = self.host_input.text()
        password = self.password_input.text()
        elastic_host = self.elastic_host_input.text()

        if not host or not password or not elastic_host:
            QMessageBox.warning(self, 'Input Error', 'Please provide all required inputs.')
            return

        self.log('Starting ingestion process...')
        logger.info('Starting ingestion process...')
        
        api = BlueBubblesAPI(host, password)
        es_client = ElasticsearchClient(elastic_host)

        self.thread = IngestionThread(api, es_client)
        self.thread.log_signal.connect(self.log)
        self.thread.start()

    def search_contacts(self):
        elastic_host = self.elastic_host_input.text()
        query = self.search_input.text()

        if not elastic_host or not query:
            QMessageBox.warning(self, 'Input Error', 'Please provide all required inputs.')
            return

        es_client = ElasticsearchClient(elastic_host)
        results = es_client.search_contacts(query)
        self.log(f"Found {len(results)} contacts matching '{query}':")
        for result in results:
            self.log(f"ID: {result['_id']}, Source: {result['_source']}")

    def fetch_messages(self):
        host = self.host_input.text()
        password = self.password_input.text()
        elastic_host = self.elastic_host_input.text()
        query = self.message_input.text()

        if not host or not password or not elastic_host or not query:
            QMessageBox.warning(self, 'Input Error', 'Please provide all required inputs.')
            return

        self.log('Fetching messages...')
        logger.info('Fetching messages...')
        
        api = BlueBubblesAPI(host, password)
        es_client = ElasticsearchClient(elastic_host)

        self.thread = MessageFetchThread(api, es_client, query)
        self.thread.log_signal.connect(self.log)
        self.thread.start()

    def download_messages(self):
        elastic_host = self.elastic_host_input.text()
        query = self.message_input.text()

        if not elastic_host or not query:
            QMessageBox.warning(self, 'Input Error', 'Please provide all required inputs.')
            return

        self.log('Downloading messages...')
        logger.info('Downloading messages...')

        es_client = ElasticsearchClient(elastic_host)

        self.thread = MessageDownloadThread(es_client, query)
        self.thread.log_signal.connect(self.log)
        self.thread.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
