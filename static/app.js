/**
 * BookHaven — Online Bookstore Management System
 * Vanilla JavaScript Single-Page Application Client
 */

// Global State
let allAuthors = [];
let allBooks = [];
let allCustomers = [];
let searchDebounceTimer = null;

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  setupNavigation();
  checkDatabaseStatus();
  loadDashboardData();
});

// =====================================================================
// Navigation & Tabs
// =====================================================================
function setupNavigation() {
  const navButtons = document.querySelectorAll(".nav-item");
  navButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const tabId = btn.getAttribute("data-tab");
      switchTab(tabId);
    });
  });
}

function switchTab(tabId) {
  // Update nav buttons
  document.querySelectorAll(".nav-item").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-tab") === tabId);
  });

  // Update tab content sections
  document.querySelectorAll(".tab-content").forEach(section => {
    section.classList.toggle("active", section.id === `tab-${tabId}`);
  });

  // Update header text
  const heading = document.getElementById("page-heading");
  const subheading = document.getElementById("page-subheading");

  switch (tabId) {
    case "dashboard":
      heading.textContent = "Dashboard Overview";
      subheading.textContent = "Real-time inventory statistics and store performance";
      loadDashboardData();
      break;
    case "books":
      heading.textContent = "Books Inventory";
      subheading.textContent = "Manage books, authors, stock quantities, and prices";
      loadBooks();
      break;
    case "orders":
      heading.textContent = "Orders Management";
      subheading.textContent = "Track sales history, customer orders, and transaction totals";
      loadOrders();
      break;
    case "customers":
      heading.textContent = "Customer Directory";
      subheading.textContent = "Registered customers, contact details, and order history";
      loadCustomers();
      break;
    case "rdbms-views":
      heading.textContent = "RDBMS Views & Queries";
      subheading.textContent = "Demonstration of MySQL 8.0 Views, Joins, and Aggregates";
      loadCustomerSummaryView();
      break;
  }
}

// =====================================================================
// Database Health Check
// =====================================================================
async function checkDatabaseStatus() {
  const indicator = document.getElementById("status-indicator");
  const title = document.getElementById("status-title");
  const sub = document.getElementById("status-sub");
  const banner = document.getElementById("db-alert-banner");
  const bannerText = document.getElementById("db-alert-text");

  try {
    const res = await fetch("/api/health");
    const data = await res.json();

    if (res.ok && data.connected) {
      if (data.missing_tables && data.missing_tables.length > 0) {
        indicator.className = "status-indicator offline";
        title.textContent = "Schema Missing";
        sub.textContent = "Run init_db.sql";
        banner.style.display = "flex";
        bannerText.textContent = data.message;
      } else {
        indicator.className = "status-indicator online";
        title.textContent = "Connected: BookstoreDB";
        sub.textContent = `MySQL ${data.server_version || "8.0"}`;
        banner.style.display = "none";
      }
    } else {
      indicator.className = "status-indicator offline";
      title.textContent = "DB Disconnected";
      sub.textContent = "Check .env config";
      banner.style.display = "flex";
      bannerText.textContent = data.message || "Failed to connect to MySQL database.";
    }
  } catch (err) {
    indicator.className = "status-indicator offline";
    title.textContent = "Server Offline";
    sub.textContent = "Flask unreachable";
    banner.style.display = "flex";
    bannerText.textContent = "Cannot reach Flask backend at http://127.0.0.1:5000.";
  }
}

// =====================================================================
// Dashboard Data Loader
// =====================================================================
async function loadDashboardData() {
  try {
    const res = await fetch("/api/analytics");
    if (!res.ok) throw new Error("Failed to load analytics");
    const data = await res.json();

    // Summary counters
    const s = data.summary;
    document.getElementById("stat-total-inventory").textContent = s.total_inventory.toLocaleString();
    document.getElementById("stat-total-titles").textContent = `${s.total_titles} titles`;
    document.getElementById("stat-total-revenue").textContent = formatCurrency(s.total_revenue);
    document.getElementById("stat-total-orders").textContent = s.total_orders.toLocaleString();
    document.getElementById("stat-units-sold").textContent = `${s.total_units_sold} items`;
    document.getElementById("stat-total-customers").textContent = s.total_customers.toLocaleString();

    // Low stock alerts
    const lowStockContainer = document.getElementById("low-stock-container");
    const lowStockTable = document.querySelector("#table-low-stock tbody");
    const lowStockCount = document.getElementById("low-stock-count");

    if (data.low_stock && data.low_stock.length > 0) {
      lowStockContainer.style.display = "block";
      lowStockCount.textContent = `${data.low_stock.length} item(s) low`;
      lowStockTable.innerHTML = data.low_stock.map(b => `
        <tr>
          <td><strong>${escapeHtml(b.Title)}</strong></td>
          <td>${escapeHtml(b.AuthorName)}</td>
          <td><span class="badge ${b.StockQuantity === 0 ? 'badge-out-stock' : 'badge-low-stock'}">${b.StockQuantity} left</span></td>
          <td>${formatCurrency(b.Price)}</td>
          <td>
            <button class="btn btn-sm btn-outline" onclick="openEditBookModalById(${b.BookID})">Restock</button>
          </td>
        </tr>
      `).join("");
    } else {
      lowStockContainer.style.display = "none";
    }

    // Top Selling Books
    const topBody = document.getElementById("top-selling-body");
    if (data.top_selling && data.top_selling.length > 0) {
      topBody.innerHTML = data.top_selling.map(b => `
        <tr>
          <td><strong>${escapeHtml(b.Title)}</strong></td>
          <td>${escapeHtml(b.AuthorName)}</td>
          <td><span class="badge badge-success">${b.UnitsSold} sold</span></td>
          <td>${formatCurrency(b.Revenue)}</td>
        </tr>
      `).join("");
    } else {
      topBody.innerHTML = `<tr><td colspan="4" class="text-center text-muted">No sales data yet.</td></tr>`;
    }

    // Recent Orders
    const recentBody = document.getElementById("recent-orders-body");
    if (data.recent_orders && data.recent_orders.length > 0) {
      recentBody.innerHTML = data.recent_orders.map(o => `
        <tr>
          <td>#${o.OrderID}</td>
          <td><strong>${escapeHtml(o.CustomerName)}</strong></td>
          <td>${escapeHtml(o.BookTitle)}</td>
          <td>${o.QuantityOrdered}</td>
          <td><strong>${formatCurrency(o.TotalAmount)}</strong></td>
        </tr>
      `).join("");
    } else {
      recentBody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">No recent orders found.</td></tr>`;
    }
  } catch (err) {
    console.error("Dashboard error:", err);
  }
}

// =====================================================================
// Books Management
// =====================================================================
async function loadBooks(searchTerm = "") {
  const tbody = document.getElementById("books-table-body");
  tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">Loading books...</td></tr>`;

  try {
    const url = searchTerm ? `/api/books?q=${encodeURIComponent(searchTerm)}` : "/api/books";
    const res = await fetch(url);
    const data = await res.json();

    if (!data.success) throw new Error(data.error);

    allBooks = data.books;

    if (allBooks.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No books found matching criteria.</td></tr>`;
      return;
    }

    tbody.innerHTML = allBooks.map(b => {
      let statusBadge = "";
      if (b.StockQuantity === 0) {
        statusBadge = `<span class="badge badge-out-stock">Out of Stock</span>`;
      } else if (b.StockQuantity < 5) {
        statusBadge = `<span class="badge badge-low-stock">Low Stock (${b.StockQuantity})</span>`;
      } else {
        statusBadge = `<span class="badge badge-in-stock">In Stock (${b.StockQuantity})</span>`;
      }

      return `
        <tr>
          <td><strong>#${b.BookID}</strong></td>
          <td>
            <strong>${escapeHtml(b.Title)}</strong>
          </td>
          <td>
            ${escapeHtml(b.AuthorName)}
            <span class="subtext">(${escapeHtml(b.AuthorCountry)})</span>
          </td>
          <td><strong>${formatCurrency(b.Price)}</strong></td>
          <td>${b.StockQuantity}</td>
          <td>${statusBadge}</td>
          <td style="text-align: right;">
            <button class="btn btn-sm btn-outline" onclick="openEditBookModalById(${b.BookID})">Edit</button>
            <button class="btn btn-sm btn-danger-outline" onclick="deleteBook(${b.BookID}, '${escapeHtml(b.Title)}')">Delete</button>
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger">${err.message}</td></tr>`;
  }
}

function handleBookSearch() {
  clearTimeout(searchDebounceTimer);
  searchDebounceTimer = setTimeout(() => {
    const term = document.getElementById("books-search-input").value.trim();
    loadBooks(term);
  }, 300);
}

// Add Book Modal & Logic
async function openAddBookModal() {
  await loadAuthorsDropdown("book-author");
  document.getElementById("form-add-book").reset();
  document.getElementById("quick-author-box").style.display = "none";
  openModal("modal-add-book");
}

function toggleQuickAuthorForm(e) {
  e.preventDefault();
  const box = document.getElementById("quick-author-box");
  box.style.display = box.style.display === "none" ? "flex" : "none";
}

async function handleQuickAuthorSubmit() {
  const name = document.getElementById("quick-author-name").value.trim();
  const country = document.getElementById("quick-author-country").value.trim();

  if (!name || !country) {
    showToast("Please enter author name and country.", "warning");
    return;
  }

  try {
    const res = await fetch("/api/authors", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ AuthorName: name, Country: country })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);

    showToast(data.message, "success");
    await loadAuthorsDropdown("book-author");
    document.getElementById("book-author").value = data.AuthorID;
    document.getElementById("quick-author-box").style.display = "none";
    document.getElementById("quick-author-name").value = "";
    document.getElementById("quick-author-country").value = "";
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function handleAddBook(e) {
  e.preventDefault();
  const title = document.getElementById("book-title").value.trim();
  const authorId = document.getElementById("book-author").value;
  const price = document.getElementById("book-price").value;
  const stock = document.getElementById("book-stock").value;

  try {
    const res = await fetch("/api/books", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        Title: title,
        AuthorID: parseInt(authorId),
        Price: parseFloat(price),
        StockQuantity: parseInt(stock)
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);

    showToast(data.message, "success");
    closeModal("modal-add-book");
    loadBooks();
    loadDashboardData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Edit Book Modal & Logic
async function openEditBookModalById(bookId) {
  const book = allBooks.find(b => b.BookID === bookId);
  if (!book) {
    const res = await fetch(`/api/books?q=${bookId}`);
    const data = await res.json();
    if (data.books && data.books.length > 0) {
      populateAndOpenEditModal(data.books[0]);
    } else {
      showToast("Book not found", "error");
    }
    return;
  }
  populateAndOpenEditModal(book);
}

async function populateAndOpenEditModal(book) {
  await loadAuthorsDropdown("edit-book-author");
  document.getElementById("edit-book-id").value = book.BookID;
  document.getElementById("edit-book-title").value = book.Title;
  document.getElementById("edit-book-author").value = book.AuthorID;
  document.getElementById("edit-book-price").value = book.Price;
  document.getElementById("edit-book-stock").value = book.StockQuantity;
  openModal("modal-edit-book");
}

async function handleEditBook(e) {
  e.preventDefault();
  const bookId = document.getElementById("edit-book-id").value;
  const title = document.getElementById("edit-book-title").value.trim();
  const authorId = document.getElementById("edit-book-author").value;
  const price = document.getElementById("edit-book-price").value;
  const stock = document.getElementById("edit-book-stock").value;

  try {
    const res = await fetch(`/api/books/${bookId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        Title: title,
        AuthorID: parseInt(authorId),
        Price: parseFloat(price),
        StockQuantity: parseInt(stock)
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);

    showToast(data.message, "success");
    closeModal("modal-edit-book");
    loadBooks();
    loadDashboardData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Delete Book
async function deleteBook(bookId, title) {
  if (!confirm(`Are you sure you want to delete book "${title}" (ID #${bookId})?`)) {
    return;
  }

  try {
    const res = await fetch(`/api/books/${bookId}`, { method: "DELETE" });
    const data = await res.json();

    if (!res.ok) {
      // Handles Foreign Key Restrict message gracefully
      alert(data.error || "Cannot delete this book.");
      return;
    }

    showToast(data.message, "success");
    loadBooks();
    loadDashboardData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// =====================================================================
// Orders Management & Placement
// =====================================================================
async function loadOrders() {
  const tbody = document.getElementById("orders-table-body");
  tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">Loading orders...</td></tr>`;

  try {
    const res = await fetch("/api/orders");
    const data = await res.json();
    if (!data.success) throw new Error(data.error);

    const orders = data.orders;
    if (orders.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">No orders found. Place your first order!</td></tr>`;
      return;
    }

    tbody.innerHTML = orders.map(o => `
      <tr>
        <td><strong>#${o.OrderID}</strong></td>
        <td>${formatDateTime(o.OrderDate)}</td>
        <td>
          <strong>${escapeHtml(o.CustomerName)}</strong>
          <div class="subtext">${escapeHtml(o.CustomerEmail)}</div>
        </td>
        <td>${escapeHtml(o.BookTitle)}</td>
        <td>${escapeHtml(o.AuthorName)}</td>
        <td><span class="badge badge-success">${o.QuantityOrdered}</span></td>
        <td>${formatCurrency(o.UnitPrice)}</td>
        <td><strong>${formatCurrency(o.TotalAmount)}</strong></td>
      </tr>
    `).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">${err.message}</td></tr>`;
  }
}

async function openPlaceOrderModal() {
  document.getElementById("form-place-order").reset();
  document.getElementById("order-qty").value = 1;

  // Load customer and book dropdowns
  await loadCustomersDropdown();
  await loadBooksDropdownForOrders();

  updateOrderPreview();
  openModal("modal-place-order");
}

function updateOrderPreview() {
  const bookSelect = document.getElementById("order-book");
  const qtyInput = document.getElementById("order-qty");
  const selectedOption = bookSelect.options[bookSelect.selectedIndex];

  const unitPriceEl = document.getElementById("order-unit-price");
  const totalPriceEl = document.getElementById("order-total-price");
  const stockDisplay = document.getElementById("order-stock-display");
  const submitBtn = document.getElementById("btn-submit-order");

  if (!selectedOption || !selectedOption.value) {
    unitPriceEl.textContent = "$0.00";
    totalPriceEl.textContent = "$0.00";
    stockDisplay.textContent = "--";
    stockDisplay.className = "stock-pill";
    submitBtn.disabled = false;
    return;
  }

  const price = parseFloat(selectedOption.getAttribute("data-price") || 0);
  const stock = parseInt(selectedOption.getAttribute("data-stock") || 0);
  const qty = parseInt(qtyInput.value || 1);

  unitPriceEl.textContent = formatCurrency(price);
  stockDisplay.textContent = `${stock} available`;

  if (stock === 0) {
    stockDisplay.className = "stock-pill badge-out-stock";
    submitBtn.disabled = true;
  } else if (stock < qty) {
    stockDisplay.className = "stock-pill badge-warning";
    submitBtn.disabled = true;
  } else {
    stockDisplay.className = "stock-pill badge-in-stock";
    submitBtn.disabled = false;
  }

  const total = Math.max(0, price * qty);
  totalPriceEl.textContent = formatCurrency(total);
}

async function handlePlaceOrder(e) {
  e.preventDefault();
  const customerId = document.getElementById("order-customer").value;
  const bookId = document.getElementById("order-book").value;
  const quantity = document.getElementById("order-qty").value;

  try {
    const res = await fetch("/api/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        CustomerID: parseInt(customerId),
        BookID: parseInt(bookId),
        QuantityOrdered: parseInt(quantity)
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);

    showToast(data.message, "success");
    closeModal("modal-place-order");
    loadOrders();
    loadDashboardData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// =====================================================================
// Customers Management
// =====================================================================
async function loadCustomers() {
  const tbody = document.getElementById("customers-table-body");
  tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">Loading customers...</td></tr>`;

  try {
    const res = await fetch("/api/customers");
    const data = await res.json();
    if (!data.success) throw new Error(data.error);

    allCustomers = data.customers;
    if (allCustomers.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No customers registered yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = allCustomers.map(c => `
      <tr>
        <td><strong>#${c.CustomerID}</strong></td>
        <td><strong>${escapeHtml(c.FullName)}</strong></td>
        <td>${escapeHtml(c.Email)}</td>
        <td>${escapeHtml(c.Phone)}</td>
        <td>${escapeHtml(c.City)}</td>
        <td><span class="badge ${c.OrderCount > 0 ? 'badge-success' : 'badge-warning'}">${c.OrderCount} order(s)</span></td>
        <td style="text-align: right;">
          <button class="btn btn-sm btn-danger-outline" onclick="deleteCustomer(${c.CustomerID}, '${escapeHtml(c.FullName)}')">Delete</button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger">${err.message}</td></tr>`;
  }
}

async function handleAddCustomer(e) {
  e.preventDefault();
  const name = document.getElementById("cust-name").value.trim();
  const email = document.getElementById("cust-email").value.trim();
  const phone = document.getElementById("cust-phone").value.trim();
  const city = document.getElementById("cust-city").value.trim();

  try {
    const res = await fetch("/api/customers", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ FullName: name, Email: email, Phone: phone, City: city })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);

    showToast(data.message, "success");
    closeModal("modal-add-customer");
    document.getElementById("form-add-customer").reset();
    loadCustomers();
    loadDashboardData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function deleteCustomer(customerId, name) {
  if (!confirm(`Are you sure you want to delete customer "${name}"?\nNote: By CASCADE rule, all their order history will also be removed.`)) {
    return;
  }

  try {
    const res = await fetch(`/api/customers/${customerId}`, { method: "DELETE" });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);

    showToast(data.message, "success");
    loadCustomers();
    loadDashboardData();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// =====================================================================
// RDBMS Views & SQL Query Viewer
// =====================================================================
async function loadCustomerSummaryView() {
  const tbody = document.getElementById("view-summary-body");
  tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">Querying MySQL View 'CustomerOrderSummary'...</td></tr>`;

  try {
    const res = await fetch("/api/reports/customer-summary");
    const data = await res.json();
    if (!data.success) throw new Error(data.error);

    if (data.data.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">No data in view.</td></tr>`;
      return;
    }

    tbody.innerHTML = data.data.map(r => `
      <tr>
        <td><strong>#${r.CustomerID}</strong></td>
        <td><strong>${escapeHtml(r.FullName)}</strong></td>
        <td>${escapeHtml(r.Email)}</td>
        <td>${escapeHtml(r.City)}</td>
        <td><span class="badge ${r.TotalOrders > 0 ? 'badge-success' : 'badge-warning'}">${r.TotalOrders}</span></td>
        <td>${r.TotalBooksPurchased}</td>
        <td><strong>${formatCurrency(r.TotalSpent)}</strong></td>
        <td>${formatCurrency(r.AverageOrderValue)}</td>
      </tr>
    `).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">${err.message}</td></tr>`;
  }
}

// =====================================================================
// Dropdown Helpers
// =====================================================================
async function loadAuthorsDropdown(selectId) {
  const select = document.getElementById(selectId);
  try {
    const res = await fetch("/api/authors");
    const data = await res.json();
    if (data.success) {
      allAuthors = data.authors;
      select.innerHTML = `<option value="">Select an Author...</option>` +
        allAuthors.map(a => `<option value="${a.AuthorID}">${escapeHtml(a.AuthorName)} (${escapeHtml(a.Country)})</option>`).join("");
    }
  } catch (err) {
    console.error("Failed to load authors:", err);
  }
}

async function loadCustomersDropdown() {
  const select = document.getElementById("order-customer");
  try {
    const res = await fetch("/api/customers");
    const data = await res.json();
    if (data.success) {
      select.innerHTML = `<option value="">Select Customer...</option>` +
        data.customers.map(c => `<option value="${c.CustomerID}">${escapeHtml(c.FullName)} (${escapeHtml(c.City)})</option>`).join("");
    }
  } catch (err) {
    console.error("Failed to load customers:", err);
  }
}

async function loadBooksDropdownForOrders() {
  const select = document.getElementById("order-book");
  try {
    const res = await fetch("/api/books");
    const data = await res.json();
    if (data.success) {
      select.innerHTML = `<option value="">Select Book...</option>` +
        data.books.map(b => {
          const stockLabel = b.StockQuantity === 0 ? "Out of Stock" : `${b.StockQuantity} in stock`;
          return `<option value="${b.BookID}" data-price="${b.Price}" data-stock="${b.StockQuantity}">${escapeHtml(b.Title)} — ${formatCurrency(b.Price)} [${stockLabel}]</option>`;
        }).join("");
    }
  } catch (err) {
    console.error("Failed to load books:", err);
  }
}

// =====================================================================
// Modal Controls
// =====================================================================
function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add("active");
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("active");
}

// Close modal when clicking on backdrop
window.addEventListener("click", (e) => {
  if (e.target.classList.contains("modal-backdrop")) {
    e.target.classList.remove("active");
  }
});

// Close modal on Escape key
window.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    document.querySelectorAll(".modal-backdrop.active").forEach(m => m.classList.remove("active"));
  }
});

// =====================================================================
// Toast Notifications
// =====================================================================
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;

  const iconMap = {
    success: "✅",
    error: "❌",
    warning: "⚠️",
    info: "ℹ️"
  };

  toast.innerHTML = `
    <span>${iconMap[type] || "ℹ️"}</span>
    <span style="flex:1;">${escapeHtml(message)}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// =====================================================================
// Utilities
// =====================================================================
function formatCurrency(val) {
  const num = parseFloat(val) || 0;
  return "$" + num.toFixed(2);
}

function formatDateTime(val) {
  if (!val) return "--";
  const d = new Date(val);
  if (isNaN(d.getTime())) return val;
  return d.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
