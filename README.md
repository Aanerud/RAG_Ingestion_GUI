# RAG Ingestion GUI

## Overview

**RAG Ingestion GUI** is a Python-based application that creates a Retrieval-Augmented Generation (RAG) database by ingesting messages from the BlueBubbles API and storing them in an Elasticsearch instance. The application features a PyQt-based GUI for easy interaction and management.

## Features

- Fetches messages from the BlueBubbles API.
- Extracts and stores notes and dates from messages.
- Uses the Ollama model for text embedding.
- Stores enriched data in Elasticsearch.
- Provides a user-friendly GUI for managing the ingestion process.

## Requirements

- Python 3.8+
- Docker (for running Elasticsearch)

## Installation

1. Clone the repository:

    ```sh
    git clone https://github.com/Aanerud/rag-ingestion-gui.git
    cd rag-ingestion-gui
    ```

2. Create a virtual environment and activate it:

    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. Install the required Python packages:

    ```sh
    pip install -r requirements.txt
    ```

4. Set up Elasticsearch using Docker:

    ```sh
    docker pull docker.elastic.co/elasticsearch/elasticsearch:8.12.2
    docker run -d --name elasticsearch -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:8.12.2
    ```

## Usage

1. Start the application:

    ```sh
    python main.py
    ```

2. Fill in the required fields in the GUI:
    - **BlueBubbles Host**: The host address for the BlueBubbles server.
    - **BlueBubbles Password**: The password for the BlueBubbles server.
    - **Elasticsearch Host**: The host address for the Elasticsearch server.

3. Click the **Ingest Messages** button to start the ingestion process.

## File Descriptions

- **main.py**: The main entry point for the application.
- **api_client.py**: Contains the `BlueBubblesAPI` class for interacting with the BlueBubbles API.
- **elasticsearch_client.py**: Contains the `ElasticsearchClient` class for managing Elasticsearch operations.
- **message_preprocessing.py**: Provides functions for preprocessing messages and extracting notes and dates.
- **gui.py**: Implements the PyQt-based GUI.
- **requirements.txt**: Lists the required Python packages.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.