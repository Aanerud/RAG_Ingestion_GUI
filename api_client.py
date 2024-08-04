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

    def query_messages(self, handle_ids):
        payload = {
            "limit": 1000,
            "offset": 0,
            "with": ["chat", "chat.participants", "attachment", "handle"],
            "where": [{
                "statement": "message.handle_id IN (:...handle_ids)",
                "args": {"handle_ids": handle_ids}
            }]
        }

        logger.info("Querying messages with payload: %s", payload)
        response = requests.post(f"{self.host}/api/v1/message/query?password={self.password}", json=payload)
        response.raise_for_status()
        return response.json()

    def get_handle_by_address(self, address):
        logger.info(f"Fetching handle by address: {address}")
        response = requests.post(f"{self.host}/api/v1/handle/query?password={self.password}", json={"addresses": [address]})
        response.raise_for_status()
        return response.json()
