from elasticsearch import Elasticsearch

def reset_elasticsearch(host="http://localhost:9200"):
    client = Elasticsearch(hosts=[host])
    indices = client.indices.get_alias(index="*")
    for index in indices:
        client.indices.delete(index=index)
    print("Elasticsearch indices have been reset.")

if __name__ == "__main__":
    reset_elasticsearch()
