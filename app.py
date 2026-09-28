"""
app.py
------
Main Flask application for CodeAlpha_RestaurantManagement.

This file contains:
    - App configuration (SQLite database setup)
    - All routes for Menu, Tables, Reservations, Orders, Inventory, Dashboard
    - Simple server-side business logic (double-booking prevention,
      automatic stock reduction on order placement, low stock alerts)

Run with:
    pip install -r requirements.txt
    python app.py

Then open:
    http://127.0.0.1:5000
"""

import math
import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy.exc import SQLAlchemyError

from models import (
    db,
    MenuItem,
    RestaurantTable,
    Reservation,
    Order,
    OrderItem,
    Inventory,
)

# ---------------------------------------------------------------------------
# APP CONFIGURATION
# ---------------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "database.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "codealpha-restaurant-secret-key"  # needed for flash messages

db.init_app(app)


def commit_changes(error_message):
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception("Database transaction failed")
        flash(error_message, "error")
        return False
    return True


# ---------------------------------------------------------------------------
# HOME PAGE
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    """Landing page with quick links to every module."""
    return render_template("index.html")


# ---------------------------------------------------------------------------
# 1. MENU MANAGEMENT
# ---------------------------------------------------------------------------
@app.route("/menu")
def menu():
    """Show all menu items, grouped implicitly by category in the template."""
    items = MenuItem.query.order_by(MenuItem.category, MenuItem.name).all()
    return render_template("menu.html", items=items)


@app.route("/menu/add", methods=["GET", "POST"])
def add_menu():
    """Add a brand new menu item."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        price = request.form.get("price", "0")
        quantity = request.form.get("quantity", "0")

        if not name or not category:
            flash("Item name and category are required.", "error")
            return redirect(url_for("add_menu"))

        try:
            price_value = float(price)
            quantity_value = int(quantity)
        except (TypeError, ValueError):
            flash("Price and quantity must be valid numbers.", "error")
            return redirect(url_for("add_menu"))
        if not math.isfinite(price_value) or price_value < 0 or quantity_value < 0:
            flash("Price and quantity cannot be negative.", "error")
            return redirect(url_for("add_menu"))

        new_item = MenuItem(
            name=name,
            category=category,
            price=price_value,
            quantity=quantity_value,
        )
        db.session.add(new_item)
        if not commit_changes("Could not save the menu item. Please try again."):
            return redirect(url_for("add_menu"))
        flash(f'Menu item "{name}" added successfully!', "success")
        return redirect(url_for("menu"))

    return render_template("add_menu.html", item=None)


@app.route("/menu/edit/<int:id>", methods=["GET", "POST"])
def edit_menu(id):
    """Edit an existing menu item."""
    item = MenuItem.query.get_or_404(id)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        try:
            price = float(request.form.get("price", ""))
            quantity = int(request.form.get("quantity", ""))
        except (TypeError, ValueError):
            flash("Price and quantity must be valid numbers.", "error")
            return redirect(url_for("edit_menu", id=item.id))
        if not name or not category or not math.isfinite(price) or price < 0 or quantity < 0:
            flash("Enter a name, category, and non-negative price and quantity.", "error")
            return redirect(url_for("edit_menu", id=item.id))
        item.name = name
        item.category = category
        item.price = price
        item.quantity = quantity
        if not commit_changes("Could not update the menu item. Please try again."):
            return redirect(url_for("edit_menu", id=item.id))
        flash(f'Menu item "{item.name}" updated successfully!', "success")
        return redirect(url_for("menu"))

    return render_template("add_menu.html", item=item)


@app.route("/menu/delete/<int:id>", methods=["POST"])
def delete_menu(id):
    """Delete a menu item."""
    item = MenuItem.query.get_or_404(id)
    if item.order_items:
        flash("This menu item is used by existing orders and cannot be deleted.", "error")
        return redirect(url_for("menu"))
    db.session.delete(item)
    if not commit_changes("Could not delete the menu item. Please try again."):
        return redirect(url_for("menu"))
    flash(f'Menu item "{item.name}" deleted.', "success")
    return redirect(url_for("menu"))


# ---------------------------------------------------------------------------
# 2. TABLE MANAGEMENT
# ---------------------------------------------------------------------------
@app.route("/tables")
def tables():
    """Show all restaurant tables and their current status."""
    all_tables = RestaurantTable.query.order_by(RestaurantTable.table_number).all()
    return render_template("tables.html", tables=all_tables)


@app.route("/tables/add", methods=["GET", "POST"])
def add_table():
    """Add a new restaurant table."""
    if request.method == "POST":
        try:
            table_number = int(request.form.get("table_number", ""))
            capacity = int(request.form.get("capacity", ""))
        except (TypeError, ValueError):
            flash("Table number and capacity must be positive whole numbers.", "error")
            return redirect(url_for("add_table"))
        if table_number < 1 or capacity < 1:
            flash("Table number and capacity must be positive whole numbers.", "error")
            return redirect(url_for("add_table"))

        existing = RestaurantTable.query.filter_by(table_number=table_number).first()
        if existing:
            flash(f"Table number {table_number} already exists.", "error")
            return redirect(url_for("add_table"))

        new_table = RestaurantTable(
            table_number=table_number,
            capacity=capacity,
            status="Available",
        )
        db.session.add(new_table)
        if not commit_changes("Could not add the table. Please try again."):
            return redirect(url_for("add_table"))
        flash(f"Table {table_number} added successfully!", "success")
        return redirect(url_for("tables"))

    return render_template("add_table.html")


@app.route("/tables/edit/<int:id>", methods=["GET", "POST"])
def edit_table(id):
    table = RestaurantTable.query.get_or_404(id)

    if request.method == "POST":
        try:
            table_number = int(request.form.get("table_number", ""))
            capacity = int(request.form.get("capacity", ""))
        except ValueError:
            flash("Table number and capacity must be positive whole numbers.", "error")
            return redirect(url_for("edit_table", id=table.id))

        if table_number < 1 or capacity < 1:
            flash("Table number and capacity must be positive whole numbers.", "error")
            return redirect(url_for("edit_table", id=table.id))

        duplicate = RestaurantTable.query.filter(
            RestaurantTable.table_number == table_number,
            RestaurantTable.id != table.id,
        ).first()
        if duplicate:
            flash(f"Table number {table_number} already exists.", "error")
            return redirect(url_for("edit_table", id=table.id))

        if any(reservation.guests > capacity for reservation in table.reservations):
            flash("Capacity cannot be lower than an existing reservation's guest count.", "error")
            return redirect(url_for("edit_table", id=table.id))

        table.table_number = table_number
        table.capacity = capacity
        if not commit_changes("Could not update the table. Please try again."):
            return redirect(url_for("edit_table", id=table.id))
        flash(f"Table {table_number} updated successfully!", "success")
        return redirect(url_for("tables"))

    return render_template("add_table.html", table=table)


@app.route("/tables/status/<int:id>", methods=["POST"])
def update_table_status(id):
    """Update a table's status (Available / Reserved / Occupied)."""
    table = RestaurantTable.query.get_or_404(id)
    new_status = request.form.get("status")
    if new_status in ("Available", "Reserved", "Occupied"):
        table.status = new_status
        if not commit_changes("Could not update the table status. Please try again."):
            return redirect(url_for("tables"))
        flash(f"Table {table.table_number} marked as {new_status}.", "success")
    else:
        flash("Choose a valid table status.", "error")
    return redirect(url_for("tables"))


@app.route("/tables/delete/<int:id>", methods=["POST"])
def delete_table(id):
    table = RestaurantTable.query.get_or_404(id)
    if table.reservations:
        flash("This table has reservations and cannot be deleted.", "error")
        return redirect(url_for("tables"))

    table_number = table.table_number
    db.session.delete(table)
    if not commit_changes("Could not delete the table. Please try again."):
        return redirect(url_for("tables"))
    flash(f"Table {table_number} deleted.", "success")
    return redirect(url_for("tables"))


# ---------------------------------------------------------------------------
# 3. RESERVATION SYSTEM
# ---------------------------------------------------------------------------
@app.route("/reservations")
def reservations():
    """Show all reservations."""
    all_reservations = Reservation.query.order_by(
        Reservation.date, Reservation.time
    ).all()
    return render_template("reservations.html", reservations=all_reservations)


@app.route("/reserve", methods=["GET", "POST"])
def reserve():
    """
    Reserve a table for a customer.

    Business rule: a table cannot be double booked for the SAME date + time.
    """
    available_tables = RestaurantTable.query.filter(
        RestaurantTable.status != "Occupied"
    ).order_by(RestaurantTable.table_number).all()

    if request.method == "POST":
        customer_name = request.form.get("customer_name", "").strip()
        phone = request.form.get("phone", "").strip()
        date = request.form.get("date")
        time = request.form.get("time")
        guests = request.form.get("guests", "1")
        table_id = request.form.get("table_id")

        if not all([customer_name, phone, date, time, table_id]):
            flash("Please fill in all reservation fields.", "error")
            return redirect(url_for("reserve"))

        try:
            guests = int(guests)
            table_id = int(table_id)
        except (TypeError, ValueError):
            flash("Guests and table must be valid whole numbers.", "error")
            return redirect(url_for("reserve"))

        table = db.session.get(RestaurantTable, table_id)
        if not table or table.status == "Occupied":
            flash("Please choose an available table.", "error")
            return redirect(url_for("reserve"))
        if guests < 1 or guests > table.capacity:
            flash("Guest count must fit the selected table's capacity.", "error")
            return redirect(url_for("reserve"))
        try:
            datetime.strptime(date, "%Y-%m-%d")
            datetime.strptime(time, "%H:%M")
        except (TypeError, ValueError):
            flash("Enter a valid reservation date and time.", "error")
            return redirect(url_for("reserve"))

        # ---- Check availability: prevent double booking ----
        clash = Reservation.query.filter_by(
            table_id=table_id, date=date, time=time
        ).first()

        if clash:
            flash(
                "This table is already reserved for the selected date and time. "
                "Please choose a different table, date, or time.",
                "error",
            )
            return redirect(url_for("reserve"))

        new_reservation = Reservation(
            customer_name=customer_name,
            phone=phone,
            date=date,
            time=time,
            guests=guests,
            table_id=table_id,
        )
        db.session.add(new_reservation)

        # Mark the table as reserved
        table.status = "Reserved"

        if not commit_changes("Could not save the reservation. Please try again."):
            return redirect(url_for("reserve"))
        flash("Table reserved successfully!", "success")
        return redirect(url_for("reservations"))

    return render_template("reserve.html", tables=available_tables)


@app.route("/reservations/edit/<int:id>", methods=["GET", "POST"])
def edit_reservation(id):
    reservation = Reservation.query.get_or_404(id)
    available_tables = RestaurantTable.query.filter(
        (RestaurantTable.status != "Occupied")
        | (RestaurantTable.id == reservation.table_id)
    ).order_by(RestaurantTable.table_number).all()

    if request.method == "POST":
        customer_name = request.form.get("customer_name", "").strip()
        phone = request.form.get("phone", "").strip()
        date = request.form.get("date", "")
        time = request.form.get("time", "")
        try:
            guests = int(request.form.get("guests", ""))
            table_id = int(request.form.get("table_id", ""))
        except ValueError:
            flash("Guests and table must be valid positive numbers.", "error")
            return redirect(url_for("edit_reservation", id=reservation.id))

        table = db.session.get(RestaurantTable, table_id)
        if not all([customer_name, phone, date, time]) or guests < 1 or not table:
            flash("Please provide valid reservation details.", "error")
            return redirect(url_for("edit_reservation", id=reservation.id))
        try:
            datetime.strptime(date, "%Y-%m-%d")
            datetime.strptime(time, "%H:%M")
        except ValueError:
            flash("Enter a valid reservation date and time.", "error")
            return redirect(url_for("edit_reservation", id=reservation.id))
        if table.status == "Occupied" and table.id != reservation.table_id:
            flash("The selected table is occupied.", "error")
            return redirect(url_for("edit_reservation", id=reservation.id))
        if guests > table.capacity:
            flash("The selected table does not have enough seats.", "error")
            return redirect(url_for("edit_reservation", id=reservation.id))

        clash = Reservation.query.filter_by(table_id=table_id, date=date, time=time).filter(
            Reservation.id != reservation.id
        ).first()
        if clash:
            flash("This table is already reserved for the selected date and time.", "error")
            return redirect(url_for("edit_reservation", id=reservation.id))

        old_table_id = reservation.table_id
        reservation.customer_name = customer_name
        reservation.phone = phone
        reservation.date = date
        reservation.time = time
        reservation.guests = guests
        reservation.table = table
        table.status = "Reserved"

        if old_table_id != table.id:
            old_table = db.session.get(RestaurantTable, old_table_id)
            remaining = Reservation.query.filter(
                Reservation.table_id == old_table_id,
                Reservation.id != reservation.id,
            ).count()
            if old_table and not remaining and old_table.status == "Reserved":
                old_table.status = "Available"

        if not commit_changes("Could not update the reservation. Please try again."):
            return redirect(url_for("edit_reservation", id=reservation.id))
        flash("Reservation updated successfully.", "success")
        return redirect(url_for("reservations"))

    return render_template(
        "reserve.html", tables=available_tables, reservation=reservation
    )


@app.route("/reservations/delete/<int:id>", methods=["POST"])
def delete_reservation(id):
    reservation = Reservation.query.get_or_404(id)
    table_id = reservation.table_id
    db.session.delete(reservation)
    table = db.session.get(RestaurantTable, table_id)
    remaining = Reservation.query.filter_by(table_id=table_id).count()
    if table and not remaining and table.status == "Reserved":
        table.status = "Available"

    if not commit_changes("Could not delete the reservation. Please try again."):
        return redirect(url_for("reservations"))
    flash("Reservation deleted.", "success")
    return redirect(url_for("reservations"))


# ---------------------------------------------------------------------------
# 4. ORDER MANAGEMENT
# ---------------------------------------------------------------------------
@app.route("/orders")
def orders():
    """Redirect to order history (kept for the /orders route requirement)."""
    return redirect(url_for("order_history"))


def adjust_order_stock(menu_item, quantity_delta):
    if not menu_item:
        return

    menu_item.quantity = max(0, menu_item.quantity + quantity_delta)
    matching_ingredient = Inventory.query.filter(
        Inventory.ingredient_name.ilike(f"%{menu_item.name}%")
    ).first()
    if matching_ingredient:
        matching_ingredient.quantity = max(
            0, matching_ingredient.quantity + quantity_delta
        )


def validated_order_lines(order=None):
    selected_ids = request.form.getlist("menu_item_id")
    quantities = request.form.getlist("quantity")
    if not selected_ids:
        flash("Please select at least one menu item.", "error")
        return None
    if len(selected_ids) != len(quantities):
        flash("Each selected menu item needs a quantity.", "error")
        return None

    previous_quantities = {}
    if order:
        for order_item in order.items:
            previous_quantities[order_item.menu_item_id] = (
                previous_quantities.get(order_item.menu_item_id, 0) + order_item.quantity
            )

    lines = []
    seen_ids = set()
    for raw_id, raw_quantity in zip(selected_ids, quantities):
        try:
            item_id = int(raw_id)
            quantity = int(raw_quantity)
        except (TypeError, ValueError):
            flash("Menu items and quantities must be valid whole numbers.", "error")
            return None

        if item_id in seen_ids or quantity < 1:
            flash("Choose each menu item once and enter a positive quantity.", "error")
            return None
        seen_ids.add(item_id)

        menu_item = db.session.get(MenuItem, item_id)
        if not menu_item:
            flash("A selected menu item no longer exists.", "error")
            return None
        available = menu_item.quantity + previous_quantities.get(item_id, 0)
        if quantity > available:
            flash(f'Not enough stock for "{menu_item.name}".', "error")
            return None
        lines.append((menu_item, quantity))
    return lines


def save_order(order=None):
    is_update = order is not None
    lines = validated_order_lines(order)
    if lines is None:
        endpoint = "edit_order" if order else "order_create"
        values = {"id": order.id} if order else {}
        return redirect(url_for(endpoint, **values))

    try:
        if order:
            for previous_item in list(order.items):
                adjust_order_stock(previous_item.menu_item, previous_item.quantity)
            order.items.clear()
        else:
            order = Order(total_amount=0.0, status="Completed")
            db.session.add(order)

        total = 0.0
        for menu_item, quantity in lines:
            subtotal = quantity * menu_item.price
            total += subtotal
            adjust_order_stock(menu_item, -quantity)
            order.items.append(
                OrderItem(quantity=quantity, subtotal=subtotal, menu_item=menu_item)
            )
        order.total_amount = total
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception("Could not save order transaction")
        flash("Could not save the order. Please try again.", "error")
        endpoint = "edit_order" if is_update else "order_create"
        values = {"id": order.id} if is_update else {}
        return redirect(url_for(endpoint, **values))
    flash(f"Order #{order.id} saved successfully! Total: ₹{total:.2f}", "success")
    return redirect(url_for("order_history"))


@app.route("/order/create", methods=["GET", "POST"])
def order_create():
    """Create an order and deduct its quantities from available stock."""
    if request.method == "POST":
        return save_order()

    menu_items = MenuItem.query.order_by(MenuItem.category, MenuItem.name).all()
    return render_template("order_create.html", menu_items=menu_items, order=None, order_quantities={})


@app.route("/order/edit/<int:id>", methods=["GET", "POST"])
def edit_order(id):
    order = Order.query.get_or_404(id)
    if request.method == "POST":
        return save_order(order)

    menu_items = MenuItem.query.order_by(MenuItem.category, MenuItem.name).all()
    order_quantities = {}
    for order_item in order.items:
        order_quantities[order_item.menu_item_id] = (
            order_quantities.get(order_item.menu_item_id, 0) + order_item.quantity
        )
    return render_template(
        "order_create.html",
        menu_items=menu_items,
        order=order,
        order_quantities=order_quantities,
    )


@app.route("/order/delete/<int:id>", methods=["POST"])
def delete_order(id):
    order = Order.query.get_or_404(id)
    for order_item in order.items:
        adjust_order_stock(order_item.menu_item, order_item.quantity)
    order_id = order.id
    db.session.delete(order)
    if not commit_changes("Could not delete the order. Please try again."):
        return redirect(url_for("order_history"))
    flash(f"Order #{order_id} deleted and stock restored.", "success")
    return redirect(url_for("order_history"))


@app.route("/order/history")
def order_history():
    """Show all past orders with their line items."""
    all_orders = Order.query.order_by(Order.order_date.desc()).all()
    return render_template("order_history.html", orders=all_orders)


# ---------------------------------------------------------------------------
# 5. INVENTORY MANAGEMENT
# ---------------------------------------------------------------------------
@app.route("/inventory")
def inventory():
    """Show all inventory ingredients and flag low stock."""
    all_inventory = Inventory.query.order_by(Inventory.ingredient_name).all()
    return render_template("inventory.html", inventory=all_inventory)


@app.route("/inventory/add", methods=["GET", "POST"])
def add_inventory():
    """Add a new ingredient to inventory, or update stock for an existing one."""
    if request.method == "POST":
        name = request.form.get("ingredient_name", "").strip()
        quantity = request.form.get("quantity", "0")
        unit = request.form.get("unit", "units").strip() or "units"
        threshold = request.form.get("low_stock_threshold", "5")

        if not name:
            flash("Ingredient name is required.", "error")
            return redirect(url_for("add_inventory"))

        try:
            quantity_value = float(quantity)
            threshold_value = float(threshold)
        except (TypeError, ValueError):
            flash("Quantity and low-stock threshold must be valid numbers.", "error")
            return redirect(url_for("add_inventory"))
        if (
            not math.isfinite(quantity_value)
            or not math.isfinite(threshold_value)
            or quantity_value < 0
            or threshold_value < 0
        ):
            flash("Quantity and low-stock threshold cannot be negative.", "error")
            return redirect(url_for("add_inventory"))

        existing = Inventory.query.filter(
            Inventory.ingredient_name.ilike(name)
        ).first()

        if existing:
            existing.quantity += quantity_value
            if not commit_changes("Could not update inventory stock. Please try again."):
                return redirect(url_for("add_inventory"))
            flash(f'Stock for "{name}" updated. New quantity: {existing.quantity}', "success")
        else:
            new_ingredient = Inventory(
                ingredient_name=name,
                quantity=quantity_value,
                unit=unit,
                low_stock_threshold=threshold_value,
            )
            db.session.add(new_ingredient)
            if not commit_changes("Could not add the ingredient. Please try again."):
                return redirect(url_for("add_inventory"))
            flash(f'Ingredient "{name}" added to inventory.', "success")

        return redirect(url_for("inventory"))

    return render_template("add_inventory.html")


@app.route("/inventory/update/<int:id>", methods=["POST"])
def update_inventory(id):
    """Update stock quantity for a specific ingredient (used from the inventory table)."""
    ingredient = Inventory.query.get_or_404(id)
    new_quantity = request.form.get("quantity")
    try:
        quantity = float(new_quantity)
    except (TypeError, ValueError):
        flash("Enter a valid non-negative stock quantity.", "error")
        return redirect(url_for("inventory"))
    if not math.isfinite(quantity) or quantity < 0:
        flash("Stock quantity cannot be negative.", "error")
        return redirect(url_for("inventory"))
    ingredient.quantity = quantity
    if not commit_changes("Could not update inventory stock. Please try again."):
        return redirect(url_for("inventory"))
    flash(f'Stock for "{ingredient.ingredient_name}" updated.', "success")
    return redirect(url_for("inventory"))


@app.route("/inventory/delete/<int:id>", methods=["POST"])
def delete_inventory(id):
    ingredient = Inventory.query.get_or_404(id)
    ingredient_name = ingredient.ingredient_name
    db.session.delete(ingredient)
    if not commit_changes("Could not delete the ingredient. Please try again."):
        return redirect(url_for("inventory"))
    flash(f'Ingredient "{ingredient_name}" deleted.', "success")
    return redirect(url_for("inventory"))


# ---------------------------------------------------------------------------
# 6. DASHBOARD
# ---------------------------------------------------------------------------
@app.route("/dashboard")
def dashboard():
    """Show key restaurant metrics at a glance."""
    total_orders = Order.query.count()
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0.0
    total_reservations = Reservation.query.count()
    available_tables = RestaurantTable.query.filter_by(status="Available").count()
    total_tables = RestaurantTable.query.count()

    low_stock_items = Inventory.query.filter(
        Inventory.quantity <= Inventory.low_stock_threshold
    ).all()

    recent_orders = Order.query.order_by(Order.order_date.desc()).limit(5).all()

    return render_template(
        "dashboard.html",
        total_orders=total_orders,
        total_revenue=total_revenue,
        total_reservations=total_reservations,
        available_tables=available_tables,
        total_tables=total_tables,
        low_stock_items=low_stock_items,
        recent_orders=recent_orders,
    )


# ---------------------------------------------------------------------------
# DATABASE INITIALIZATION + SAMPLE DATA
# ---------------------------------------------------------------------------
def seed_sample_data():
    """Add a few sample rows so the app looks good on first run (only if empty)."""
    if MenuItem.query.count() == 0:
        db.session.add_all(
            [
                MenuItem(name="Margherita Pizza", category="Main Course", price=8.99, quantity=25),
                MenuItem(name="Caesar Salad", category="Starters", price=5.49, quantity=30),
                MenuItem(name="Grilled Chicken", category="Main Course", price=11.99, quantity=20),
                MenuItem(name="Chocolate Lava Cake", category="Desserts", price=4.99, quantity=15),
                MenuItem(name="Iced Lemon Tea", category="Beverages", price=2.49, quantity=50),
            ]
        )

    if RestaurantTable.query.count() == 0:
        db.session.add_all(
            [
                RestaurantTable(table_number=1, capacity=2, status="Available"),
                RestaurantTable(table_number=2, capacity=4, status="Available"),
                RestaurantTable(table_number=3, capacity=4, status="Occupied"),
                RestaurantTable(table_number=4, capacity=6, status="Available"),
            ]
        )

    if Inventory.query.count() == 0:
        db.session.add_all(
            [
                Inventory(ingredient_name="Pizza Dough", quantity=20, unit="pcs", low_stock_threshold=5),
                Inventory(ingredient_name="Chicken Breast", quantity=15, unit="kg", low_stock_threshold=4),
                Inventory(ingredient_name="Lettuce", quantity=3, unit="kg", low_stock_threshold=5),
                Inventory(ingredient_name="Cocoa Powder", quantity=2, unit="kg", low_stock_threshold=3),
            ]
        )

    db.session.commit()


with app.app_context():
    db.create_all()
    seed_sample_data()


if __name__ == "__main__":
    app.run(debug=True)
