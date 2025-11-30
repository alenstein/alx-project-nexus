# Users App

## Overview

The `users` app is responsible for all aspects of user management, authentication, and authorization within the eCommerce platform. It features a custom user model to provide flexibility beyond Django's default, and it uses JSON Web Tokens (JWT) for secure, stateless authentication.

---

## Data Models

*   **`SiteUser`**: This is the custom user model that replaces Django's default `User`. It uses the email address as the unique identifier (username) and includes standard fields like `first_name`, `last_name`, and `is_active`. Using a custom user model from the start is a best practice that allows for easy future extension.

*   **`UserAddress`**: This model stores shipping and billing addresses associated with a `SiteUser`. A user can have multiple addresses, with one marked as the default.

---

## Key Features & Logic

*   **Email as Username:** The system uses the email address for login, which is a common and user-friendly approach.
*   **Asynchronous Email Confirmation:** Upon registration, a new user is created in an `is_active=False` state. A Celery background task is dispatched to send a confirmation email with a unique activation link. This ensures the user registration process is fast and does not get blocked by email sending delays.
*   **JWT-Based Authentication:** The application uses `djangorestframework-simplejwt` to handle authentication. Upon successful login, the API provides short-lived access tokens and long-lived refresh tokens, which is a standard and secure practice for modern APIs.

---

## API Endpoints

The `users` app exposes the following endpoints for authentication and user profile management.

### Authentication

*   **Endpoint:** `POST /api/v1/auth/register/`
    *   **Description:** Allows a new user to register. Creates an inactive user and triggers the confirmation email.

*   **Endpoint:** `GET /api/v1/auth/confirm-email/{uidb64}/{token}/`
    *   **Description:** A special endpoint that the user visits by clicking the link in their email. It validates the token and activates the user's account.

*   **Endpoint:** `POST /api/v1/token/`
    *   **Description:** The login endpoint. Takes the user's email and password and returns JWT access and refresh tokens upon success.

*   **Endpoint:** `POST /api/v1/token/refresh/`
    *   **Description:** Takes a valid refresh token and returns a new access token.

*   **Endpoint:** `POST /api/v1/auth/logout/`
    *   **Description:** Blacklists the user's current refresh token, effectively logging them out. Requires authentication.

### User & Address Management

*   **Endpoint:** `GET, PUT, PATCH /api/v1/auth/user/`
    *   **Description:** Allows an authenticated user to retrieve or update their own profile details.

*   **Endpoint:** `GET, POST /api/v1/auth/addresses/`
    *   **Description:** Allows an authenticated user to view their list of saved addresses or add a new one.

*   **Endpoint:** `GET, PUT, DELETE /api/v1/auth/addresses/{id}/`
    *   **Description:** Allows an authenticated user to retrieve, update, or delete a specific address.
