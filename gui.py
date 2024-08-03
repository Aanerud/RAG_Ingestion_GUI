import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QTextEdit, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from api_client import BlueBubblesAPI
from elasticsearch_client import ElasticsearchClient
from message_preprocessing import preprocess_message, preprocess_email
from outlook_client import get_emails, init_outlook
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
            self.ingest_bluebubbles()
            self.ingest_outlook()
            self.log_signal.emit('Ingestion process completed successfully.')
            logger.info('Ingestion process completed successfully.')
        except Exception as e:
            error_msg = f'Error during ingestion process: {str(e)}'
            self.log_signal.emit(error_msg)
            logger.error(error_msg)

    def ingest_bluebubbles(self):
        try:
            contacts = self.api.get_contacts()
            for contact in contacts['data']:
                index_name = contact['address']
                self.es_client.create_index(index_name)
                
                chat_guid = contact['chats'][0]['guid']
                messages = self.api.get_messages(chat_guid)
                
                for message in messages['data']:
                    processed_message = preprocess_message(message, self.api)
                    self.es_client.store_message(index_name, processed_message)
            logger.info('BlueBubbles ingestion completed successfully.')
        except Exception as e:
            logger.error(f'Error during BlueBubbles ingestion: {str(e)}')
            raise

    def ingest_outlook(self):
        try:
            config = configparser.ConfigParser()
            config.read('config.ini')
            EMAILADDRESS = config['Outlook']['EMAILADDRESS']
            IGNORESENDER = config['Outlook']['IGNOREDSENDER'].split(',')
            monitored_subjects = config['Outlook']['MONITORED_SUBJECTS'].split(',')

            accounts, outlook = init_outlook()
            emails = get_emails(accounts, outlook, monitored_subjects, IGNORESENDER)
            for email in emails:
                index_name = email['sender']
                self.es_client.create_index(index_name)
                processed_email = preprocess_email(email, self.api)
                self.es_client.store_message(index_name, processed_email)
            logger.info('Outlook ingestion completed successfully.')
        except Exception as e:
            logger.error(f'Error during Outlook ingestion: {str(e)}')
            raise

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('RAG Database Ingestion')
        self.setGeometry(100, 100, 600, 400)
        
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
        
        self.ingest_button = QPushButton('Ingest Messages', self)
        self.ingest_button.clicked.connect(self.start_ingestion)
        layout.addWidget(self.ingest_button)

        self.setLayout(layout)
        self.show()
        self.validate_inputs()

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
