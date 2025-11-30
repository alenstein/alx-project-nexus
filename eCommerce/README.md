# Scalable eCommerce Backend API

This repository contains the source code for a robust, scalable, and secure backend system designed for a modern eCommerce platform. Built with Django and the Django REST Framework, this project serves as a production-ready foundation for managing products, user authentication, and shopping cart functionality.

The entire application is containerized with Docker and includes a complete CI/CD pipeline for automated testing and deployment to AWS, making it an excellent reference for modern backend development practices.

![Project Architecture](https://i.imgur.com/your-architecture-diagram.png) <!-- Optional: Create and upload an architecture diagram -->

---

## Key Features

*   **RESTful API:** A complete API for managing products, categories, users, and shopping carts.
*   **JWT Authentication:** Secure, token-based authentication for all user-related endpoints, including registration with email confirmation.
*   **Asynchronous Task Processing:** Celery and Redis are integrated to handle background tasks like sending confirmation emails, ensuring a fast and responsive user experience.
*   **Advanced Product Filtering:** The API supports searching, filtering by category and brand, and sorting by price.
*   **Pagination:** All list endpoints are paginated to ensure efficient handling of large datasets.
*   **Automated API Documentation:** The project uses `drf-spectacular` to automatically generate an OpenAPI 3.0 schema, with interactive Swagger UI and ReDoc interfaces.
*   **Containerized Environment:** The entire application stack (Django, PostgreSQL, Redis, Celery) is containerized with Docker for consistent development and production environments.
*   **Automated CI/CD Pipeline:** A GitHub Actions workflow automates testing, Docker image builds, and deployment to an AWS EC2 instance.
*   **Production-Ready Deployment:** The project is deployed on AWS EC2 with Nginx as a reverse proxy and UFW for firewall management.

---

## Technology Stack & Architecture

This project follows a standard, high-performance architecture for modern web applications.

*   **Backend:** Django, Django REST Framework (DRF)
*   **Database:** PostgreSQL
*   **Application Server:** Gunicorn
*   **Asynchronous Tasks:** Celery, Redis
*   **Containerization:** Docker, Docker Compose
*   **API Documentation:** `drf-spectacular` (Swagger UI / ReDoc)
*   **CI/CD:** GitHub Actions
*   **Deployment:** AWS EC2, Nginx, UFW

### Deployment Architecture

1.  **Nginx (Reverse Proxy):** Acts as the entry point for all incoming traffic. It serves static and media files directly for high performance and forwards all other requests to the Gunicorn application server.
2.  **Gunicorn (Application Server):** Manages the Django application, running multiple worker processes to handle concurrent requests.
3.  **Docker & Docker Compose:** The entire application stack, including the database, cache, and application server, is containerized, ensuring consistency and isolation.
4.  **GitHub Actions (CI/CD):** Automates the entire deployment process, from running tests to deploying the latest version of the application to the server.

---

## Getting Started

### Prerequisites

*   Docker and Docker Compose
*   An active Docker Hub account (for pushing images if you fork the project)
*   An AWS account with a configured EC2 instance (for production deployment)

### Local Development

This project is configured for easy local development using a dedicated development compose file.

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/your-username/alx-project-nexus.git
    cd alx-project-nexus
    ```

2.  **Create a `.env` file:**
    Create a `.env` file in the project root by copying the example file. This file will hold your local environment variables.
    ```sh
    cp .env.example .env
    ```
    Fill in the `.env` file with your desired local settings for the database, secret key, etc.

3.  **Build and run the services:**
    Use the `docker-compose.dev.yml` file to build and run the containers.
    ```sh
    docker-compose -f docker-compose.dev.yml up --build
    ```

4.  **Access the application:**
    *   **API:** `http://localhost:8000/`
    *   **Admin:** `http://localhost:8000/admin/`
    *   **Swagger UI:** `http://localhost:8000/api/swagger-ui/`

---

## Production Deployment

The production deployment is fully automated via the GitHub Actions CI/CD pipeline defined in `.github/workflows/cd.yml`. **There are no manual deployment steps.**

### Deployment Process

1.  **Trigger:** The workflow is triggered when a pull request is merged into the `main` branch.
2.  **Build & Push:** A production-ready Docker image is built and pushed to Docker Hub.
3.  **Deploy to EC2:** The workflow securely connects to the production server via SSH.
4.  **Server-Side Script:** On the server, the script automatically:
    *   Sets up the required directories (`/var/www/ecommerce/`) and permissions for Nginx.
    *   Creates the `.env` and `docker-compose.yml` files from GitHub Secrets.
    *   Stops any old containers and prunes the Docker system to ensure a clean state.
    *   Pulls the new Docker image from Docker Hub.
    *   Starts the application stack in detached mode using Docker Compose.
    *   Configures and restarts the Nginx reverse proxy to serve the application and its static/media files.

### Replicating the Deployment

To fork this project and deploy it to your own server, you must configure the following secrets in your repository's settings (`Settings > Secrets and variables > Actions`):

*   `EC2_HOST`: The public IP address of your EC2 instance.
*   `EC2_USERNAME`: The username for the EC2 instance (e.g., `ubuntu`).
*   `EC2_SSH_PRIVATE_KEY`: The private SSH key used to access the EC2 instance.
*   `DOCKERHUB_USERNAME`: Your Docker Hub username.
*   `DOCKERHUB_TOKEN`: A Docker Hub access token with push permissions.
*   `SECRET_KEY`: Your Django secret key.
*   `ALLOWED_HOSTS`: A comma-separated list of allowed hosts (e.g., `your_server_ip,your_domain.com`).
*   `DB_NAME`, `DB_USER`, `DB_PASSWORD`: Credentials for the PostgreSQL database.
*   ... (and all other secrets required by your `.env` file).

---

## API Documentation

The API documentation is automatically generated and can be accessed at the following endpoints on your deployed server:

*   **Swagger UI:** `http://<your_server_ip>/api/swagger-ui/`
*   **ReDoc:** `http://<your_server_ip>/api/redoc/`
*   **Schema:** `http://<your_server_ip>/api/schema/`

These interactive interfaces provide a clear overview of all available endpoints, their expected request/response formats, and allow for direct testing of the API.
