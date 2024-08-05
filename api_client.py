import requests
import logging

logger = logging.getLogger(__name__)

class BlueBubblesAPI:
    def __init__(self, host, password):
        self.host = host
        self.password = password

    def get_contacts(self):
        response = requests.get(f"{self.host}/api/v1/contact?password={self.password}")
        response.raise_for_status()
        return response.json()

    def query_chats(self):
        payload = {
            "limit": 1000,
            "offset": 0,
            "with": ["lastMessage", "participants", "sms", "archived"],
            "sort": "lastmessage"
        }
        logger.info("Querying chats with payload: %s", payload)
        response = requests.post(f"{self.host}/api/v1/chat/query?password={self.password}", json=payload)
        response.raise_for_status()
        return response.json()

    def get_chat_by_guid(self, guid):
        logger.info("Fetching chat by GUID: %s", guid)
        response = requests.get(f"{self.host}/api/v1/chat/{guid}?password={self.password}&with=participants,lastmessage")
        response.raise_for_status()
        return response.json()

    def query_messages(self, handle_id):
        payload = {
            "limit": 10,
            "offset": 0,
            "with": ["chat", "chat.participants", "attachment", "handle"],
            "where": [{
                "statement": "message.handle_id = :id",
                "args": {"id": handle_id}
            }],
            "sort": "DESC"
        }

        logger.info("Querying messages with payload: %s", payload)
        response = requests.post(f"{self.host}/api/v1/message/query?password={self.password}", json=payload)
        response.raise_for_status()
        return response.json()

    def get_handle_by_address(self, address):
        normalized_address = address.replace(" ", "")
        logger.info(f"Fetching handle by address: {normalized_address}")
        response = requests.get(f"{self.host}/api/v1/handle/{normalized_address}?password={self.password}")
        response.raise_for_status()
        return response.json()
