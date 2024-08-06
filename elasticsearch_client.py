from elasticsearch import Elasticsearch
import hashlib
import logging
import numpy as np

logger = logging.getLogger(__name__)

class ElasticsearchClient:
    def __init__(self, host="http://localhost:9200"):
        self.client = Elasticsearch(hosts=[host])
        self.index_name = "contacts"

    def create_index(self):
        index_mapping = {
            "mappings": {
                "properties": {
                    "emails": {"type": "text"},
                    "phoneNumbers": {"type": "text"},
                    "firstName": {"type": "text"},
                    "lastName": {"type": "text"},
                    "displayName": {"type": "text"},
                    "company": {"type": "text"},
                    "title": {"type": "text"},
                    "addresses": {"type": "nested", "properties": {
                        "type": {"type": "text"},
                        "address": {"type": "text"}
                    }},
                    "socialProfiles": {"type": "nested", "properties": {
                        "platform": {"type": "text"},
                        "url": {"type": "text"}
                    }},
                    "urls": {"type": "nested", "properties": {
                        "type": {"type": "text"},
                        "url": {"type": "text"}
                    }},
                    "contactInfo": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "keyword"},
                            "handles": {"type": "object"}
                        }
                    },
                    "notes": {"type": "text"},
                    "vectorized_notes": {
                        "type": "dense_vector",
                        "dims": 1536,
                        "index": True,
                        "similarity": "cosine"
                    },
                    "blob_id": {"type": "keyword"},
                    "blob": {"type": "text"}
                }
            }
        }
        if not self.client.indices.exists(index=self.index_name):
            self.client.indices.create(index=self.index_name, body=index_mapping)

    def store_contact(self, contact):
        self.client.index(index=self.index_name, id=contact['id'], document=contact)

    def generate_unique_id(self, contact):
        unique_string = f"{contact['firstName']}{contact['lastName']}{contact.get('emails', '')}{contact.get('phoneNumbers', '')}"
        return hashlib.md5(unique_string.encode()).hexdigest()

    def search_contacts(self, query):
        search_query = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["firstName", "lastName", "emails", "displayName", "company", "title", "addresses.address", "socialProfiles.url", "urls.url"]
                }
            }
        }
        response = self.client.search(index=self.index_name, body=search_query)
        return response['hits']['hits']

    def update_contact_handles(self, contact_id, handles):
        update_body = {
            "doc": {
                "contactInfo": {
                    "handles": handles
                }
            }
        }
        self.client.update(index=self.index_name, id=contact_id, body=update_body)

    def store_message_blob(self, blob_id, blob):
        self.client.index(index=self.index_name, id=blob_id, document={"blob_id": blob_id, "blob": blob})

    def fetch_message_blobs(self, contact_id):
        search_query = {
            "query": {
                "wildcard": {
                    "blob_id": f"{contact_id}_blob_*"
                }
            }
        }
        response = self.client.search(index=self.index_name, body=search_query)
        return [hit['_source']['blob'] for hit in response['hits']['hits']]
