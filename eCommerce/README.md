# E-Commerce Backend

This project is a robust backend system for an e-commerce product catalog. It handles product data management, user authentication, and provides APIs for filtering, sorting, and pagination, simulating a real-world scenario for backend engineers.

## Project Goals

-   **CRUD APIs:** Build APIs for managing products, categories, and user authentication.
-   **Filtering, Sorting, Pagination:** Implement robust logic for efficient product discovery.
-   **Database Optimization:** Design a high-performance database schema to support seamless queries.

## Technologies Used

-   **Django & Django Rest Framework:** For building a scalable backend framework.
-   **PostgreSQL:** As the relational database for optimized performance.
-   **django-environ:** For managing environment variables.
-   **JWT (JSON Web Tokens):** For secure, stateless user authentication.
-   **drf-yasg (Swagger/OpenAPI):** To automatically generate API documentation.

## Key Features

-   **User Management:** Custom user model with email-based authentication.
-   **Product Catalog:** A multi-tiered product model including categories, brands, colors, and sizes.
-   **Shopping Cart:** A persistent shopping cart for each user.
-   **API Documentation:** Automatically generated and interactive API documentation.

## Project Structure

The project is organized into the following Django apps:

-   `eCommerce/`: The main project directory containing settings and root URL configuration.
-   `users/`: Manages user accounts, authentication, and addresses.
-   `product/`: Handles the product catalog, including categories, products, and inventory.
-   `cart/`: Manages the shopping cart and its items.

## Getting Started

### Prerequisites

-   Python 3.8+
-   PostgreSQL
-   Git

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd eCommerce
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Configure environment variables:**
    -   Rename the `.env.example` file to `.env`.
    -   Update the `.env` file with your database credentials and a new Django `SECRET_KEY`.
    ```bash
    mv .env.example .env
    # Now edit the .env file
    ```

4.  **Set up the database:**
    -   Ensure your PostgreSQL server is running.
    -   Create a new database with the name you specified in your `.env` file.

5.  **Run database migrations:**
    ```bash
    python manage.py migrate
    ```

6.  **Create a superuser:**
    This will allow you to access the Django admin interface.
    ```bash
    python manage.py createsuperuser
    ```

7.  **Run the development server:**
    ```bash
    python manage.py runserver
    ```
    The API will be available at `http://127.0.0.1:8000/`.

## API Endpoints

The API is versioned under `/api/v1/`.

-   **Admin:** `http://127.0.0.1:8000/admin/`
-   **API Documentation:**
    -   Swagger UI: `http://127.0.0.1:8000/swagger/`
    -   ReDoc: `http://127.0.0.1:8000/redoc/`
-   **Authentication:**
    -   `POST /api/v1/token/`: Obtain JWT token pair (access and refresh).
    -   `POST /api/v1/token/refresh/`: Refresh an expired access token.
    -   User registration and management endpoints are available under `/api/v1/auth/`.
-   **Products:** `/api/v1/products/`
-   **Shopping Cart:** `/api/v1/cart/`

## Git Commit Workflow

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification. The following is a recommended sequence of commits that aligns with the project roadmap.

### Phase 0: Project Setup
-   `feat: set up Django project with PostgreSQL`


### Phase 1: User Authentication
- `feat(users): implement complete user registration flow with serializers, views, and tests`

### Phase 2: Product Catalog API
-   `feat(product): create serializers for all product models`
-   `feat(product): implement read-only API for product listing and detail`
-   `feat(product): add filtering, sorting, and pagination to product list`
-   `feat(product): implement admin-only viewset for product CRUD operations`
-   `test(product): add tests for public product API endpoints`

### Phase 3: Shopping Cart Functionality
-   `feat(cart): create serializers for shopping cart and cart items`
-   `feat(cart): implement API views for managing the user's cart`
-   `fix(cart): ensure users can only access their own cart`
-   `test(cart): add tests for adding items and viewing the cart`

### Phase 4: Optimization and Documentation
-   `perf(models): add database indexes to frequently filtered fields`
-   `docs(api): review and add detailed descriptions to Swagger documentation`
-   `refactor: improve code structure and maintainability`
