import http.client
import json
import ollama

class BlueBubblesAPI:
    def __init__(self, host, password):
        self.host = host
        self.password = password
    
    def get_contacts(self):
        conn = http.client.HTTPSConnection(self.host)
        conn.request("GET", f"/api/v1/contact?password={self.password}")
        res = conn.getresponse()
        data = res.read()
        return json.loads(data.decode("utf-8"))

    def get_messages(self, chat_guid, with_details="handle"):
        conn = http.client.HTTPSConnection(self.host)
        conn.request("GET", f"/api/v1/chat/{chat_guid}/message?password={self.password}&with={with_details}")
        res = conn.getresponse()
        data = res.read()
        return json.loads(data.decode("utf-8"))

    def embed_text(self, text):
        response = ollama.embeddings(model='llama3.1', prompt=text)
        return response['embedding']
