from db_config import get_connection

conn = get_connection()
print("Connected successfully!")

cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM products;")
result = cur.fetchone()
print(f"Number of products in database: {result[0]}")

cur.close()
conn.close()
