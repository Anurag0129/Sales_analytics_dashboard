import random
from datetime import datetime, timedelta
from faker import Faker
from db_config import get_connection

fake = Faker()

CATEGORIES = ["Electronics", "Clothing", "Home & Kitchen", "Books", "Sports", "Beauty"]

PRODUCT_NAMES = {
    "Electronics": ["Wireless Earbuds", "Bluetooth Speaker", "Smartwatch", "Laptop Stand", "USB-C Hub", "Power Bank", "Webcam", "Mechanical Keyboard"],
    "Clothing": ["Cotton T-Shirt", "Denim Jacket", "Running Shoes", "Hoodie", "Formal Shirt", "Sneakers", "Winter Jacket", "Casual Trousers"],
    "Home & Kitchen": ["Air Fryer", "Coffee Maker", "Non-stick Pan Set", "Blender", "Vacuum Cleaner", "Dinner Set", "Knife Set", "Storage Containers"],
    "Books": ["Fiction Novel", "Self-Help Book", "Cookbook", "Biography", "Mystery Thriller", "Business Book", "Children's Storybook"],
    "Sports": ["Yoga Mat", "Dumbbell Set", "Cricket Bat", "Football", "Resistance Bands", "Skipping Rope", "Badminton Racket"],
    "Beauty": ["Face Moisturizer", "Shampoo", "Lipstick Set", "Sunscreen", "Hair Dryer", "Perfume", "Face Wash"]
}

ORDER_STATUSES = ["delivered", "delivered", "delivered", "shipped", "pending", "cancelled"]
# weighted: more delivered, fewer cancelled/pending

NUM_CUSTOMERS = 150
NUM_ORDERS = 700
MONTHS_BACK = 12


def clear_existing_data(cur):
    print("Clearing existing data...")
    cur.execute("TRUNCATE TABLE order_items, orders, products, customers RESTART IDENTITY CASCADE;")


def seed_customers(cur):
    print(f"Seeding {NUM_CUSTOMERS} customers...")
    customers = []
    for _ in range(NUM_CUSTOMERS):
        name = fake.name()
        email = fake.unique.email()
        phone = fake.msisdn()[:15]
        created_at = fake.date_time_between(start_date=f"-{MONTHS_BACK}M", end_date="now")
        customers.append((name, email, phone, created_at))

    cur.executemany(
        "INSERT INTO customers (name, email, phone, created_at) VALUES (%s, %s, %s, %s)",
        customers
    )
    print(f"Inserted {len(customers)} customers.")


def seed_products(cur):
    print("Seeding products...")
    products = []
    for category, names in PRODUCT_NAMES.items():
        for name in names:
            price = round(random.uniform(199, 4999), 2)
            stock = random.randint(10, 200)
            products.append((name, price, stock, category))

    cur.executemany(
        "INSERT INTO products (product_name, price, stock_quantity, category) VALUES (%s, %s, %s, %s)",
        products
    )
    print(f"Inserted {len(products)} products.")


def seed_orders_and_items(cur):
    print(f"Seeding {NUM_ORDERS} orders with items...")

    cur.execute("SELECT customer_id FROM customers")
    customer_ids = [row[0] for row in cur.fetchall()]

    cur.execute("SELECT product_id, price FROM products")
    products = cur.fetchall()  # list of (product_id, price)

    now = datetime.now()
    start_date = now - timedelta(days=MONTHS_BACK * 30)

    order_insert_query = """
        INSERT INTO orders (customer_id, order_status, order_date)
        VALUES (%s, %s, %s) RETURNING order_id
    """
    item_insert_query = """
        INSERT INTO order_items (order_id, product_id, quantity, price_at_order)
        VALUES (%s, %s, %s, %s)
    """

    total_items = 0

    for i in range(NUM_ORDERS):
        customer_id = random.choice(customer_ids)
        status = random.choice(ORDER_STATUSES)

        # bias order dates to be more frequent in recent months (simple linear weighting)
        days_offset = int(random.triangular(0, MONTHS_BACK * 30, MONTHS_BACK * 30))
        order_date = start_date + timedelta(days=days_offset, hours=random.randint(0, 23))

        cur.execute(order_insert_query, (customer_id, status, order_date))
        order_id = cur.fetchone()[0]

        num_items = random.randint(1, 5)
        chosen_products = random.sample(products, min(num_items, len(products)))

        for product_id, price in chosen_products:
            quantity = random.randint(1, 4)
            cur.execute(item_insert_query, (order_id, product_id, quantity, price))
            total_items += 1

        if (i + 1) % 100 == 0:
            print(f"  ...{i + 1} orders created")

    print(f"Inserted {NUM_ORDERS} orders and {total_items} order items.")


def main():
    conn = get_connection()
    cur = conn.cursor()

    try:
        clear_existing_data(cur)
        seed_customers(cur)
        seed_products(cur)
        seed_orders_and_items(cur)
        conn.commit()
        print("\nSeeding complete and committed successfully!")
    except Exception as e:
        conn.rollback()
        print(f"Error occurred, rolled back: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()