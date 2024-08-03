from elasticsearch import Elasticsearch

class ElasticsearchClient:
    def __init__(self, host="localhost", port=9200):
        self.client = Elasticsearch([{'host': host, 'port': port}])
    
    def create_index(self, index_name):
        index_mapping = {
            "mappings": {
                "properties": {
                    "message_vector": {
                        "type": "dense_vector",
                        "dims": 1536,
                        "index": "true",
                        "similarity": "cosine"
                    },
                    "text": {"type": "text"},
                    "sender": {"type": "text"},
                    "date_sent": {"type": "date"},
                    "is_from_me": {"type": "boolean"},
                    "notes": {"type": "text"},
                    "dates": {"type": "date"}
                }
            }
        }
        if not self.client.indices.exists(index=index_name):
            self.client.indices.create(index=index_name, body=index_mapping)
    
    def store_message(self, index_name, message):
        self.client.index(index=index_name, body=message)
