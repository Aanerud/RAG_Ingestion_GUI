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
                        }
                    },
                    "notes": {"type": "text"},
                    "vectorized_notes": {
                        "type": "dense_vector",
                        "dims": 1536,
                        "index": True,
                        "similarity": "cosine"
                    }
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

    def update_contact(self, contact_id, messages):
        self.client.update(
            index=self.index_name,
            id=contact_id,
            body={
                "doc": {
                    "messages": messages
                }
            }
        )
