# Products Recommender API

## 1\. Introduction

This document provides a comprehensive overview of the Products Recommender API. This system leverages vector embeddings and a Qdrant vector database to provide efficient and semantically aware product recommendations. It integrates with a PostgreSQL database for product data management and uses FastEmbed for generating high-quality text embeddings.

## 2\. Features

  * **Semantic Product Search:** Find products based on the meaning of a query, not just keywords.

  * **Similar Product Recommendations:** Discover products semantically similar to a given product ID.

  * **Data Synchronization:** Automated process to fetch product data from PostgreSQL, generate embeddings, and upload them to Qdrant.

  * **Health and Status Monitoring:** Endpoints to check the status of the synchronization process and database/vector store connections.

  * **Secure Administration Endpoints:** Admin functionalities are protected by HTTP Bearer authentication.

## 3\. API Endpoints

The API is structured under `/api/v1/` and provides the following endpoints:

### 3.1. Admin Endpoints (`/api/v1/admin`)

These endpoints are designed for administrative tasks, primarily related to data synchronization and system health.

#### `POST /api/v1/admin/sync`

  * **Summary:** Sync Products

  * **Description:** Initiates the main synchronization process. This endpoint fetches products from PostgreSQL that have not yet been indexed in Qdrant (`qdrant_indexed is FALSE`), generates their vector embeddings, uploads these embeddings to the Qdrant vector database, and subsequently updates the `qdrant_indexed` flag to `TRUE` along with setting the `qdrant_indexed_at` timestamp in PostgreSQL.

  * **Request Body:** `SyncRequest` (JSON schema reference)

  * **Responses:**

      * `200 OK`: Successful synchronization.

      * `422 Unprocessable Entity`: Validation error for request body.

  * **Security:** Requires `HTTPBearer` authentication.

#### `GET /api/v1/admin/sync/status`

  * **Summary:** Get Sync Status

  * **Description:** Retrieves current status information regarding the product synchronization process. This includes details such as the last synchronization timestamp, collection information from Qdrant, and the current connection status of the PostgreSQL database.

  * **Responses:**

      * `200 OK`: Successful retrieval of sync status.

  * **Security:** Requires `HTTPBearer` authentication.

#### `POST /api/v1/admin/sync/test-connection`

  * **Summary:** Test Connections

  * **Description:** Provides a utility to test the connectivity to both the PostgreSQL database and the Qdrant vector database. This is particularly useful for debugging connectivity issues during deployment or operation.

  * **Responses:**

      * `200 OK`: Successful response indicating connection statuses.

  * **Security:** Requires `HTTPBearer` authentication.

### 3.2. Product Endpoints (`/api/v1/products`)

These endpoints facilitate product discovery and recommendations based on semantic similarity.

#### `POST /api/v1/products/similar`

  * **Summary:** Get Similar Products

  * **Description:** This endpoint retrieves products semantically similar to a given `product_id` (integer or convertible string) by directly querying the Qdrant vector database using vector similarity search.

  * **Request Body:** `SimilarProductsRequest` (JSON schema reference)

  * **Responses:**

      * `200 OK`: Successful retrieval of similar products.

      * `422 Unprocessable Entity`: Validation error for request body.

#### `POST /api/v1/products/search`

  * **Summary:** Semantic Search

  * **Description:** Performs a semantic search for products using a natural language text query. This endpoint takes a text string, generates its vector embedding using the configured embedding model, and then returns the most relevant products from Qdrant based on semantic similarity to the query.

  * **Request Body:** `SemanticQueryRequest` (JSON schema reference)

  * **Responses:**

      * `200 OK`: Successful retrieval of search results.

      * `422 Unprocessable Entity`: Validation error for request body.

### 3.3. Core Application Endpoints

#### `GET /`

  * **Summary:** Root

  * **Description:** The root endpoint providing basic API information.

  * **Responses:**

      * `200 OK`: Successful response with API information.

#### `GET /health`

  * **Summary:** Health Check

  * **Description:** A simple health check endpoint to verify the application's operational status.

  * **Responses:**

      * `200 OK`: Successful response indicating application health.

## 4\. Installation

Detailed installation instructions will be provided here. It is recommended to use Python 3.9+ and create a virtual environment for dependency management.

**Using `uv` for Virtual Environment and Package Management:**

If you use `uv` (a fast Python package installer and resolver, often used as a `pip` and `venv` replacement), follow these steps:

1.  **Install `uv`:**

    ```bash
    pip install uv
    ```

2.  **Create and Activate Virtual Environment:**

    ```bash
    uv venv .venv
    source .venv/bin/activate
    ```

    Alternatively, you can use the standard `venv` module:

    ```bash
    python3.9 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Cloning the Repository:**

    ```
    git clone <repository_url>
    cd <repository_directory>
    ```

4.  **Setting up Environment Variables:**
    Create a `.env` file based on a provided `.env.example` with your database credentials, Qdrant URL, and other configuration settings. Key variables include: `POSTGRES_URL`, `QDRANT_URL`, `QDRANT_PORT`, `API_BEARER_TOKEN`, and `EMBEDDING_MODEL_NAME`.

5.  **Installing Dependencies:**

    ```
    uv pip install -r requirements.txt
    # Or for specific packages:
    # uv pip install fastapi uvicorn asyncpg qdrant-client fastembed python-dotenv
    ```

6.  **Database Setup:**
    Ensure your PostgreSQL database is running and the necessary tables (e.g., `products`) are created.

7.  **Qdrant Setup:**
    Ensure your Qdrant instance is running. You can run it via Docker:
    For a more streamlined local development environment, consider providing a `docker-compose.yml` file that that orchestrates both PostgreSQL and Qdrant services. This simplifies setup and management.

    ```
    docker pull qdrant/qdrant
    docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
    ```

## 5\. Usage

To run the application:

```
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API documentation (Swagger UI) will be available at `http://localhost:8000/docs`.

## 6\. Security

Administrative endpoints (`/api/v1/admin/*`) are secured using HTTP Bearer Token authentication. Ensure that a valid token is provided in the `Authorization` header for these requests.

## 7\. Contributing

Information on how to contribute to the project will be provided here.

## 8\. License

This project is licensed under the MIT License.