#!/usr/bin/env python3
"""
生成模拟生产环境数据
30+ 表，每表 50 万+ 行数据
"""
import psycopg2
import random
import string
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# 连接配置
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "database": "dba_assistant_test",
    "user": "cjwdsg"
}

# 批量插入大小
BATCH_SIZE = 10000

def random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def random_date(start_days=365*2, end_days=0):
    return datetime.now() - timedelta(days=random.randint(end_days, start_days))

def random_datetime(start_days=365*2, end_days=0):
    return datetime.now() - timedelta(
        days=random.randint(end_days, start_days),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )

def generate_users(count):
    """生成用户表"""
    table_name = "users"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    # 创建表
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(128),
            full_name VARCHAR(100),
            phone VARCHAR(20),
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            last_login TIMESTAMP,
            is_verified BOOLEAN DEFAULT FALSE,
            is_admin BOOLEAN DEFAULT FALSE
        )
    """)

    # 批量插入
    values = []
    for i in range(count):
        username = f"user_{i:010d}_{random_string(4)}"
        email = f"user_{i:010d}@example.com"
        values.append((
            username, email, random_string(64), f"Full Name {i}",
            f"+86-{random.randint(13000000000, 18999999999)}",
            random.choice(['active', 'inactive', 'suspended']),
            random_datetime(), random_datetime(), random_datetime(),
            random.choice([True, False]), random.choice([True, False])
        ))
        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (username, email, password_hash, full_name, phone, status, created_at, updated_at, last_login, is_verified, is_admin)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (username, email, password_hash, full_name, phone, status, created_at, updated_at, last_login, is_verified, is_admin)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_orders(count):
    """生成订单表"""
    table_name = "orders"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            order_no VARCHAR(32) UNIQUE NOT NULL,
            user_id INTEGER REFERENCES users(id),
            amount DECIMAL(12, 2) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            payment_method VARCHAR(20),
            payment_status VARCHAR(20) DEFAULT 'unpaid',
            shipping_address TEXT,
            receiver_name VARCHAR(100),
            receiver_phone VARCHAR(20),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            paid_at TIMESTAMP,
            shipped_at TIMESTAMP,
            delivered_at TIMESTAMP,
            tracking_no VARCHAR(50)
        )
    """)

    statuses = ['pending', 'paid', 'shipped', 'delivered', 'cancelled', 'refunded']
    payment_methods = ['alipay', 'wechat', 'card', 'bank_transfer']

    values = []
    for i in range(count):
        user_id = random.randint(1, 500000)
        amount = round(random.uniform(10, 5000), 2)
        status = random.choice(statuses)
        payment_status = random.choice(['paid', 'unpaid', 'refunding']) if status != 'cancelled' else 'refunded'

        values.append((
            f"ORD{i:010d}",
            user_id, amount, status, random.choice(payment_methods),
            payment_status, f"Address {i}", f"Receiver {i}",
            f"+86-{random.randint(13000000000, 18999999999)}",
            random_datetime(), random_datetime(),
            random_datetime() if status in ['paid', 'shipped', 'delivered'] else None,
            random_datetime() if status in ['shipped', 'delivered'] else None,
            random_datetime() if status == 'delivered' else None,
            f"TRACK{random.randint(100000000, 999999999)}" if status in ['shipped', 'delivered'] else None
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (order_no, user_id, amount, status, payment_method, payment_status, shipping_address, receiver_name, receiver_phone, created_at, updated_at, paid_at, shipped_at, delivered_at, tracking_no)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (order_no, user_id, amount, status, payment_method, payment_status, shipping_address, receiver_name, receiver_phone, created_at, updated_at, paid_at, shipped_at, delivered_at, tracking_no)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_products(count):
    """生成商品表"""
    table_name = "products"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            product_no VARCHAR(32) UNIQUE NOT NULL,
            name VARCHAR(200) NOT NULL,
            category VARCHAR(50),
            sub_category VARCHAR(50),
            brand VARCHAR(50),
            price DECIMAL(10, 2) NOT NULL,
            cost DECIMAL(10, 2),
            stock INTEGER DEFAULT 0,
            sales_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            description TEXT,
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)

    categories = ['Electronics', 'Clothing', 'Home', 'Sports', 'Books', 'Food', 'Beauty', 'Toys']
    brands = ['BrandA', 'BrandB', 'BrandC', 'BrandD', 'BrandE']
    statuses = ['active', 'inactive', 'discontinued']

    values = []
    for i in range(count):
        values.append((
            f"PRD{i:010d}",
            f"Product {i} - {random_string(20)}",
            random.choice(categories),
            f"SubCategory_{random.randint(1, 20)}",
            random.choice(brands),
            round(random.uniform(10, 5000), 2),
            round(random.uniform(5, 2500), 2),
            random.randint(0, 10000),
            random.randint(0, 50000),
            random.randint(0, 100000),
            f"Description for product {i}",
            random.choice(statuses),
            random_datetime(), random_datetime()
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (product_no, name, category, sub_category, brand, price, cost, stock, sales_count, view_count, description, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (product_no, name, category, sub_category, brand, price, cost, stock, sales_count, view_count, description, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_order_items(count):
    """生成订单明细表"""
    table_name = "order_items"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(id),
            product_id INTEGER REFERENCES products(id),
            quantity INTEGER NOT NULL,
            unit_price DECIMAL(10, 2) NOT NULL,
            subtotal DECIMAL(12, 2) NOT NULL,
            discount DECIMAL(10, 2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    values = []
    for i in range(count):
        values.append((
            random.randint(1, 500000),
            random.randint(1, 500000),
            random.randint(1, 10),
            round(random.uniform(10, 1000), 2),
            round(random.uniform(10, 10000), 2),
            round(random.uniform(0, 100), 2),
            random_datetime()
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (order_id, product_id, quantity, unit_price, subtotal, discount, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (order_id, product_id, quantity, unit_price, subtotal, discount, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_categories(count):
    """生成分类表"""
    table_name = "categories"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            parent_id INTEGER REFERENCES categories(id),
            level INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            icon VARCHAR(50),
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    values = []
    for i in range(count):
        values.append((
            f"Category_{i}",
            random.randint(1, 100) if i > 100 else None,
            random.randint(1, 3),
            random.randint(0, 100),
            f"icon_{i}",
            random.choice(['active', 'inactive']),
            random_datetime()
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (name, parent_id, level, sort_order, icon, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (name, parent_id, level, sort_order, icon, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_inventory(count):
    """生成库存表"""
    table_name = "inventory"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            product_id INTEGER REFERENCES products(id),
            warehouse_id INTEGER,
            quantity INTEGER NOT NULL,
            reserved_quantity INTEGER DEFAULT 0,
            available_quantity INTEGER GENERATED ALWAYS AS (quantity - reserved_quantity) STORED,
            last_inbound TIMESTAMP,
            last_outbound TIMESTAMP,
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)

    values = []
    for i in range(count):
        quantity = random.randint(0, 5000)
        reserved = random.randint(0, min(quantity, 100))
        values.append((
            random.randint(1, 500000),
            random.randint(1, 10),
            quantity,
            reserved,
            random_datetime(365) if random.random() > 0.3 else None,
            random_datetime(30) if random.random() > 0.5 else None,
            random_datetime()
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (product_id, warehouse_id, quantity, reserved_quantity, last_inbound, last_outbound, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (product_id, warehouse_id, quantity, reserved_quantity, last_inbound, last_outbound, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_payments(count):
    """生成支付表"""
    table_name = "payments"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            payment_no VARCHAR(32) UNIQUE NOT NULL,
            order_id INTEGER REFERENCES orders(id),
            user_id INTEGER REFERENCES users(id),
            amount DECIMAL(12, 2) NOT NULL,
            payment_method VARCHAR(20),
            status VARCHAR(20) DEFAULT 'pending',
            transaction_id VARCHAR(64),
            paid_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)

    statuses = ['pending', 'success', 'failed', 'refunded']
    methods = ['alipay', 'wechat', 'card', 'bank_transfer']

    values = []
    for i in range(count):
        status = random.choice(statuses)
        values.append((
            f"PAY{i:010d}",
            random.randint(1, 500000),
            random.randint(1, 500000),
            round(random.uniform(10, 5000), 2),
            random.choice(methods),
            status,
            f"TXN{random.randint(100000000, 999999999)}" if status == 'success' else None,
            random_datetime() if status in ['success', 'refunded'] else None,
            random_datetime(),
            random_datetime()
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (payment_no, order_id, user_id, amount, payment_method, status, transaction_id, paid_at, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (payment_no, order_id, user_id, amount, payment_method, status, transaction_id, paid_at, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_shipping(count):
    """生成物流表"""
    table_name = "shipping"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(id),
            carrier VARCHAR(50),
            tracking_no VARCHAR(64),
            status VARCHAR(20) DEFAULT 'pending',
            shipped_at TIMESTAMP,
            in_transit_at TIMESTAMP,
            delivered_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)

    statuses = ['pending', 'shipped', 'in_transit', 'delivered', 'exception']

    values = []
    for i in range(count):
        status = random.choice(statuses)
        values.append((
            random.randint(1, 500000),
            random.choice(['SF Express', 'JD Logistics', 'YTO', 'ZTO', 'EMS']),
            f"TRACK{i:010d}",
            status,
            random_datetime(30) if status in ['shipped', 'in_transit', 'delivered'] else None,
            random_datetime(15) if status in ['in_transit', 'delivered'] else None,
            random_datetime(7) if status == 'delivered' else None,
            random_datetime(),
            random_datetime()
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (order_id, carrier, tracking_no, status, shipped_at, in_transit_at, delivered_at, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (order_id, carrier, tracking_no, status, shipped_at, in_transit_at, delivered_at, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_reviews(count):
    """生成评论表"""
    table_name = "reviews"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(id),
            product_id INTEGER REFERENCES products(id),
            user_id INTEGER REFERENCES users(id),
            rating INTEGER CHECK (rating >= 1 AND rating <= 5),
            title VARCHAR(100),
            content TEXT,
            helpful_count INTEGER DEFAULT 0,
            status VARCHAR(20) DEFAULT 'published',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)

    values = []
    for i in range(count):
        values.append((
            random.randint(1, 500000),
            random.randint(1, 500000),
            random.randint(1, 500000),
            random.randint(1, 5),
            f"Review Title {i}",
            f"This is a review content for product. " * random.randint(1, 10),
            random.randint(0, 1000),
            random.choice(['published', 'hidden', 'pending']),
            random_datetime(365),
            random_datetime()
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (order_id, product_id, user_id, rating, title, content, helpful_count, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (order_id, product_id, user_id, rating, title, content, helpful_count, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_addresses(count):
    """生成收货地址表"""
    table_name = "addresses"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            receiver_name VARCHAR(100) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            province VARCHAR(30),
            city VARCHAR(30),
            district VARCHAR(30),
            address TEXT NOT NULL,
            postal_code VARCHAR(10),
            is_default BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    provinces = ['Beijing', 'Shanghai', 'Guangdong', 'Zhejiang', 'Jiangsu', 'Sichuan', 'Hubei', 'Hunan']
    cities = ['Beijing', 'Shanghai', 'Guangzhou', 'Shenzhen', 'Hangzhou', 'Nanjing', 'Chengdu', 'Wuhan', 'Changsha']

    values = []
    for i in range(count):
        values.append((
            random.randint(1, 500000),
            f"Receiver {i}",
            f"+86-{random.randint(13000000000, 18999999999)}",
            random.choice(provinces),
            random.choice(cities),
            f"District_{random.randint(1, 20)}",
            f"Detailed address {i}",
            f"{random.randint(100000, 999999)}",
            random.choice([True, False]),
            random_datetime()
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (user_id, receiver_name, phone, province, city, district, address, postal_code, is_default, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (user_id, receiver_name, phone, province, city, district, address, postal_code, is_default, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_coupons(count):
    """生成优惠券表"""
    table_name = "coupons"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            code VARCHAR(32) UNIQUE NOT NULL,
            name VARCHAR(100),
            coupon_type VARCHAR(20),
            discount_value DECIMAL(10, 2),
            min_order_amount DECIMAL(10, 2),
            max_discount_amount DECIMAL(10, 2),
            total_count INTEGER,
            used_count INTEGER DEFAULT 0,
            per_user_limit INTEGER DEFAULT 1,
            valid_from TIMESTAMP,
            valid_until TIMESTAMP,
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    types = ['cash', 'discount', 'shipping']

    values = []
    for i in range(count):
        total = random.randint(1000, 100000)
        values.append((
            f"COUPON{i:010d}",
            f"Coupon Name {i}",
            random.choice(types),
            round(random.uniform(5, 200), 2),
            round(random.uniform(50, 500), 2),
            round(random.uniform(10, 100), 2),
            total,
            random.randint(0, total),
            random.randint(1, 5),
            random_datetime(365, 180),
            random_datetime(179, 0),
            random.choice(['active', 'expired', 'disabled']),
            random_datetime()
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (code, name, coupon_type, discount_value, min_order_amount, max_discount_amount, total_count, used_count, per_user_limit, valid_from, valid_until, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (code, name, coupon_type, discount_value, min_order_amount, max_discount_amount, total_count, used_count, per_user_limit, valid_from, valid_until, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_user_coupons(count):
    """生成用户优惠券表"""
    table_name = "user_coupons"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            coupon_id INTEGER REFERENCES coupons(id),
            order_id INTEGER REFERENCES orders(id),
            status VARCHAR(20) DEFAULT 'unused',
            received_at TIMESTAMP DEFAULT NOW(),
            used_at TIMESTAMP
        )
    """)

    statuses = ['unused', 'used', 'expired']

    values = []
    for i in range(count):
        status = random.choice(statuses)
        values.append((
            random.randint(1, 500000),
            random.randint(1, 500000),
            random.randint(1, 500000) if random.random() > 0.3 else None,
            status,
            random_datetime(180),
            random_datetime() if status == 'used' else None
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (user_id, coupon_id, order_id, status, received_at, used_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (user_id, coupon_id, order_id, status, received_at, used_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_wishlists(count):
    """生成收藏表"""
    table_name = "wishlists"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            product_id INTEGER REFERENCES products(id),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    values = []
    for i in range(count):
        values.append((
            random.randint(1, 500000),
            random.randint(1, 500000),
            random_datetime()
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (user_id, product_id, created_at)
                VALUES (%s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (user_id, product_id, created_at)
            VALUES (%s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_notifications(count):
    """生成通知表"""
    table_name = "notifications"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            type VARCHAR(30),
            title VARCHAR(100),
            content TEXT,
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    types = ['order', 'promotion', 'system', 'security']

    values = []
    for i in range(count):
        values.append((
            random.randint(1, 500000),
            random.choice(types),
            f"Notification Title {i}",
            f"Notification content for user action {i}",
            random.choice([True, False]),
            random_datetime(180)
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (user_id, type, title, content, is_read, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (user_id, type, title, content, is_read, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_logs(count):
    """生成操作日志表"""
    table_name = "operation_logs"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            action VARCHAR(50),
            resource_type VARCHAR(30),
            resource_id INTEGER,
            ip_address VARCHAR(40),
            user_agent TEXT,
            request_data TEXT,
            response_status INTEGER,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    actions = ['login', 'logout', 'create', 'update', 'delete', 'view', 'download']
    resource_types = ['order', 'product', 'user', 'coupon', 'review']

    values = []
    for i in range(count):
        values.append((
            random.randint(1, 500000),
            random.choice(actions),
            random.choice(resource_types),
            random.randint(1, 1000000),
            f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
            f"User-Agent {i}",
            f"{{'action': '{random.choice(actions)}', 'data': {i}}}",
            random.choice([200, 200, 200, 400, 500]),
            random_datetime(90)
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (user_id, action, resource_type, resource_id, ip_address, user_agent, request_data, response_status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (user_id, action, resource_type, resource_id, ip_address, user_agent, request_data, response_status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_sessions(count):
    """生成会话表"""
    table_name = "sessions"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(64) UNIQUE NOT NULL,
            user_id INTEGER REFERENCES users(id),
            ip_address VARCHAR(40),
            user_agent TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            expires_at TIMESTAMP,
            last_activity TIMESTAMP DEFAULT NOW()
        )
    """)

    values = []
    for i in range(count):
        is_active = random.choice([True, True, True, False])
        values.append((
            f"SESSION_{random_string(32)}",
            random.randint(1, 500000),
            f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
            f"User-Agent {i}",
            is_active,
            random_datetime(),
            random_datetime(7) + timedelta(days=7),
            random_datetime(7)
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (session_id, user_id, ip_address, user_agent, is_active, created_at, expires_at, last_activity)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (session_id, user_id, ip_address, user_agent, is_active, created_at, expires_at, last_activity)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_warehouses(count):
    """生成仓库表"""
    table_name = "warehouses"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            type VARCHAR(20),
            province VARCHAR(30),
            city VARCHAR(30),
            district VARCHAR(30),
            address TEXT,
            manager_name VARCHAR(50),
            manager_phone VARCHAR(20),
            capacity INTEGER,
            current_stock INTEGER DEFAULT 0,
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    types = ['central', 'regional', 'front']
    statuses = ['active', 'inactive', 'maintenance']

    values = []
    for i in range(count):
        values.append((
            f"WH{i:06d}",
            f"Warehouse {i}",
            random.choice(types),
            random.choice(['Beijing', 'Shanghai', 'Guangdong', 'Zhejiang']),
            random.choice(['Beijing', 'Shanghai', 'Guangzhou', 'Shenzhen']),
            f"District_{random.randint(1, 20)}",
            f"Warehouse address {i}",
            f"Manager {i}",
            f"+86-{random.randint(13000000000, 18999999999)}",
            random.randint(10000, 1000000),
            random.randint(0, 500000),
            random.choice(statuses),
            random_datetime()
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (code, name, type, province, city, district, address, manager_name, manager_phone, capacity, current_stock, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (code, name, type, province, city, district, address, manager_name, manager_phone, capacity, current_stock, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_suppliers(count):
    """生成供应商表"""
    table_name = "suppliers"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(200) NOT NULL,
            contact_name VARCHAR(50),
            contact_phone VARCHAR(20),
            contact_email VARCHAR(100),
            province VARCHAR(30),
            city VARCHAR(30),
            address TEXT,
            rating DECIMAL(2, 1),
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    statuses = ['active', 'inactive', 'suspended']

    values = []
    for i in range(count):
        values.append((
            f"SUP{i:06d}",
            f"Supplier Company {i}",
            f"Contact Person {i}",
            f"+86-{random.randint(13000000000, 18999999999)}",
            f"contact{i}@supplier.com",
            random.choice(['Beijing', 'Shanghai', 'Guangdong', 'Zhejiang', 'Jiangsu']),
            random.choice(['Beijing', 'Shanghai', 'Guangzhou', 'Shenzhen', 'Hangzhou']),
            f"Supplier address {i}",
            round(random.uniform(3.0, 5.0), 1),
            random.choice(statuses),
            random_datetime()
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (code, name, contact_name, contact_phone, contact_email, province, city, address, rating, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (code, name, contact_name, contact_phone, contact_email, province, city, address, rating, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_inbound_records(count):
    """生成入库记录表"""
    table_name = "inbound_records"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            inbound_no VARCHAR(32) UNIQUE NOT NULL,
            warehouse_id INTEGER REFERENCES warehouses(id),
            supplier_id INTEGER REFERENCES suppliers(id),
            product_id INTEGER REFERENCES products(id),
            quantity INTEGER NOT NULL,
            unit_cost DECIMAL(10, 2),
            total_cost DECIMAL(12, 2),
            status VARCHAR(20) DEFAULT 'pending',
            operator VARCHAR(50),
            inbound_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    statuses = ['pending', 'in_transit', 'received', 'cancelled']

    values = []
    for i in range(count):
        quantity = random.randint(10, 1000)
        unit_cost = round(random.uniform(5, 500), 2)
        values.append((
            f"INB{i:010d}",
            random.randint(1, 500000),
            random.randint(1, 500000),
            random.randint(1, 500000),
            quantity,
            unit_cost,
            round(quantity * unit_cost, 2),
            random.choice(statuses),
            f"Operator_{random.randint(1, 100)}",
            random_datetime(90),
            random_datetime()
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (inbound_no, warehouse_id, supplier_id, product_id, quantity, unit_cost, total_cost, status, operator, inbound_at, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (inbound_no, warehouse_id, supplier_id, product_id, quantity, unit_cost, total_cost, status, operator, inbound_at, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_outbound_records(count):
    """生成出库记录表"""
    table_name = "outbound_records"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            outbound_no VARCHAR(32) UNIQUE NOT NULL,
            warehouse_id INTEGER REFERENCES warehouses(id),
            order_id INTEGER REFERENCES orders(id),
            product_id INTEGER REFERENCES products(id),
            quantity INTEGER NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            operator VARCHAR(50),
            outbound_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    statuses = ['pending', 'picking', 'shipped', 'delivered', 'cancelled']

    values = []
    for i in range(count):
        values.append((
            f"OUT{i:010d}",
            random.randint(1, 500000),
            random.randint(1, 500000),
            random.randint(1, 500000),
            random.randint(1, 100),
            random.choice(statuses),
            f"Operator_{random.randint(1, 100)}",
            random_datetime(60),
            random_datetime()
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (outbound_no, warehouse_id, order_id, product_id, quantity, status, operator, outbound_at, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (outbound_no, warehouse_id, order_id, product_id, quantity, status, operator, outbound_at, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_return_records(count):
    """生成退货记录表"""
    table_name = "return_records"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            return_no VARCHAR(32) UNIQUE NOT NULL,
            order_id INTEGER REFERENCES orders(id),
            product_id INTEGER REFERENCES products(id),
            user_id INTEGER REFERENCES users(id),
            quantity INTEGER NOT NULL,
            reason VARCHAR(200),
            refund_amount DECIMAL(10, 2),
            status VARCHAR(20) DEFAULT 'pending',
            processed_by VARCHAR(50),
            processed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    statuses = ['pending', 'approved', 'rejected', 'returned', 'refunded']
    reasons = ['defective', 'wrong_item', 'not_as_described', 'changed_mind', 'other']

    values = []
    for i in range(count):
        status = random.choice(statuses)
        values.append((
            f"RET{i:010d}",
            random.randint(1, 500000),
            random.randint(1, 500000),
            random.randint(1, 500000),
            random.randint(1, 10),
            random.choice(reasons),
            round(random.uniform(10, 1000), 2),
            status,
            f"Staff_{random.randint(1, 50)}" if status in ['approved', 'rejected', 'returned', 'refunded'] else None,
            random_datetime(30) if status in ['approved', 'rejected', 'returned', 'refunded'] else None,
            random_datetime(60)
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (return_no, order_id, product_id, user_id, quantity, reason, refund_amount, status, processed_by, processed_at, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (return_no, order_id, product_id, user_id, quantity, reason, refund_amount, status, processed_by, processed_at, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_invoice_records(count):
    """生成发票记录表"""
    table_name = "invoice_records"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            invoice_no VARCHAR(32) UNIQUE NOT NULL,
            order_id INTEGER REFERENCES orders(id),
            user_id INTEGER REFERENCES users(id),
            title VARCHAR(100),
            tax_no VARCHAR(30),
            amount DECIMAL(12, 2),
            status VARCHAR(20) DEFAULT 'pending',
            issued_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    statuses = ['pending', 'issued', 'invalid']

    values = []
    for i in range(count):
        status = random.choice(statuses)
        values.append((
            f"INV{i:010d}",
            random.randint(1, 500000),
            random.randint(1, 500000),
            f"Invoice Title {i}",
            f"{random.randint(100000000, 999999999)}",
            round(random.uniform(100, 10000), 2),
            status,
            random_datetime(60) if status == 'issued' else None,
            random_datetime()
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (invoice_no, order_id, user_id, title, tax_no, amount, status, issued_at, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (invoice_no, order_id, user_id, title, tax_no, amount, status, issued_at, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_product_images(count):
    """生成商品图片表"""
    table_name = "product_images"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            product_id INTEGER REFERENCES products(id),
            url VARCHAR(500) NOT NULL,
            is_primary BOOLEAN DEFAULT FALSE,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    values = []
    for i in range(count):
        values.append((
            random.randint(1, 500000),
            f"https://cdn.example.com/images/{random.randint(1, 10000)}.jpg",
            random.choice([True, False, False, False]),
            random.randint(0, 10),
            random_datetime()
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (product_id, url, is_primary, sort_order, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (product_id, url, is_primary, sort_order, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_banners(count):
    """生成横幅表"""
    table_name = "banners"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            title VARCHAR(100) NOT NULL,
            image_url VARCHAR(500),
            link_url VARCHAR(500),
            position VARCHAR(20),
            sort_order INTEGER DEFAULT 0,
            status VARCHAR(20) DEFAULT 'active',
            start_at TIMESTAMP,
            end_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    positions = ['home_top', 'home_middle', 'home_bottom', 'category', 'product']

    values = []
    for i in range(count):
        values.append((
            f"Banner Title {i}",
            f"https://cdn.example.com/banners/{random.randint(1, 1000)}.jpg",
            f"https://www.example.com/target/{i}",
            random.choice(positions),
            random.randint(0, 100),
            random.choice(['active', 'inactive']),
            random_datetime(180, 90),
            random_datetime(89, 0),
            random_datetime()
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (title, image_url, link_url, position, sort_order, status, start_at, end_at, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (title, image_url, link_url, position, sort_order, status, start_at, end_at, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_search_history(count):
    """生成搜索历史表"""
    table_name = "search_history"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            keyword VARCHAR(100) NOT NULL,
            result_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    keywords = ['iPhone', 'MacBook', 'AirPods', 'Samsung', 'Xiaomi', 'Huawei', 'Nike', 'Adidas', 'laptop', 'phone', 'tablet', 'watch', 'headphones', 'camera', 'speaker']

    values = []
    for i in range(count):
        values.append((
            random.randint(1, 500000),
            random.choice(keywords) + f" {random.randint(1, 100)}",
            random.randint(0, 10000),
            random_datetime(90)
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (user_id, keyword, result_count, created_at)
                VALUES (%s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (user_id, keyword, result_count, created_at)
            VALUES (%s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_cart_items(count):
    """生成购物车表"""
    table_name = "cart_items"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            product_id INTEGER REFERENCES products(id),
            quantity INTEGER DEFAULT 1,
            selected BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)

    values = []
    for i in range(count):
        values.append((
            random.randint(1, 500000),
            random.randint(1, 500000),
            random.randint(1, 20),
            random.choice([True, False]),
            random_datetime(30),
            random_datetime()
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (user_id, product_id, quantity, selected, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (user_id, product_id, quantity, selected, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_point_transactions(count):
    """生成积分变动表"""
    table_name = "point_transactions"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            type VARCHAR(20) NOT NULL,
            amount INTEGER NOT NULL,
            balance INTEGER,
            reason VARCHAR(100),
            order_id INTEGER REFERENCES orders(id),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    types = ['earn', 'redeem', 'expire', 'adjust']

    values = []
    for i in range(count):
        amount = random.randint(-1000, 500)
        values.append((
            random.randint(1, 500000),
            random.choice(types),
            amount,
            random.randint(0, 100000),
            f"Point reason {i}",
            random.randint(1, 500000) if random.random() > 0.3 else None,
            random_datetime(180)
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (user_id, type, amount, balance, reason, order_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (user_id, type, amount, balance, reason, order_id, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_level_configs(count):
    """生成会员等级配置表"""
    table_name = "level_configs"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            level_name VARCHAR(30) NOT NULL,
            min_points INTEGER NOT NULL,
            max_points INTEGER,
            discount_rate DECIMAL(4, 2),
            point_multiplier DECIMAL(2, 1),
            benefits TEXT,
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    levels = ['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond']
    benefits = ['Basic discount', 'Extra discount', 'Priority support', 'Free shipping', 'Exclusive access']

    values = []
    for i, level in enumerate(levels):
        min_pts = i * 10000
        max_pts = (i + 1) * 10000 - 1 if i < len(levels) - 1 else None
        values.append((
            level,
            min_pts,
            max_pts,
            round(0.01 * (i + 1), 2),
            round(1.0 + i * 0.2, 1),
            f"{'; '.join(benefits[:i+1])}",
            'active',
            random_datetime()
        ))

    # Insert all at once
    cur.executemany(f"""
        INSERT INTO {table_name} (level_name, min_points, max_points, discount_rate, point_multiplier, benefits, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, values)
    conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒 (少量配置数据)")

def generate_product_tags(count):
    """生成商品标签表"""
    table_name = "product_tags"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            product_id INTEGER REFERENCES products(id),
            tag VARCHAR(30) NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    tags = ['hot', 'new', 'sale', 'recommend', 'bestseller', 'limited', 'preorder', 'clearance']

    values = []
    for i in range(count):
        values.append((
            random.randint(1, 500000),
            random.choice(tags),
            random_datetime()
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (product_id, tag, created_at)
                VALUES (%s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (product_id, tag, created_at)
            VALUES (%s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def generate_sensitive_words(count):
    """生成敏感词表"""
    table_name = "sensitive_words"
    print(f"创建 {table_name} 表，插入 {count:,} 行...")
    start = time.time()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            word VARCHAR(50) UNIQUE NOT NULL,
            type VARCHAR(20),
            level INTEGER DEFAULT 1,
            replace_text VARCHAR(50),
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    words = ['spam', 'fake', 'illegal', 'prohibited', 'scam', 'fraud', 'fake', ' counterfeit', 'smuggled', 'pirated']

    values = []
    for i in range(count):
        values.append((
            f"{random.choice(words)}_{i}",
            random.choice(['political', 'commercial', 'illegal', 'vulgar']),
            random.randint(1, 3),
            '***',
            'active',
            random_datetime()
        ))

        if len(values) >= BATCH_SIZE:
            cur.executemany(f"""
                INSERT INTO {table_name} (word, type, level, replace_text, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, values)
            conn.commit()
            values = []

    if values:
        cur.executemany(f"""
            INSERT INTO {table_name} (word, type, level, replace_text, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, values)
        conn.commit()

    elapsed = time.time() - start
    print(f"  ✓ {table_name} 完成，耗时 {elapsed:.1f}秒")

def main():
    global conn, cur

    print("=" * 60)
    print("开始生成模拟生产环境数据")
    print("=" * 60)

    # 连接数据库
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print(f"✓ 连接到数据库: {DB_CONFIG['database']}")

    total_start = time.time()

    # 表生成顺序：先有主表数据，再有外键关联
    # 基础表 (无或少量外键)
    generate_level_configs(5)  # 会员等级配置，少量数据
    generate_users(500000)    # 用户
    generate_products(500000)  # 商品
    generate_warehouses(500000) # 仓库
    generate_suppliers(500000) # 供应商
    generate_categories(500000) # 分类

    # 业务表
    generate_orders(500000)     # 订单
    generate_order_items(500000) # 订单明细
    generate_inventory(500000)  # 库存
    generate_payments(500000)   # 支付
    generate_shipping(500000)   # 物流
    generate_reviews(500000)    # 评论
    generate_addresses(500000) # 地址
    generate_coupons(500000)    # 优惠券
    generate_user_coupons(500000) # 用户优惠券
    generate_wishlists(500000)  # 收藏
    generate_notifications(500000) # 通知
    generate_logs(500000) # 操作日志
    generate_sessions(500000)  # 会话
    generate_inbound_records(500000) # 入库记录
    generate_outbound_records(500000) # 出库记录
    generate_return_records(500000) # 退货记录
    generate_invoice_records(500000) # 发票记录
    generate_product_images(500000) # 商品图片
    generate_banners(500000)    # 横幅
    generate_search_history(500000) # 搜索历史
    generate_cart_items(500000) # 购物车
    generate_point_transactions(500000) # 积分变动
    generate_product_tags(500000) # 商品标签
    generate_sensitive_words(500000) # 敏感词

    conn.commit()
    cur.close()
    conn.close()

    total_elapsed = time.time() - total_start
    print("=" * 60)
    print(f"✓ 数据生成完成！总耗时: {total_elapsed:.1f}秒 ({total_elapsed/60:.1f}分钟)")
    print("=" * 60)

    # 验证
    print("\n验证数据...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name, pg_relation_size(quote_ident(table_name)::regclass) as size
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY size DESC
        LIMIT 20
    """)
    tables = cur.fetchall()
    print("\n表大小排名 (前20):")
    for t, s in tables:
        print(f"  {t}: {s/1024/1024:.1f} MB")

    cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
    table_count = cur.fetchone()[0]
    print(f"\n总表数: {table_count}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
