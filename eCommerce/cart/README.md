# Cart App

## Overview

The `cart` app provides the complete shopping cart functionality for the eCommerce platform. It is responsible for managing items that users have selected for purchase. The design ensures that each authenticated user has a persistent cart linked to their account.

---

## Data Models

The app's data model is centered around two main components: the shopping cart itself and the items within it.

*   **`ShoppingCart`**: This model represents a user's shopping cart. It is linked directly to a `SiteUser` via a one-to-one relationship, ensuring that each user has a single, unique cart.

*   **`CartItem`**: This model represents a specific product variation that has been added to a `ShoppingCart`. It holds a foreign key to the `ProductVariation` model (which specifies the product, color, and size) and stores the `quantity` selected by the user.

---

## API Endpoints

The `cart` app exposes the following endpoints for managing a user's shopping cart. All endpoints require JWT-based authentication.

### View and Add to Cart

*   **Endpoint:** `GET /api/v1/cart/`
    *   **Description:** Retrieves the contents of the currently authenticated user's shopping cart, including a list of all items and the calculated total price.

*   **Endpoint:** `POST /api/v1/cart/`
    *   **Description:** Adds a new product variation to the user's shopping cart.
    *   **Body:** Requires a `product_variation_id` and `quantity`.

### Update and Remove Cart Items

*   **Endpoint:** `PUT /api/v1/cart/{item_id}/`
    *   **Description:** Updates the quantity of a specific item in the user's cart.
    *   **Body:** Requires the new `quantity`.

*   **Endpoint:** `DELETE /api/v1/cart/{item_id}/`
    *   **Description:** Removes a specific item from the user's shopping cart entirely.
