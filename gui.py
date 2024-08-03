import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QTextEdit, QMessageBox
from api_client import BlueBubblesAPI
from elasticsearch_client import ElasticsearchClient
from message_preprocessing import preprocess_message

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
            contacts = api.get_contacts()
            for contact in contacts['data']:
                index_name = contact['address']
                es_client.create_index(index_name)
                
                chat_guid = contact['chats'][0]['guid']
                messages = api.get_messages(chat_guid)
                
                for message in messages['data']:
                    processed_message = preprocess_message(message, api)
                    es_client.store_message(index_name, processed_message)
            
            self.log('Ingestion process completed successfully.')
        except Exception as e:
            self.log(f'Error during ingestion process: {str(e)}')
            QMessageBox.critical(self, 'Error', 'An error occurred during the ingestion process.')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
