import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QTextEdit, QMessageBox
from api_client import BlueBubblesAPI
from elasticsearch_client import ElasticsearchClient
from message_preprocessing import preprocess_message, preprocess_email
from outlook_client import get_emails, init_outlook

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

    def log(self, message):
        self.log_text.append(message)
    
    def start_ingestion(self):
        host = self.host_input.text()
        password = self.password_input.text()
        elastic_host = self.elastic_host_input.text()

        if not host or not password or not elastic_host:
            QMessageBox.warning(self, 'Input Error', 'Please provide all required inputs.')
            return
        
        api = BlueBubblesAPI(host, password)
        es_client = ElasticsearchClient(elastic_host)

        self.log('Starting ingestion process...')
        
        try:
            # Ingest BlueBubbles messages
            contacts = api.get_contacts()
            for contact in contacts['data']:
                index_name = contact['address']
                es_client.create_index(index_name)
                
                chat_guid = contact['chats'][0]['guid']
                messages = api.get_messages(chat_guid)
                
                for message in messages['data']:
                    processed_message = preprocess_message(message, api)
                    es_client.store_message(index_name, processed_message)

            # Ingest Outlook emails
            EMAILADDRESS = "your_email@example.com"
            IGNORESENDER = ["ignored_sender@example.com"]
            monitored_subjects = ["subject1", "subject2"]

            accounts, outlook = init_outlook()
            emails = get_emails(accounts, outlook, monitored_subjects, IGNORESENDER)
            for email in emails:
                index_name = email['sender']
                es_client.create_index(index_name)
                processed_email = preprocess_email(email, api)
                es_client.store_message(index_name, processed_email)

            self.log('Ingestion process completed successfully.')
        except Exception as e:
            self.log(f'Error during ingestion process: {str(e)}')
            QMessageBox.critical(self, 'Error', 'An error occurred during the ingestion process.')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
