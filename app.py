import json
from decimal import Decimal
from datetime import date, datetime
from flask import Flask, jsonify, request, render_template
from config import Config
from db import get_db_cursor, check_db_health

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

# ---------------------------------------------------------------------
# Custom JSON encoder helper for Decimals and Datetime objects
# ---------------------------------------------------------------------
def format_row(row):
    """Recursively converts Decimal and Datetime types to JSON-serializable types."""
    if isinstance(row, dict):
        return {k: format_row(v) for k, v in row.items()}
    elif isinstance(row, list):
        return [format_row(item) for item in row]
    elif isinstance(row, Decimal):
        return float(row)
    elif isinstance(row, (datetime, date)):
        return row.strftime("%Y-%m-%d %H:%M:%S")
    return row

def serialize_response(data, status_code=200):
    """Helper to return formatted JSON responses."""
    return jsonify(format_row(data)), status_code

def error_response(message, status_code=400, details=None):
    """Standardized error response."""
    payload = {"success": False, "error": message}
    if details:
        payload["details"] = details
    return jsonify(payload), status_code

# ---------------------------------------------------------------------
# Web Frontend Route
# ---------------------------------------------------------------------
@app.route("/")
def index():
    """Serves the Single-Page Application dashboard."""
    return render_template("index.html")

# ---------------------------------------------------------------------
# Health & Status Endpoint
# ---------------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health():
    """Returns database connection status and table existence."""
    health_data = check_db_health()
    status_code = 200 if health_data["connected"] else 503
    return jsonify(health_data), status_code

# ---------------------------------------------------------------------
# Authors API Endpoints
# ---------------------------------------------------------------------
@app.route("/api/authors", methods=["GET"])
def get_authors():
    """Retrieve all authors."""
    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute("""
                SELECT AuthorID, AuthorName, Country, CreatedAt
                FROM Authors
                ORDER BY AuthorName ASC;
            """)
            authors = cursor.fetchall()
            return serialize_response({"success": True, "authors": authors})
    except Exception as e:
        return error_response("Failed to fetch authors", 500, str(e))

@app.route("/api/authors", methods=["POST"])
def add_author():
    """Add a new author."""
    data = request.get_json() or {}
    name = (data.get("AuthorName") or "").strip()
    country = (data.get("Country") or "").strip()

    if not name:
        return error_response("Author name is required.")
    if not country:
        return error_response("Author country is required.")

    try:
        with get_db_cursor(commit=True) as (cursor, _):
            cursor.execute(
                "INSERT INTO Authors (AuthorName, Country) VALUES (%s, %s);",
                (name, country)
            )
            new_id = cursor.lastrowid
            return serialize_response({
                "success": True,
                "message": f"Author '{name}' added successfully.",
                "AuthorID": new_id
            }, 201)
    except Exception as e:
        return error_response("Failed to add author", 500, str(e))

# ---------------------------------------------------------------------
# Books API Endpoints (CRUD)
# ---------------------------------------------------------------------
@app.route("/api/books", methods=["GET"])
def get_books():
    """
    Retrieve all books with their author details.
    Supports optional search filter: /api/books?q=search_term
    """
    search_query = request.args.get("q", "").strip()

    try:
        with get_db_cursor() as (cursor, _):
            if search_query:
                query = """
                    SELECT 
                        b.BookID, 
                        b.Title, 
                        b.AuthorID, 
                        a.AuthorName, 
                        a.Country AS AuthorCountry,
                        b.Price, 
                        b.StockQuantity,
                        b.CreatedAt
                    FROM Books b
                    JOIN Authors a ON b.AuthorID = a.AuthorID
                    WHERE b.Title LIKE %s OR a.AuthorName LIKE %s
                    ORDER BY b.BookID DESC;
                """
                wildcard = f"%{search_query}%"
                cursor.execute(query, (wildcard, wildcard))
            else:
                query = """
                    SELECT 
                        b.BookID, 
                        b.Title, 
                        b.AuthorID, 
                        a.AuthorName, 
                        a.Country AS AuthorCountry,
                        b.Price, 
                        b.StockQuantity,
                        b.CreatedAt
                    FROM Books b
                    JOIN Authors a ON b.AuthorID = a.AuthorID
                    ORDER BY b.BookID DESC;
                """
                cursor.execute(query)

            books = cursor.fetchall()
            return serialize_response({"success": True, "count": len(books), "books": books})
    except Exception as e:
        return error_response("Failed to fetch books", 500, str(e))

@app.route("/api/books", methods=["POST"])
def add_book():
    """Add a new book to the inventory."""
    data = request.get_json() or {}
    title = (data.get("Title") or "").strip()
    author_id = data.get("AuthorID")
    price = data.get("Price")
    stock = data.get("StockQuantity", 0)

    # Validations
    if not title:
        return error_response("Book title is required.")
    if author_id is None:
        return error_response("Valid Author ID is required.")
    try:
        price = float(price)
        if price < 0:
            return error_response("Price must be greater than or equal to 0.")
    except (ValueError, TypeError):
        return error_response("Price must be a valid positive number.")

    try:
        stock = int(stock)
        if stock < 0:
            return error_response("Stock quantity cannot be negative.")
    except (ValueError, TypeError):
        return error_response("Stock quantity must be a non-negative integer.")

    try:
        with get_db_cursor(commit=True) as (cursor, _):
            # Check if Author exists
            cursor.execute("SELECT AuthorID, AuthorName FROM Authors WHERE AuthorID = %s;", (author_id,))
            author = cursor.fetchone()
            if not author:
                return error_response(f"Author with ID {author_id} does not exist.", 404)

            # Insert book
            cursor.execute(
                """
                INSERT INTO Books (Title, AuthorID, Price, StockQuantity)
                VALUES (%s, %s, %s, %s);
                """,
                (title, author_id, price, stock)
            )
            new_id = cursor.lastrowid
            return serialize_response({
                "success": True,
                "message": f"Book '{title}' added successfully.",
                "BookID": new_id
            }, 201)
    except Exception as e:
        return error_response("Failed to add book", 500, str(e))

@app.route("/api/books/<int:book_id>", methods=["PUT"])
def update_book(book_id):
    """Update an existing book's details, price, or stock."""
    data = request.get_json() or {}
    title = (data.get("Title") or "").strip()
    author_id = data.get("AuthorID")
    price = data.get("Price")
    stock = data.get("StockQuantity")

    if not title:
        return error_response("Book title is required.")
    if author_id is None:
        return error_response("Valid Author ID is required.")

    try:
        price = float(price)
        if price < 0:
            return error_response("Price must be greater than or equal to 0.")
    except (ValueError, TypeError):
        return error_response("Price must be a valid number.")

    try:
        stock = int(stock)
        if stock < 0:
            return error_response("Stock quantity cannot be negative.")
    except (ValueError, TypeError):
        return error_response("Stock quantity must be a valid integer.")

    try:
        with get_db_cursor(commit=True) as (cursor, _):
            # Verify book exists
            cursor.execute("SELECT BookID FROM Books WHERE BookID = %s;", (book_id,))
            if not cursor.fetchone():
                return error_response(f"Book with ID {book_id} not found.", 404)

            # Verify author exists
            cursor.execute("SELECT AuthorID FROM Authors WHERE AuthorID = %s;", (author_id,))
            if not cursor.fetchone():
                return error_response(f"Author with ID {author_id} not found.", 404)

            cursor.execute(
                """
                UPDATE Books
                SET Title = %s, AuthorID = %s, Price = %s, StockQuantity = %s
                WHERE BookID = %s;
                """,
                (title, author_id, price, stock, book_id)
            )
            return serialize_response({
                "success": True,
                "message": f"Book #{book_id} updated successfully."
            })
    except Exception as e:
        return error_response("Failed to update book", 500, str(e))

@app.route("/api/books/<int:book_id>", methods=["DELETE"])
def delete_book(book_id):
    """
    Remove a book.
    If the book has existing orders, foreign key constraint (RESTRICT) prevents deletion.
    """
    try:
        with get_db_cursor(commit=True) as (cursor, _):
            # Check if book exists
            cursor.execute("SELECT Title FROM Books WHERE BookID = %s;", (book_id,))
            book = cursor.fetchone()
            if not book:
                return error_response(f"Book with ID {book_id} not found.", 404)

            # Check if referenced in Orders
            cursor.execute("SELECT COUNT(*) AS order_count FROM Orders WHERE BookID = %s;", (book_id,))
            orders_ref = cursor.fetchone()["order_count"]
            if orders_ref > 0:
                return error_response(
                    f"Cannot delete '{book['Title']}' because it has {orders_ref} historical order(s). "
                    "In RDBMS, foreign key integrity preserves audit history. "
                    "To hide this book, consider setting its Stock to 0 instead.",
                    409
                )

            cursor.execute("DELETE FROM Books WHERE BookID = %s;", (book_id,))
            return serialize_response({
                "success": True,
                "message": f"Book '{book['Title']}' (ID #{book_id}) deleted successfully."
            })
    except Exception as e:
        return error_response("Failed to delete book", 500, str(e))

# ---------------------------------------------------------------------
# Customers API Endpoints (CRUD)
# ---------------------------------------------------------------------
@app.route("/api/customers", methods=["GET"])
def get_customers():
    """Retrieve all customers along with their order counts."""
    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute("""
                SELECT 
                    c.CustomerID, 
                    c.FullName, 
                    c.Email, 
                    c.Phone, 
                    c.City, 
                    c.CreatedAt,
                    COUNT(o.OrderID) AS OrderCount
                FROM Customers c
                LEFT JOIN Orders o ON c.CustomerID = o.CustomerID
                GROUP BY c.CustomerID, c.FullName, c.Email, c.Phone, c.City, c.CreatedAt
                ORDER BY c.CustomerID DESC;
            """)
            customers = cursor.fetchall()
            return serialize_response({"success": True, "count": len(customers), "customers": customers})
    except Exception as e:
        return error_response("Failed to fetch customers", 500, str(e))

@app.route("/api/customers", methods=["POST"])
def add_customer():
    """Register a new customer."""
    data = request.get_json() or {}
    name = (data.get("FullName") or "").strip()
    email = (data.get("Email") or "").strip()
    phone = (data.get("Phone") or "").strip()
    city = (data.get("City") or "").strip()

    if not name:
        return error_response("Customer full name is required.")
    if not email:
        return error_response("Email address is required.")
    if "@" not in email or "." not in email:
        return error_response("Please provide a valid email address.")
    if not phone:
        return error_response("Phone number is required.")
    if not city:
        return error_response("City is required.")

    try:
        with get_db_cursor(commit=True) as (cursor, _):
            # Check unique email
            cursor.execute("SELECT CustomerID FROM Customers WHERE Email = %s;", (email,))
            if cursor.fetchone():
                return error_response(f"A customer with email '{email}' already exists.", 409)

            cursor.execute(
                """
                INSERT INTO Customers (FullName, Email, Phone, City)
                VALUES (%s, %s, %s, %s);
                """,
                (name, email, phone, city)
            )
            new_id = cursor.lastrowid
            return serialize_response({
                "success": True,
                "message": f"Customer '{name}' registered successfully.",
                "CustomerID": new_id
            }, 201)
    except Exception as e:
        return error_response("Failed to add customer", 500, str(e))

@app.route("/api/customers/<int:customer_id>", methods=["DELETE"])
def delete_customer(customer_id):
    """
    Delete a customer. 
    By schema definition, CASCADE automatically removes their orders.
    """
    try:
        with get_db_cursor(commit=True) as (cursor, _):
            cursor.execute("SELECT FullName FROM Customers WHERE CustomerID = %s;", (customer_id,))
            customer = cursor.fetchone()
            if not customer:
                return error_response(f"Customer #{customer_id} not found.", 404)

            cursor.execute("DELETE FROM Customers WHERE CustomerID = %s;", (customer_id,))
            return serialize_response({
                "success": True,
                "message": f"Customer '{customer['FullName']}' and their associated orders were removed."
            })
    except Exception as e:
        return error_response("Failed to delete customer", 500, str(e))

# ---------------------------------------------------------------------
# Orders API Endpoints (Transactions & Joins)
# ---------------------------------------------------------------------
@app.route("/api/orders", methods=["GET"])
def get_orders():
    """Retrieve all orders with customer, book, and author details."""
    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute("""
                SELECT 
                    o.OrderID,
                    o.OrderDate,
                    o.CustomerID,
                    c.FullName AS CustomerName,
                    c.Email AS CustomerEmail,
                    o.BookID,
                    b.Title AS BookTitle,
                    a.AuthorName,
                    b.Price AS UnitPrice,
                    o.QuantityOrdered,
                    o.TotalAmount
                FROM Orders o
                JOIN Customers c ON o.CustomerID = c.CustomerID
                JOIN Books b ON o.BookID = b.BookID
                JOIN Authors a ON b.AuthorID = a.AuthorID
                ORDER BY o.OrderID DESC;
            """)
            orders = cursor.fetchall()
            return serialize_response({"success": True, "count": len(orders), "orders": orders})
    except Exception as e:
        return error_response("Failed to fetch orders", 500, str(e))

@app.route("/api/orders", methods=["POST"])
def place_order():
    """
    Place a new book order.
    Demonstrates ACID transaction:
      1. Locks and verifies Book stock.
      2. Validates Customer existence.
      3. Calculates TotalAmount = Price * QuantityOrdered.
      4. Deducts StockQuantity from Books table.
      5. Inserts record into Orders table.
      6. Commits transaction atomically.
    """
    data = request.get_json() or {}
    customer_id = data.get("CustomerID")
    book_id = data.get("BookID")
    quantity = data.get("QuantityOrdered")

    if not customer_id:
        return error_response("Customer selection is required.")
    if not book_id:
        return error_response("Book selection is required.")
    try:
        quantity = int(quantity)
        if quantity <= 0:
            return error_response("Quantity must be at least 1.")
    except (ValueError, TypeError):
        return error_response("Quantity must be a positive integer.")

    try:
        with get_db_cursor(commit=True) as (cursor, conn):
            # 1. Verify customer exists
            cursor.execute("SELECT CustomerID, FullName FROM Customers WHERE CustomerID = %s;", (customer_id,))
            customer = cursor.fetchone()
            if not customer:
                return error_response(f"Customer with ID {customer_id} does not exist.", 404)

            # 2. Check Book availability with FOR UPDATE row-level lock
            cursor.execute(
                "SELECT BookID, Title, Price, StockQuantity FROM Books WHERE BookID = %s FOR UPDATE;",
                (book_id,)
            )
            book = cursor.fetchone()
            if not book:
                return error_response(f"Book with ID {book_id} does not exist.", 404)

            current_stock = book["StockQuantity"]
            if current_stock < quantity:
                return error_response(
                    f"Insufficient stock for '{book['Title']}'. "
                    f"Requested: {quantity}, Available in stock: {current_stock}."
                )

            # 3. Calculate total amount
            unit_price = float(book["Price"])
            total_amount = round(unit_price * quantity, 2)

            # 4. Deduct stock quantity
            cursor.execute(
                "UPDATE Books SET StockQuantity = StockQuantity - %s WHERE BookID = %s;",
                (quantity, book_id)
            )

            # 5. Insert Order
            cursor.execute(
                """
                INSERT INTO Orders (CustomerID, BookID, QuantityOrdered, TotalAmount)
                VALUES (%s, %s, %s, %s);
                """,
                (customer_id, book_id, quantity, total_amount)
            )
            order_id = cursor.lastrowid

            return serialize_response({
                "success": True,
                "message": f"Order #{order_id} placed successfully for '{customer['FullName']}'!",
                "order": {
                    "OrderID": order_id,
                    "CustomerName": customer["FullName"],
                    "BookTitle": book["Title"],
                    "QuantityOrdered": quantity,
                    "UnitPrice": unit_price,
                    "TotalAmount": total_amount,
                    "RemainingStock": current_stock - quantity
                }
            }, 201)
    except Exception as e:
        return error_response("Transaction failed while placing order", 500, str(e))

# ---------------------------------------------------------------------
# Analytics & Reports API Endpoints
# ---------------------------------------------------------------------
@app.route("/api/analytics", methods=["GET"])
def get_analytics():
    """
    Returns aggregate statistics for the dashboard:
      - Total Book Titles & Inventory Count
      - Total Revenue
      - Total Orders Placed
      - Total Registered Customers
      - Top Selling Books
      - Low Stock Alert List
    """
    try:
        with get_db_cursor() as (cursor, _):
            # Inventory & Book count
            cursor.execute("""
                SELECT 
                    COUNT(BookID) AS TotalTitles,
                    COALESCE(SUM(StockQuantity), 0) AS TotalInventory
                FROM Books;
            """)
            book_stats = cursor.fetchone()

            # Customer count
            cursor.execute("SELECT COUNT(CustomerID) AS TotalCustomers FROM Customers;")
            customer_stats = cursor.fetchone()

            # Orders & Revenue stats
            cursor.execute("""
                SELECT 
                    COUNT(OrderID) AS TotalOrders,
                    COALESCE(SUM(TotalAmount), 0.00) AS TotalRevenue,
                    COALESCE(SUM(QuantityOrdered), 0) AS TotalUnitsSold
                FROM Orders;
            """)
            order_stats = cursor.fetchone()

            # Top 5 Selling Books
            cursor.execute("""
                SELECT 
                    b.BookID,
                    b.Title,
                    a.AuthorName,
                    COALESCE(SUM(o.QuantityOrdered), 0) AS UnitsSold,
                    COALESCE(SUM(o.TotalAmount), 0.00) AS Revenue
                FROM Books b
                JOIN Authors a ON b.AuthorID = a.AuthorID
                JOIN Orders o ON b.BookID = o.BookID
                GROUP BY b.BookID, b.Title, a.AuthorName
                ORDER BY UnitsSold DESC
                LIMIT 5;
            """)
            top_selling = cursor.fetchall()

            # Low Stock Books (StockQuantity < 5)
            cursor.execute("""
                SELECT 
                    b.BookID, 
                    b.Title, 
                    a.AuthorName, 
                    b.StockQuantity, 
                    b.Price
                FROM Books b
                JOIN Authors a ON b.AuthorID = a.AuthorID
                WHERE b.StockQuantity < 5
                ORDER BY b.StockQuantity ASC;
            """)
            low_stock = cursor.fetchall()

            # Recent 5 Orders
            cursor.execute("""
                SELECT 
                    o.OrderID,
                    o.OrderDate,
                    c.FullName AS CustomerName,
                    b.Title AS BookTitle,
                    o.QuantityOrdered,
                    o.TotalAmount
                FROM Orders o
                JOIN Customers c ON o.CustomerID = c.CustomerID
                JOIN Books b ON o.BookID = b.BookID
                ORDER BY o.OrderID DESC
                LIMIT 5;
            """)
            recent_orders = cursor.fetchall()

            return serialize_response({
                "success": True,
                "summary": {
                    "total_titles": book_stats["TotalTitles"],
                    "total_inventory": book_stats["TotalInventory"],
                    "total_customers": customer_stats["TotalCustomers"],
                    "total_orders": order_stats["TotalOrders"],
                    "total_revenue": order_stats["TotalRevenue"],
                    "total_units_sold": order_stats["TotalUnitsSold"]
                },
                "top_selling": top_selling,
                "low_stock": low_stock,
                "recent_orders": recent_orders
            })
    except Exception as e:
        return error_response("Failed to generate analytics", 500, str(e))

@app.route("/api/reports/customer-summary", methods=["GET"])
def get_customer_summary_view():
    """
    Directly queries the RDBMS View `CustomerOrderSummary`
    demonstrating view usage for academic project evaluation.
    """
    try:
        with get_db_cursor() as (cursor, _):
            cursor.execute("SELECT * FROM CustomerOrderSummary ORDER BY TotalSpent DESC;")
            records = cursor.fetchall()
            return serialize_response({
                "success": True,
                "view_name": "CustomerOrderSummary",
                "count": len(records),
                "data": records
            })
    except Exception as e:
        return error_response("Failed to query CustomerOrderSummary view", 500, str(e))

# ---------------------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print(" 📖 Online Bookstore Management System (Flask + MySQL 8.0)")
    print(f" Server starting at: http://127.0.0.1:{Config.FLASK_PORT}")
    print(" Press CTRL+C to stop.")
    print("=" * 60)
    app.run(host="127.0.0.1", port=Config.FLASK_PORT, debug=Config.FLASK_DEBUG)
