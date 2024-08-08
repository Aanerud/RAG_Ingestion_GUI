# elasticsearch_client.py

from elasticsearch import Elasticsearch
import hashlib
import logging

logger = logging.getLogger(__name__)

class ElasticsearchClient:
    def __init__(self, host="http://localhost:9200"):
        self.client = Elasticsearch(hosts=[host])

    def create_index(self, index_name):
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
                    "custom_blob_id": {"type": "keyword"},  # Define custom_blob_id as keyword
                    "message_blob": {"type": "text"}
                }
            }
        }
        if not self.client.indices.exists(index=index_name):
            self.client.indices.create(index=index_name, body=index_mapping)
            logger.info(f"Created index: {index_name}")

    def store_contact(self, index_name, contact):
        self.client.index(index=index_name, id=contact['id'], document=contact)

    def generate_unique_id(self, contact):
        unique_string = f"{contact['firstName']}{contact['lastName']}{contact.get('emails', '')}{contact.get('phoneNumbers', '')}"
        return hashlib.md5(unique_string.encode()).hexdigest()

    def search_contacts(self, query):
        search_query = {
            "query": {
                "prefix": {
                    "displayName": {
                        "value": query,
                        "case_insensitive": True
                    }
                }
            }
        }
        response = self.client.search(index="contacts_*", body=search_query)
        return response['hits']['hits']

    def update_contact_handles(self, index_name, contact_id, handles):
        update_body = {
            "doc": {
                "contactInfo": {
                    "handles": handles
                }
            }
        }
        self.client.update(index=index_name, id=contact_id, body=update_body)

    def store_message_blob(self, index_name, contact_id, blob_id, blob):
        document = {
            "contact_id": contact_id,
            "custom_blob_id": blob_id,
            "message_blob": blob
        }
        self.client.index(index=index_name, id=blob_id, document=document)

    def fetch_message_blobs(self, contact_id):
        search_query = {
            "query": {
                "term": {
                    "contact_id": contact_id
                }
            },
            "sort": [
                {"custom_blob_id": {"order": "asc"}}
            ]
        }
        response = self.client.search(index="contacts_*", body=search_query, size=1000)
        return [hit['_source']['message_blob'] for hit in response['hits']['hits']]
