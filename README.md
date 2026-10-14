# Inventory Management API

REST API to manage **categories**, **suppliers** and **products**, built with **FastAPI**, **SQLAlchemy ORM**, **MySQL** (PyMySQL driver) and **Pydantic**.

## Project Structure

```
inventory_api/
├── app/
│   ├── main.py            FastAPI app, exception handlers, health check
│   ├── config.py          Reads database settings from environment / .env
│   ├── database.py        Engine, session factory, Base, get_db dependency
│   ├── models.py          Category, Supplier, Product models + relationships
│   ├── schemas.py         Pydantic create / update / response schemas
│   ├── exceptions.py      NotFound / Conflict / BadRequest errors
│   ├── crud/              Database logic (category, supplier, product)
│   └── routers/           API routes (categories, suppliers, products)
├── sql/schema.sql         MySQL database and table structure
├── postman/               Postman collection with test cases
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

### 1. Prerequisites
- Python 3.10+
- MySQL Server 8.0.16+ running locally (8.0.16+ enforces the CHECK constraints)

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
```

### 3. Create the database

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS inventory_db CHARACTER SET utf8mb4;"
```

The tables are created automatically when the app starts. To create them manually instead, run:

```bash
mysql -u root -p < sql/schema.sql
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and enter your real MySQL details:

```bash
copy .env.example .env         # Windows
cp .env.example .env           # macOS / Linux
```

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=inventory_db
```

`.env` is listed in `.gitignore`. No credentials exist anywhere in the source code.

### 5. Run the application

```bash
uvicorn app.main:app --reload
```

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Health check: http://127.0.0.1:8000/health

## Database Design

| Table | Columns |
|---|---|
| categories | id, name (unique), description, created_at |
| suppliers | id, name, email (unique), phone_number, address, company_name, created_at |
| products | id, name, description, category_id (FK), supplier_id (FK), price, quantity, created_at, updated_at |

Relationships:
- One category has many products (`Category.products` / `Product.category`)
- One supplier has many products (`Supplier.products` / `Product.supplier`)
- Foreign keys use `ON DELETE RESTRICT`, so a category or supplier that still has products cannot be deleted.
- Database CHECK constraints: `price > 0` and `quantity >= 0`.

## API Endpoints

### Categories
| Method | Endpoint | Description |
|---|---|---|
| POST | /categories | Create a category |
| GET | /categories | List categories |
| GET | /categories/{category_id} | Get one category |
| PUT | /categories/{category_id} | Update a category |
| DELETE | /categories/{category_id} | Delete a category |

### Suppliers
| Method | Endpoint | Description |
|---|---|---|
| POST | /suppliers | Create a supplier |
| GET | /suppliers | List suppliers |
| GET | /suppliers/{supplier_id} | Get one supplier |
| PUT | /suppliers/{supplier_id} | Update a supplier |
| DELETE | /suppliers/{supplier_id} | Delete a supplier |
| GET | /suppliers/{supplier_id}/products | Products supplied by a supplier |

### Products
| Method | Endpoint | Description |
|---|---|---|
| POST | /products | Create a product |
| GET | /products | List products (supports filters below) |
| GET | /products/{product_id} | Get one product |
| PUT | /products/{product_id} | Update a product |
| DELETE | /products/{product_id} | Delete a product |
| GET | /products/inventory-value | Total inventory value |

### Search and filters (query parameters on `GET /products`)
| Parameter | Example | Meaning |
|---|---|---|
| search | `/products?search=laptop` | Name contains text (case-insensitive) |
| category_id | `/products?category_id=1` | Filter by category |
| supplier_id | `/products?supplier_id=1` | Filter by supplier |
| min_price, max_price | `/products?min_price=100&max_price=1000` | Price range |
| skip, limit | `/products?skip=0&limit=50` | Pagination (limit max 500) |

Filters can be combined, for example `/products?search=laptop&min_price=100&supplier_id=2`.

### Inventory value
`GET /products/inventory-value` returns `SUM(price × quantity)`:

```json
{
  "total_products": 3,
  "total_quantity": 25,
  "total_inventory_value": 5412.5
}
```

## Validation Rules

- Category name must be unique, supplier email must be unique (emails are stored in lowercase)
- Product price must be greater than 0 (max 2 decimal places), quantity must be 0 or more
- A product must reference an existing category and supplier
- Supplier name, email, phone number and company name are required; address is optional
- Update requests are partial: send only the fields to change, at least one field is required

## HTTP Status Codes

| Code | When |
|---|---|
| 200 | Successful read, update or delete |
| 201 | Record created |
| 400 | Invalid price range (min_price greater than max_price) |
| 404 | Record not found, or product references a non-existing category or supplier |
| 409 | Duplicate category name or supplier email, or deleting a category or supplier that still has products |
| 422 | Request data failed validation (negative price, negative quantity, bad email, etc.) |
| 503 | Database connection failed (MySQL down or wrong credentials) |
| 500 | Other unexpected database error |

Error responses look like:

```json
{ "detail": "Category with id 99 not found" }
```

## Testing

### Swagger UI
Open http://127.0.0.1:8000/docs and use **Try it out** on each endpoint.

### Postman
1. Import `postman/Inventory_API.postman_collection.json`
2. Make sure the app is running (the collection variable `base_url` defaults to `http://127.0.0.1:8000`)
3. Open the collection, click **Run**, and run all folders in order. IDs are saved automatically between requests, and each request has test scripts checking status codes and response data.

The collection covers: create, list, get by ID, update and delete for all three resources; search and filters; supplier products; inventory value; non-existing category and supplier; duplicate email and name; negative and zero price; negative quantity; empty and invalid updates; and delete protection.

### Manual test scenarios

| Scenario | How to test | Expected |
|---|---|---|
| Invalid database credentials | Put a wrong `DB_PASSWORD` in `.env`, restart, call `GET /categories` | 503 with a clear message; the password is not shown in the response or logs |
| Data persists after restart | Create records, stop the server (Ctrl+C), start it again, call the list endpoints | Records are still there |
| Credentials not in source code | Search the project for your password (for example `grep -r "yourpassword" app/`) | No matches; only `.env` contains it |

## Notes

- The app starts even if MySQL is unreachable. It logs an error and every database request returns 503 until the connection works, which makes the invalid-credentials test easy to run.
- Instead of the separate `DB_*` values you can set a single `DATABASE_URL` in `.env` (for example `mysql+pymysql://user:pass@localhost:3306/inventory_db`). If set, it takes priority.
- Never commit your real `.env` file.
