# Product App

## Overview

The `product` app is the core of the eCommerce platform's catalog management system. It is responsible for handling all data related to products, including their categories, brands, pricing, and inventory. The design emphasizes a normalized data structure to ensure data integrity and support efficient querying.

---

## Data Models

The app's data model is designed to be flexible and scalable, separating core product information from its variations and attributes.

*   **`Product`**: The central model representing a unique product (e.g., "Classic Crewneck T-Shirt"). It holds general information like the product name, description, category, and brand.

*   **`ProductCategory`**, **`Brand`**, **`Colour`**, **`SizeOption`**: These are lookup tables that provide standardized attributes for products. Using foreign keys to these models prevents data duplication and makes filtering more efficient.

*   **`ProductItem`**: Represents a specific version of a `Product`, typically defined by its color. For example, a "Classic Crewneck T-Shirt" (`Product`) might have a "Red" version and a "Blue" version, each being a separate `ProductItem`. This model holds the SKU base and price.

*   **`ProductImage`**: Linked to a `ProductItem`, this model stores images for a specific product variant (e.g., images of the red t-shirt).

*   **`ProductVariation`**: The most granular model, representing a specific size of a `ProductItem` (e.g., the "Red" t-shirt in size "M"). This model holds the final quantity in stock.

---

## API Endpoints

The `product` app exposes the following public endpoints for interacting with the product catalog.

### List & Search Products

*   **Endpoint:** `GET /api/v1/products/`
*   **Description:** Retrieves a paginated list of all available products.
*   **Features:**
    *   **Filtering:** Supports filtering by `category` and `brand` (e.g., `?category=T-Shirts&brand=Nike`).
    *   **Searching:** Supports full-text search on product names and descriptions (e.g., `?search=hoodie`).
    *   **Sorting:** Supports sorting by `price` (e.g., `?ordering=original_price` for ascending, `?ordering=-original_price` for descending).
    *   **Pagination:** Returns results in pages to ensure fast and efficient responses.

### Retrieve a Single Product

*   **Endpoint:** `GET /api/v1/products/{id}/`
*   **Description:** Retrieves the detailed information for a single product, including all its available items, colors, sizes, and stock levels.
