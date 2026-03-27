#!/usr/bin/env python3
"""
ERP 仿真数据库生成脚本
完整版 ERP，每表 2 万行数据
用于智能助手监控演示：慢查询、死锁、连接管理等
"""
import psycopg2
import random
import string
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import sys

# 连接配置
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "database": "erp_simulation",
    "user": "cjwdsg"
}

# 批量插入大小
BATCH_SIZE = 5000
# 每表默认行数
DEFAULT_ROWS = 20000

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

def random_phone():
    return f"+86-{random.randint(13000000000, 19999999999)}"

def random_id_card():
    """生成随机身份证号"""
    area = f"{random.randint(110000, 659000):06d}"
    birth = random_date(60, 18).strftime("%Y%m%d")
    seq = f"{random.randint(0, 999):03d}"
    return f"{area}{birth}{seq}{random.randint(0, 9)}"

def random_bank_account():
    return f"{random.randint(6200000000000000, 6299999999999999)}"

def random_address():
    provinces = ["北京", "上海", "广东", "浙江", "江苏", "四川", "湖北", "湖南", "河南", "山东"]
    cities = ["市", "市", "市", "县"]
    districts = ["区", "县", "开发区"]
    streets = ["路", "街", "大道"]
    return (f"{random.choice(provinces)}{random.choice(cities[0]) if len(random.choice(cities)) > 1 else '市'}"
            f"{random.choice(districts)}{random.randint(1, 999)}{random.choice(streets)}"
            f"{random.randint(1, 999)}号")

def random_product_name():
    adjectives = ["高级", "优质", "标准", "经济", "豪华", "专业", "便携", "智能"]
    nouns = ["电脑", "手机", "打印机", "显示器", "键盘", "鼠标", "耳机", "相机",
             "显示器", "投影仪", "扫描仪", "复印机", "服务器", "存储设备", "网络设备"]
    return f"{random.choice(adjectives)}{random.choice(nouns)}-{random_string(6).upper()}"

def random_company_name():
    prefixes = ["深圳", "上海", "北京", "广州", "杭州", "南京", "武汉", "成都", "西安", "苏州"]
    nouns = ["科技", "实业", "贸易", "电子", "机械", "化工", "纺织", "食品", "医药", "建材"]
    sufs = ["有限公司", "股份有限公司", "集团公司"]
    return f"{random.choice(prefixes)}{random.choice(nouns)}{random.choice(sufs)}"

def random_person_name():
    surnames = ["王", "李", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴", "徐", "孙", "胡", "朱", "高"]
    names = ["伟", "芳", "娜", "敏", "静", "丽", "强", "磊", "军", "洋", "勇", "艳", "杰", "涛", "明"]
    return f"{random.choice(surnames)}{random.choice(names)}"

def setup_database():
    """创建数据库"""
    print("=" * 60)
    print("ERP 仿真数据库生成器")
    print("=" * 60)

    # 先连接到 postgres 数据库来创建新数据库
    config = DB_CONFIG.copy()
    config["database"] = "postgres"

    try:
        conn = psycopg2.connect(**config)
        conn.autocommit = True
        cur = conn.cursor()

        # 检查数据库是否存在，如存在则删除重建
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_CONFIG["database"],))
        if cur.fetchone():
            # 终止所有到该数据库的连接
            cur.execute(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{DB_CONFIG["database"]}'
                AND pid <> pg_backend_pid()
            """)
            cur.execute(f'DROP DATABASE {DB_CONFIG["database"]}')
            print(f"✓ 删除旧数据库: {DB_CONFIG['database']}")

        cur.execute(f'CREATE DATABASE {DB_CONFIG["database"]}')
        print(f"✓ 创建数据库: {DB_CONFIG['database']}")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"✗ 创建数据库失败: {e}")
        sys.exit(1)

    # 连接到目标数据库
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor()

    print(f"✓ 连接数据库: {DB_CONFIG['database']}")
    return conn, cur

def create_tables(cur):
    """创建 ERP 表结构"""
    print("\n>>> 创建表结构...")

    tables = [
        # ========== HR 模块 ==========
        """
        CREATE TABLE hr_departments (
            id SERIAL PRIMARY KEY,
            code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            parent_id INTEGER REFERENCES hr_departments(id),
            manager_id INTEGER,
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE hr_positions (
            id SERIAL PRIMARY KEY,
            code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            department_id INTEGER REFERENCES hr_departments(id),
            level INTEGER DEFAULT 1,
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE hr_employees (
            id SERIAL PRIMARY KEY,
            employee_code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(50) NOT NULL,
            id_card VARCHAR(18) UNIQUE,
            gender VARCHAR(10),
            birth_date DATE,
            phone VARCHAR(20),
            email VARCHAR(100),
            department_id INTEGER REFERENCES hr_departments(id),
            position_id INTEGER REFERENCES hr_positions(id),
            hire_date DATE,
            contract_start DATE,
            contract_end DATE,
            status VARCHAR(20) DEFAULT 'active',
            bank_account VARCHAR(30),
            social_security_no VARCHAR(30),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE hr_attendance (
            id SERIAL PRIMARY KEY,
            employee_id INTEGER REFERENCES hr_employees(id),
            work_date DATE NOT NULL,
            check_in_time TIME,
            check_out_time TIME,
            status VARCHAR(20) DEFAULT 'normal',
            overtime_hours DECIMAL(4,1) DEFAULT 0,
            leave_type VARCHAR(20),
            remarks TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE hr_salary (
            id SERIAL PRIMARY KEY,
            employee_id INTEGER REFERENCES hr_employees(id),
            salary_month VARCHAR(7) NOT NULL,
            base_salary DECIMAL(10,2),
            overtime_pay DECIMAL(10,2) DEFAULT 0,
            bonus DECIMAL(10,2) DEFAULT 0,
            deduction DECIMAL(10,2) DEFAULT 0,
            net_salary DECIMAL(10,2),
            paid_at TIMESTAMP,
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,

        # ========== CRM 模块 ==========
        """
        CREATE TABLE crm_customers (
            id SERIAL PRIMARY KEY,
            customer_code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(200) NOT NULL,
            short_name VARCHAR(100),
            customer_type VARCHAR(20),
            industry VARCHAR(50),
            credit_rating VARCHAR(10),
            credit_limit DECIMAL(15,2) DEFAULT 0,
            contact_person VARCHAR(50),
            contact_phone VARCHAR(20),
            contact_email VARCHAR(100),
            address TEXT,
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE crm_contacts (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER REFERENCES crm_customers(id),
            name VARCHAR(50) NOT NULL,
            gender VARCHAR(10),
            phone VARCHAR(20),
            email VARCHAR(100),
            position VARCHAR(50),
            is_primary BOOLEAN DEFAULT FALSE,
            birthday DATE,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE crm_customer_addresses (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER REFERENCES crm_customers(id),
            address_type VARCHAR(20),
            contact_name VARCHAR(50),
            contact_phone VARCHAR(20),
            address TEXT,
            is_default BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,

        # ========== SCM/供应商模块 ==========
        """
        CREATE TABLE scm_suppliers (
            id SERIAL PRIMARY KEY,
            supplier_code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(200) NOT NULL,
            short_name VARCHAR(100),
            supplier_type VARCHAR(20),
            industry VARCHAR(50),
            contact_person VARCHAR(50),
            contact_phone VARCHAR(20),
            contact_email VARCHAR(100),
            address TEXT,
            bank_account VARCHAR(30),
            tax_no VARCHAR(30),
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE scm_supplier_contacts (
            id SERIAL PRIMARY KEY,
            supplier_id INTEGER REFERENCES scm_suppliers(id),
            name VARCHAR(50) NOT NULL,
            gender VARCHAR(10),
            phone VARCHAR(20),
            email VARCHAR(100),
            position VARCHAR(50),
            is_primary BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,

        # ========== INV 库存模块 ==========
        """
        CREATE TABLE inv_warehouses (
            id SERIAL PRIMARY KEY,
            code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            warehouse_type VARCHAR(20),
            address TEXT,
            manager_id INTEGER,
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE inv_locations (
            id SERIAL PRIMARY KEY,
            warehouse_id INTEGER REFERENCES inv_warehouses(id),
            location_code VARCHAR(20) UNIQUE NOT NULL,
            zone VARCHAR(20),
            aisle VARCHAR(10),
            rack VARCHAR(10),
            shelf VARCHAR(10),
            bin VARCHAR(10),
            status VARCHAR(20) DEFAULT 'available',
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE inv_product_categories (
            id SERIAL PRIMARY KEY,
            code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            parent_id INTEGER REFERENCES inv_product_categories(id),
            level INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE inv_products (
            id SERIAL PRIMARY KEY,
            product_code VARCHAR(30) UNIQUE NOT NULL,
            name VARCHAR(200) NOT NULL,
            category_id INTEGER REFERENCES inv_product_categories(id),
            spec VARCHAR(100),
            unit VARCHAR(10),
            cost_price DECIMAL(12,2) DEFAULT 0,
            sale_price DECIMAL(12,2) DEFAULT 0,
            safety_stock INTEGER DEFAULT 0,
            reorder_point INTEGER DEFAULT 0,
            weight DECIMAL(8,2),
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE inv_inventory (
            id SERIAL PRIMARY KEY,
            product_id INTEGER REFERENCES inv_products(id),
            warehouse_id INTEGER REFERENCES inv_warehouses(id),
            location_id INTEGER REFERENCES inv_locations(id),
            quantity INTEGER DEFAULT 0,
            available_quantity INTEGER DEFAULT 0,
            reserved_quantity INTEGER DEFAULT 0,
            unit_cost DECIMAL(12,2) DEFAULT 0,
            last_in_date TIMESTAMP,
            last_out_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE inv_inventory_transactions (
            id SERIAL PRIMARY KEY,
            transaction_no VARCHAR(30) UNIQUE NOT NULL,
            product_id INTEGER REFERENCES inv_products(id),
            warehouse_id INTEGER REFERENCES inv_warehouses(id),
            location_id INTEGER REFERENCES inv_locations(id),
            transaction_type VARCHAR(20) NOT NULL,
            quantity INTEGER NOT NULL,
            before_quantity INTEGER,
            after_quantity INTEGER,
            reference_no VARCHAR(50),
            operator_id INTEGER,
            remarks TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,

        # ========== PUR 采购模块 ==========
        """
        CREATE TABLE pur_purchase_orders (
            id SERIAL PRIMARY KEY,
            order_no VARCHAR(30) UNIQUE NOT NULL,
            supplier_id INTEGER REFERENCES scm_suppliers(id),
            order_date DATE,
            expected_date DATE,
            total_amount DECIMAL(15,2) DEFAULT 0,
            paid_amount DECIMAL(15,2) DEFAULT 0,
            status VARCHAR(20) DEFAULT 'draft',
            approver_id INTEGER,
            approved_at TIMESTAMP,
            received_amount DECIMAL(15,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE pur_purchase_order_items (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES pur_purchase_orders(id),
            product_id INTEGER REFERENCES inv_products(id),
            quantity INTEGER NOT NULL,
            received_quantity INTEGER DEFAULT 0,
            unit_price DECIMAL(12,2),
            tax_rate DECIMAL(5,2) DEFAULT 0.13,
            amount DECIMAL(15,2),
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE pur_goods_receipts (
            id SERIAL PRIMARY KEY,
            receipt_no VARCHAR(30) UNIQUE NOT NULL,
            purchase_order_id INTEGER REFERENCES pur_purchase_orders(id),
            supplier_id INTEGER REFERENCES scm_suppliers(id),
            receipt_date DATE,
            total_amount DECIMAL(15,2) DEFAULT 0,
            status VARCHAR(20) DEFAULT 'draft',
            warehouse_id INTEGER REFERENCES inv_warehouses(id),
            received_by INTEGER,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE pur_goods_receipt_items (
            id SERIAL PRIMARY KEY,
            receipt_id INTEGER REFERENCES pur_goods_receipts(id),
            order_item_id INTEGER,
            product_id INTEGER REFERENCES inv_products(id),
            quantity INTEGER NOT NULL,
            qualified_quantity INTEGER,
            defective_quantity INTEGER DEFAULT 0,
            unit_cost DECIMAL(12,2),
            amount DECIMAL(15,2),
            location_id INTEGER REFERENCES inv_locations(id),
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,

        # ========== SAL 销售模块 ==========
        """
        CREATE TABLE sal_orders (
            id SERIAL PRIMARY KEY,
            order_no VARCHAR(30) UNIQUE NOT NULL,
            customer_id INTEGER REFERENCES crm_customers(id),
            order_date DATE,
            expected_date DATE,
            total_amount DECIMAL(15,2) DEFAULT 0,
            paid_amount DECIMAL(15,2) DEFAULT 0,
            discount_amount DECIMAL(15,2) DEFAULT 0,
            status VARCHAR(20) DEFAULT 'draft',
            sales_person_id INTEGER,
            approver_id INTEGER,
            approved_at TIMESTAMP,
            shipped_amount DECIMAL(15,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE sal_order_items (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES sal_orders(id),
            product_id INTEGER REFERENCES inv_products(id),
            quantity INTEGER NOT NULL,
            shipped_quantity INTEGER DEFAULT 0,
            unit_price DECIMAL(12,2),
            tax_rate DECIMAL(5,2) DEFAULT 0.13,
            discount_rate DECIMAL(5,2) DEFAULT 0,
            amount DECIMAL(15,2),
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE sal_deliveries (
            id SERIAL PRIMARY KEY,
            delivery_no VARCHAR(30) UNIQUE NOT NULL,
            order_id INTEGER REFERENCES sal_orders(id),
            customer_id INTEGER REFERENCES crm_customers(id),
            delivery_date DATE,
            total_amount DECIMAL(15,2) DEFAULT 0,
            status VARCHAR(20) DEFAULT 'draft',
            warehouse_id INTEGER REFERENCES inv_warehouses(id),
            shipped_by INTEGER,
            received_by VARCHAR(50),
            received_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE sal_delivery_items (
            id SERIAL PRIMARY KEY,
            delivery_id INTEGER REFERENCES sal_deliveries(id),
            order_item_id INTEGER,
            product_id INTEGER REFERENCES inv_products(id),
            quantity INTEGER NOT NULL,
            unit_price DECIMAL(12,2),
            amount DECIMAL(15,2),
            location_id INTEGER REFERENCES inv_locations(id),
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,

        # ========== FIN 财务模块 ==========
        """
        CREATE TABLE fin_accounts (
            id SERIAL PRIMARY KEY,
            account_code VARCHAR(20) UNIQUE NOT NULL,
            account_name VARCHAR(100) NOT NULL,
            account_type VARCHAR(20),
            parent_id INTEGER REFERENCES fin_accounts(id),
            level INTEGER DEFAULT 1,
            is_cash_account BOOLEAN DEFAULT FALSE,
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE fin_vouchers (
            id SERIAL PRIMARY KEY,
            voucher_no VARCHAR(30) UNIQUE NOT NULL,
            voucher_type VARCHAR(20),
            voucher_date DATE,
            total_debit DECIMAL(15,2) DEFAULT 0,
            total_credit DECIMAL(15,2) DEFAULT 0,
            status VARCHAR(20) DEFAULT 'draft',
            preparer_id INTEGER,
            approver_id INTEGER,
            approved_at TIMESTAMP,
            source_type VARCHAR(30),
            source_no VARCHAR(50),
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE fin_voucher_details (
            id SERIAL PRIMARY KEY,
            voucher_id INTEGER REFERENCES fin_vouchers(id),
            account_id INTEGER REFERENCES fin_accounts(id),
            debit DECIMAL(15,2) DEFAULT 0,
            credit DECIMAL(15,2) DEFAULT 0,
            summary VARCHAR(200),
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE fin_journal_entries (
            id SERIAL PRIMARY KEY,
            entry_no VARCHAR(30) UNIQUE NOT NULL,
            entry_date DATE,
            account_id INTEGER REFERENCES fin_accounts(id),
            debit DECIMAL(15,2) DEFAULT 0,
            credit DECIMAL(15,2) DEFAULT 0,
            voucher_id INTEGER,
            description TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,

        # ========== PRO 项目模块 ==========
        """
        CREATE TABLE pro_projects (
            id SERIAL PRIMARY KEY,
            project_code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(200) NOT NULL,
            project_type VARCHAR(30),
            customer_id INTEGER REFERENCES crm_customers(id),
            start_date DATE,
            end_date DATE,
            total_budget DECIMAL(15,2) DEFAULT 0,
            spent_amount DECIMAL(15,2) DEFAULT 0,
            status VARCHAR(20) DEFAULT 'planning',
            project_manager_id INTEGER,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE pro_project_tasks (
            id SERIAL PRIMARY KEY,
            project_id INTEGER REFERENCES pro_projects(id),
            task_no VARCHAR(30),
            name VARCHAR(200) NOT NULL,
            parent_task_id INTEGER,
            assigned_to INTEGER REFERENCES hr_employees(id),
            start_date DATE,
            end_date DATE,
            planned_hours DECIMAL(10,2) DEFAULT 0,
            actual_hours DECIMAL(10,2) DEFAULT 0,
            progress DECIMAL(5,2) DEFAULT 0,
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE pro_milestones (
            id SERIAL PRIMARY KEY,
            project_id INTEGER REFERENCES pro_projects(id),
            milestone_no VARCHAR(30),
            name VARCHAR(200) NOT NULL,
            planned_date DATE,
            actual_date DATE,
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,

        # ========== MRP 生产模块 ==========
        """
        CREATE TABLE mrp_production_orders (
            id SERIAL PRIMARY KEY,
            order_no VARCHAR(30) UNIQUE NOT NULL,
            product_id INTEGER REFERENCES inv_products(id),
            quantity INTEGER NOT NULL,
            order_date DATE,
            start_date DATE,
            end_date DATE,
            workstation VARCHAR(50),
            total_cost DECIMAL(15,2) DEFAULT 0,
            status VARCHAR(20) DEFAULT 'planned',
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE mrp_bom (
            id SERIAL PRIMARY KEY,
            product_id INTEGER REFERENCES inv_products(id),
            component_id INTEGER REFERENCES inv_products(id),
            quantity DECIMAL(10,2) NOT NULL,
           loss_rate DECIMAL(5,2) DEFAULT 0,
            level INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE mrp_work_orders (
            id SERIAL PRIMARY KEY,
            production_order_id INTEGER REFERENCES mrp_production_orders(id),
            work_order_no VARCHAR(30) UNIQUE NOT NULL,
            process_name VARCHAR(100),
            workstation VARCHAR(50),
            assigned_to INTEGER REFERENCES hr_employees(id),
            planned_start TIMESTAMP,
            planned_end TIMESTAMP,
            actual_start TIMESTAMP,
            actual_end TIMESTAMP,
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,

        # ========== SYS 系统模块 ==========
        """
        CREATE TABLE sys_users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(128),
            full_name VARCHAR(100),
            email VARCHAR(100),
            phone VARCHAR(20),
            employee_id INTEGER REFERENCES hr_employees(id),
            status VARCHAR(20) DEFAULT 'active',
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE sys_roles (
            id SERIAL PRIMARY KEY,
            code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(50) NOT NULL,
            description TEXT,
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE sys_user_roles (
            user_id INTEGER REFERENCES sys_users(id),
            role_id INTEGER REFERENCES sys_roles(id),
            PRIMARY KEY (user_id, role_id)
        )
        """,
        """
        CREATE TABLE sys_permissions (
            id SERIAL PRIMARY KEY,
            code VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            module VARCHAR(30),
            parent_id INTEGER REFERENCES sys_permissions(id),
            level INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE sys_role_permissions (
            role_id INTEGER REFERENCES sys_roles(id),
            permission_id INTEGER REFERENCES sys_permissions(id),
            PRIMARY KEY (role_id, permission_id)
        )
        """,
        """
        CREATE TABLE sys_audit_log (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            username VARCHAR(50),
            action VARCHAR(50),
            module VARCHAR(30),
            object_type VARCHAR(50),
            object_id VARCHAR(50),
            ip_address VARCHAR(50),
            user_agent TEXT,
            request_data TEXT,
            response_status VARCHAR(20),
            error_message TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,

        # ========== WMS 排班模块 ==========
        """
        CREATE TABLE wms_employee_schedules (
            id SERIAL PRIMARY KEY,
            employee_id INTEGER REFERENCES hr_employees(id),
            schedule_date DATE,
            shift_type VARCHAR(20),
            warehouse_id INTEGER REFERENCES inv_warehouses(id),
            work_start TIME,
            work_end TIME,
            status VARCHAR(20) DEFAULT 'scheduled',
            created_at TIMESTAMP DEFAULT NOW()
        )
        """
    ]

    for i, sql in enumerate(tables):
        sql = sql.strip()
        if sql:
            try:
                cur.execute(sql)
                table_name = sql.split('(')[0].replace('CREATE TABLE', '').strip()
                print(f"  ✓ 创建表: {table_name}")
            except Exception as e:
                print(f"  ✗ 创建表失败: {e}")

    cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
    table_count = cur.fetchone()[0]
    print(f">>> 总计创建 {table_count} 张表")

# ============= 数据生成函数 =============

def generate_hr_data(conn, cur):
    """生成 HR 模块数据"""
    print("\n>>> 生成 HR 模块数据...")

    # 部门 - 50个
    print("  生成 hr_departments...")
    dept_ids = []
    cur.execute("INSERT INTO hr_departments (code, name, parent_id, status) VALUES (%s, %s, NULL, 'active') RETURNING id",
                 ('DEPT001', '总公司'))
    root_id = cur.fetchone()[0]
    dept_ids.append(root_id)

    for i in range(2, 51):
        parent_id = random.choice(dept_ids) if random.random() > 0.3 and len(dept_ids) > 1 else root_id
        cur.execute("""
            INSERT INTO hr_departments (code, name, parent_id, status)
            VALUES (%s, %s, %s, 'active') RETURNING id
        """, (f'DEPT{i:03d}', f'{random.choice(["研发", "销售", "市场", "财务", "人事", "行政", "采购", "仓储", "生产", "质量"])}部{i}', parent_id))
        dept_ids.append(cur.fetchone()[0])
    conn.commit()

    # 岗位 - 每个部门2-5个
    print("  生成 hr_positions...")
    pos_ids = []
    for dept_id in dept_ids:
        for i in range(random.randint(2, 5)):
            cur.execute("""
                INSERT INTO hr_positions (code, name, department_id, level, status)
                VALUES (%s, %s, %s, %s, 'active') RETURNING id
            """, (f'POS{dept_id:04d}{i:02d}', random.choice(['经理', '主管', '专员', '助理', '工程师']), dept_id, random.randint(1, 5)))
            pos_ids.append(cur.fetchone()[0])
    conn.commit()

    # 员工 - 2万
    print("  生成 hr_employees (20,000 行)...")
    batch = []
    for i in range(DEFAULT_ROWS):
        batch.append((
            f'EMP{i+1:08d}', random_person_name(), random_id_card(),
            random.choice(['男', '女']), random_date(60, 18),
            random_phone(), f'emp{i+1}@company.com',
            random.choice(dept_ids), random.choice(pos_ids),
            random_date(10, 0), random_date(10, 5), random_date(15, 10),
            'active', random_bank_account(), f'SS{random_string(10).upper()}'
        ))
        if len(batch) >= BATCH_SIZE:
            cur.executemany("""
                INSERT INTO hr_employees (employee_code, name, id_card, gender, birth_date, phone, email,
                    department_id, position_id, hire_date, contract_start, contract_end, status, bank_account, social_security_no)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, batch)
            conn.commit()
            batch = []
            print(f"    {i+1:,} / {DEFAULT_ROWS:,}")
    if batch:
        cur.executemany("""
            INSERT INTO hr_employees (employee_code, name, id_card, gender, birth_date, phone, email,
                department_id, position_id, hire_date, contract_start, contract_end, status, bank_account, social_security_no)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, batch)
        conn.commit()

    # 获取员工ID列表用于后续
    cur.execute("SELECT id FROM hr_employees")
    emp_ids = [r[0] for r in cur.fetchall()]

    # 考勤 - 2万条（每人约1条记录）
    print("  生成 hr_attendance (20,000 行)...")
    batch = []
    for i in range(DEFAULT_ROWS):
        emp_id = random.choice(emp_ids)
        work_date = random_date(90, 0)
        status = random.choice(['normal', 'normal', 'normal', 'late', 'absent', 'leave'])
        cur.execute("""
            INSERT INTO hr_attendance (employee_id, work_date, check_in_time, check_out_time, status, overtime_hours)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (emp_id, work_date,
              f'{random.randint(7, 9)}:{random.randint(0, 59):02d}:00',
              f'{random.randint(17, 20)}:{random.randint(0, 59):02d}:00',
              status, random.choice([0, 0, 0, 1, 2, 3])))
        if (i + 1) % BATCH_SIZE == 0:
            conn.commit()
            print(f"    {i+1:,} / {DEFAULT_ROWS:,}")
    conn.commit()

    # 工资 - 2万条（每月约1600条×12月+历史）
    print("  生成 hr_salary (20,000 行)...")
    batch = []
    for i in range(DEFAULT_ROWS):
        base = random.randint(5000, 30000)
        bonus = random.choice([0, 0, 0, 1000, 2000, 5000])
        deduction = random.randint(500, 3000)
        net = base + bonus - deduction
        batch.append((
            random.choice(emp_ids), f'2024-{random.randint(1, 12):02d}',
            base, random.choice([0, 100, 200, 500]), bonus, deduction, net,
            random_datetime(12, 0) if random.random() > 0.3 else None, 'paid'
        ))
        if len(batch) >= BATCH_SIZE:
            cur.executemany("""
                INSERT INTO hr_salary (employee_id, salary_month, base_salary, overtime_pay, bonus, deduction, net_salary, paid_at, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, batch)
            conn.commit()
            batch = []
            print(f"    {i+1:,} / {DEFAULT_ROWS:,}")
    if batch:
        cur.executemany("""
            INSERT INTO hr_salary (employee_id, salary_month, base_salary, overtime_pay, bonus, deduction, net_salary, paid_at, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, batch)
        conn.commit()

    return emp_ids

def generate_crm_data(conn, cur):
    """生成 CRM 模块数据"""
    print("\n>>> 生成 CRM 模块数据...")

    # 客户 - 2万
    print("  生成 crm_customers (20,000 行)...")
    batch = []
    for i in range(DEFAULT_ROWS):
        batch.append((
            f'CUST{i+1:08d}', random_company_name(),
            random.choice([None, random_string(10)]),
            random.choice(['enterprise', 'individual', 'government']),
            random.choice(['IT', '制造', '金融', '医疗', '教育', '零售', '物流']),
            random.choice(['A', 'B', 'C', 'D']), random.randint(100000, 5000000),
            random_person_name(), random_phone(), f'cust{i+1}@example.com',
            random_address(), 'active'
        ))
        if len(batch) >= BATCH_SIZE:
            cur.executemany("""
                INSERT INTO crm_customers (customer_code, name, short_name, customer_type, industry, credit_rating,
                    credit_limit, contact_person, contact_phone, contact_email, address, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, batch)
            conn.commit()
            batch = []
            print(f"    {i+1:,} / {DEFAULT_ROWS:,}")
    if batch:
        cur.executemany("""
            INSERT INTO crm_customers (customer_code, name, short_name, customer_type, industry, credit_rating,
                credit_limit, contact_person, contact_phone, contact_email, address, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, batch)
        conn.commit()

    cur.execute("SELECT id FROM crm_customers")
    customer_ids = [r[0] for r in cur.fetchall()]

    # 联系人 - 平均每客户2个
    print("  生成 crm_contacts (约 40,000 行)...")
    batch = []
    for i in range(DEFAULT_ROWS * 2):
        cur.execute("""
            INSERT INTO crm_contacts (customer_id, name, gender, phone, email, position, is_primary, birthday)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (random.choice(customer_ids), random_person_name(),
              random.choice(['男', '女']), random_phone(),
              f'contact{i}@example.com', random.choice(['经理', '采购', '技术', '财务']),
              i % 5 == 0, random_date(60, 18)))
        if (i + 1) % BATCH_SIZE == 0:
            conn.commit()
            print(f"    {i+1:,} 行")
    conn.commit()

    # 客户地址
    print("  生成 crm_customer_addresses...")
    for i in range(DEFAULT_ROWS):
        cur.execute("""
            INSERT INTO crm_customer_addresses (customer_id, address_type, contact_name, contact_phone, address, is_default)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (random.choice(customer_ids), random.choice(['billing', 'shipping']),
              random_person_name(), random_phone(), random_address(), i % 3 == 0))
    conn.commit()

    return customer_ids

def generate_scm_data(conn, cur):
    """生成 SCM 供应商数据"""
    print("\n>>> 生成 SCM 模块数据...")

    # 供应商 - 2万
    print("  生成 scm_suppliers (20,000 行)...")
    batch = []
    for i in range(DEFAULT_ROWS):
        batch.append((
            f'SUP{i+1:08d}', random_company_name(),
            random.choice([None, random_string(10)]),
            random.choice(['manufacturer', 'distributor', 'trader']),
            random.choice(['IT', '制造', '化工', '原材料', '设备']),
            random_person_name(), random_phone(), f'sup{i+1}@example.com',
            random_address(), random_bank_account(), f'TAX{random_string(15).upper()}',
            'active'
        ))
        if len(batch) >= BATCH_SIZE:
            cur.executemany("""
                INSERT INTO scm_suppliers (supplier_code, name, short_name, supplier_type, industry,
                    contact_person, contact_phone, contact_email, address, bank_account, tax_no, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, batch)
            conn.commit()
            batch = []
            print(f"    {i+1:,} / {DEFAULT_ROWS:,}")
    if batch:
        cur.executemany("""
            INSERT INTO scm_suppliers (supplier_code, name, short_name, supplier_type, industry,
                contact_person, contact_phone, contact_email, address, bank_account, tax_no, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, batch)
        conn.commit()

    cur.execute("SELECT id FROM scm_suppliers")
    supplier_ids = [r[0] for r in cur.fetchall()]

    # 供应商联系人
    print("  生成 scm_supplier_contacts...")
    for i in range(DEFAULT_ROWS):
        cur.execute("""
            INSERT INTO scm_supplier_contacts (supplier_id, name, gender, phone, email, position, is_primary)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (random.choice(supplier_ids), random_person_name(),
              random.choice(['男', '女']), random_phone(),
              f'supcontact{i}@example.com', random.choice(['销售', '技术', '采购']),
              i % 3 == 0))
    conn.commit()

    return supplier_ids

def generate_inv_data(conn, cur):
    """生成 INV 库存模块数据"""
    print("\n>>> 生成 INV 库存模块数据...")

    # 仓库 - 20个
    print("  生成 inv_warehouses...")
    warehouse_ids = []
    for i in range(20):
        cur.execute("""
            INSERT INTO inv_warehouses (code, name, warehouse_type, address, status)
            VALUES (%s, %s, %s, %s, 'active') RETURNING id
        """, (f'WH{i+1:03d}', f'{random.choice(["中心仓", "区域仓", "配送中心"])}{i+1}',
              random.choice(['main', 'branch', 'transit']), random_address()))
        warehouse_ids.append(cur.fetchone()[0])
    conn.commit()

    # 库位 - 每个仓库100个 = 2000个
    print("  生成 inv_locations (2,000 行)...")
    loc_ids = []
    for wh_id in warehouse_ids:
        for i in range(100):
            cur.execute("""
                INSERT INTO inv_locations (warehouse_id, location_code, zone, aisle, rack, shelf, bin, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'available') RETURNING id
            """, (wh_id, f'LOC{wh_id:02d}{i:04d}',
                  random.choice(['A', 'B', 'C', 'D']), f'{random.randint(1, 20):02d}',
                  f'{random.randint(1, 10):02d}', f'{random.randint(1, 5):02d}',
                  f'{random.randint(1, 20):02d}'))
            loc_ids.append(cur.fetchone()[0])
    conn.commit()

    # 产品分类 - 树形结构
    print("  生成 inv_product_categories...")
    cat_ids = []
    for i in range(30):
        parent_id = random.choice(cat_ids) if cat_ids and random.random() > 0.5 else None
        cur.execute("""
            INSERT INTO inv_product_categories (code, name, parent_id, level)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (f'CAT{i+1:04d}', random.choice(['电子', '机械', '化工', '食品', '医药', '建材', '服装']),
              parent_id, 1 if parent_id is None else 2))
        cat_ids.append(cur.fetchone()[0])
    conn.commit()

    # 产品 - 2万
    print("  生成 inv_products (20,000 行)...")
    batch = []
    for i in range(DEFAULT_ROWS):
        batch.append((
            f'PRD{i+1:08d}', random_product_name(),
            random.choice(cat_ids), f'Spec-{random_string(8)}',
            random.choice(['个', '台', '件', '箱', '米', '公斤']),
            random.uniform(10, 1000), random.uniform(50, 5000),
            random.randint(10, 100), random.randint(5, 50),
            random.uniform(0.1, 50), 'active'
        ))
        if len(batch) >= BATCH_SIZE:
            cur.executemany("""
                INSERT INTO inv_products (product_code, name, category_id, spec, unit, cost_price, sale_price,
                    safety_stock, reorder_point, weight, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, batch)
            conn.commit()
            batch = []
            print(f"    {i+1:,} / {DEFAULT_ROWS:,}")
    if batch:
        cur.executemany("""
            INSERT INTO inv_products (product_code, name, category_id, spec, unit, cost_price, sale_price,
                safety_stock, reorder_point, weight, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, batch)
        conn.commit()

    cur.execute("SELECT id FROM inv_products")
    product_ids = [r[0] for r in cur.fetchall()]

    # 库存 - 2万条
    print("  生成 inv_inventory (20,000 行)...")
    batch = []
    for i in range(DEFAULT_ROWS):
        qty = random.randint(0, 10000)
        batch.append((
            random.choice(product_ids), random.choice(warehouse_ids),
            random.choice(loc_ids), qty, qty, 0,
            random.uniform(10, 1000), random_datetime(30, 0),
            random_datetime(60, 30)
        ))
        if len(batch) >= BATCH_SIZE:
            cur.executemany("""
                INSERT INTO inv_inventory (product_id, warehouse_id, location_id, quantity, available_quantity,
                    reserved_quantity, unit_cost, last_in_date, last_out_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, batch)
            conn.commit()
            batch = []
            print(f"    {i+1:,} / {DEFAULT_ROWS:,}")
    if batch:
        cur.executemany("""
            INSERT INTO inv_inventory (product_id, warehouse_id, location_id, quantity, available_quantity,
                reserved_quantity, unit_cost, last_in_date, last_out_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, batch)
        conn.commit()

    # 库存事务 - 2万
    print("  生成 inv_inventory_transactions (20,000 行)...")
    tx_types = ['purchase_in', 'sale_out', 'transfer', 'adjust', 'return']
    batch = []
    for i in range(DEFAULT_ROWS):
        batch.append((
            f'TX{random_string(12).upper()}', random.choice(product_ids),
            random.choice(warehouse_ids), random.choice(loc_ids),
            random.choice(tx_types), random.randint(-1000, 1000),
            random.randint(0, 10000), random.randint(0, 10000),
            f'REF{random_string(10).upper()}', None,
            f'Transaction {i}'
        ))
        if len(batch) >= BATCH_SIZE:
            cur.executemany("""
                INSERT INTO inv_inventory_transactions (transaction_no, product_id, warehouse_id, location_id,
                    transaction_type, quantity, before_quantity, after_quantity, reference_no, operator_id, remarks)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, batch)
            conn.commit()
            batch = []
            print(f"    {i+1:,} / {DEFAULT_ROWS:,}")
    if batch:
        cur.executemany("""
            INSERT INTO inv_inventory_transactions (transaction_no, product_id, warehouse_id, location_id,
                transaction_type, quantity, before_quantity, after_quantity, reference_no, operator_id, remarks)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, batch)
        conn.commit()

    return warehouse_ids, loc_ids, product_ids

def generate_pur_data(conn, cur, supplier_ids, product_ids):
    """生成采购模块数据"""
    print("\n>>> 生成 PUR 采购模块数据...")

    # 采购订单 - 2万
    print("  生成 pur_purchase_orders (20,000 行)...")
    batch = []
    for i in range(DEFAULT_ROWS):
        total = random.uniform(10000, 500000)
        batch.append((
            f'PO{random_string(8).upper()}', random.choice(supplier_ids),
            random_date(180, 0), random_date(90, 30),
            total, random.uniform(0, total),
            random.choice(['draft', 'approved', 'partial', 'received', 'closed']),
            None, random_datetime(90, 0), random.uniform(0, total)
        ))
        if len(batch) >= BATCH_SIZE:
            cur.executemany("""
                INSERT INTO pur_purchase_orders (order_no, supplier_id, order_date, expected_date, total_amount,
                    paid_amount, status, approver_id, approved_at, received_amount)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, batch)
            conn.commit()
            batch = []
            print(f"    {i+1:,} / {DEFAULT_ROWS:,}")
    if batch:
        cur.executemany("""
            INSERT INTO pur_purchase_orders (order_no, supplier_id, order_date, expected_date, total_amount,
                paid_amount, status, approver_id, approved_at, received_amount)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, batch)
        conn.commit()

    cur.execute("SELECT id FROM pur_purchase_orders")
    po_ids = [r[0] for r in cur.fetchall()]

    # 采购订单明细 - 每订单约3条
    print("  生成 pur_purchase_order_items (约 60,000 行)...")
    for i in range(DEFAULT_ROWS * 3):
        qty = random.randint(10, 500)
        price = random.uniform(10, 500)
        cur.execute("""
            INSERT INTO pur_purchase_order_items (order_id, product_id, quantity, unit_price, amount)
            VALUES (%s, %s, %s, %s, %s)
        """, (random.choice(po_ids), random.choice(product_ids), qty, price, qty * price))
        if (i + 1) % BATCH_SIZE == 0:
            conn.commit()
            print(f"    {i+1:,} 行")
    conn.commit()

    # 到货单 - 2万
    print("  生成 pur_goods_receipts (20,000 行)...")
    batch = []
    for i in range(DEFAULT_ROWS):
        batch.append((
            f'GR{random_string(8).upper()}', random.choice(po_ids),
            random.choice(supplier_ids), random_date(90, 0),
            random.uniform(10000, 300000), random.choice(['draft', 'confirmed', 'closed']),
            random.choice([1, 2, 3, 4, 5]), None
        ))
        if len(batch) >= BATCH_SIZE:
            cur.executemany("""
                INSERT INTO pur_goods_receipts (receipt_no, purchase_order_id, supplier_id, receipt_date,
                    total_amount, status, warehouse_id, received_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, batch)
            conn.commit()
            batch = []
            print(f"    {i+1:,} / {DEFAULT_ROWS:,}")
    if batch:
        cur.executemany("""
            INSERT INTO pur_goods_receipts (receipt_no, purchase_order_id, supplier_id, receipt_date,
                total_amount, status, warehouse_id, received_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, batch)
        conn.commit()

def generate_sal_data(conn, cur, customer_ids, product_ids, emp_ids):
    """生成销售模块数据"""
    print("\n>>> 生成 SAL 销售模块数据...")

    # 销售订单 - 2万
    print("  生成 sal_orders (20,000 行)...")
    batch = []
    for i in range(DEFAULT_ROWS):
        total = random.uniform(10000, 500000)
        batch.append((
            f'SO{random_string(8).upper()}', random.choice(customer_ids),
            random_date(180, 0), random_date(90, 30),
            total, random.uniform(0, total), random.uniform(0, 10000),
            random.choice(['draft', 'approved', 'partial', 'shipped', 'closed']),
            None, None, random_datetime(90, 0), random.uniform(0, total)
        ))
        if len(batch) >= BATCH_SIZE:
            cur.executemany("""
                INSERT INTO sal_orders (order_no, customer_id, order_date, expected_date, total_amount,
                    paid_amount, discount_amount, status, sales_person_id, approver_id, approved_at, shipped_amount)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, batch)
            conn.commit()
            batch = []
            print(f"    {i+1:,} / {DEFAULT_ROWS:,}")
    if batch:
        cur.executemany("""
            INSERT INTO sal_orders (order_no, customer_id, order_date, expected_date, total_amount,
                paid_amount, discount_amount, status, sales_person_id, approver_id, approved_at, shipped_amount)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, batch)
        conn.commit()

    cur.execute("SELECT id FROM sal_orders")
    so_ids = [r[0] for r in cur.fetchall()]

    # 销售订单明细
    print("  生成 sal_order_items (约 60,000 行)...")
    for i in range(DEFAULT_ROWS * 3):
        qty = random.randint(1, 100)
        price = random.uniform(10, 1000)
        cur.execute("""
            INSERT INTO sal_order_items (order_id, product_id, quantity, unit_price, amount)
            VALUES (%s, %s, %s, %s, %s)
        """, (random.choice(so_ids), random.choice(product_ids), qty, price, qty * price))
        if (i + 1) % BATCH_SIZE == 0:
            conn.commit()
            print(f"    {i+1:,} 行")
    conn.commit()

    # 发货单
    print("  生成 sal_deliveries (20,000 行)...")
    batch = []
    for i in range(DEFAULT_ROWS):
        batch.append((
            f'DLV{random_string(8).upper()}', random.choice(so_ids),
            random.choice(customer_ids), random_date(90, 0),
            random.uniform(5000, 200000), random.choice(['draft', 'shipped', 'delivered']),
            random.choice([1, 2, 3, 4, 5]), random.choice(emp_ids),
            random_datetime(60, 0) if random.random() > 0.5 else None
        ))
        if len(batch) >= BATCH_SIZE:
            cur.executemany("""
                INSERT INTO sal_deliveries (delivery_no, order_id, customer_id, delivery_date, total_amount,
                    status, warehouse_id, shipped_by, received_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, batch)
            conn.commit()
            batch = []
            print(f"    {i+1:,} / {DEFAULT_ROWS:,}")
    if batch:
        cur.executemany("""
            INSERT INTO sal_deliveries (delivery_no, order_id, customer_id, delivery_date, total_amount,
                status, warehouse_id, shipped_by, received_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, batch)
        conn.commit()

def generate_fin_data(conn, cur):
    """生成财务模块数据"""
    print("\n>>> 生成 FIN 财务模块数据...")

    # 财务科目 - 100个
    print("  生成 fin_accounts...")
    account_ids = []
    for i in range(100):
        parent_id = random.choice(account_ids) if account_ids and random.random() > 0.7 else None
        cur.execute("""
            INSERT INTO fin_accounts (account_code, account_name, account_type, parent_id, is_cash_account)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (f'{random.randint(1000, 9999)}',
              random.choice(['银行存款', '应收账款', '应付账款', '主营业务收入', '主营业务成本',
                           '管理费用', '销售费用', '固定资产', '无形资产', '短期借款']),
              random.choice(['asset', 'liability', 'equity', 'revenue', 'expense']),
              parent_id, random.choice([True, False])))
        account_ids.append(cur.fetchone()[0])
    conn.commit()

    # 凭证 - 2万
    print("  生成 fin_vouchers (20,000 行)...")
    batch = []
    for i in range(DEFAULT_ROWS):
        total = random.uniform(1000, 100000)
        batch.append((
            f'V{random_string(10).upper()}', random.choice(['receipt', 'payment', 'transfer', 'general']),
            random_date(365, 0), total, total,
            random.choice(['draft', 'approved', 'posted']),
            None, None, random_datetime(365, 0),
            random.choice(['sales', 'purchase', 'expense', 'payroll', 'other']),
            f'REF{random_string(8).upper()}'
        ))
        if len(batch) >= BATCH_SIZE:
            cur.executemany("""
                INSERT INTO fin_vouchers (voucher_no, voucher_type, voucher_date, total_debit, total_credit,
                    status, preparer_id, approver_id, approved_at, source_type, source_no)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, batch)
            conn.commit()
            batch = []
            print(f"    {i+1:,} / {DEFAULT_ROWS:,}")
    if batch:
        cur.executemany("""
            INSERT INTO fin_vouchers (voucher_no, voucher_type, voucher_date, total_debit, total_credit,
                status, preparer_id, approver_id, approved_at, source_type, source_no)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, batch)
        conn.commit()

    cur.execute("SELECT id FROM fin_vouchers")
    voucher_ids = [r[0] for r in cur.fetchall()]

    # 凭证分录 - 每凭证约2条
    print("  生成 fin_voucher_details (约 40,000 行)...")
    for i in range(DEFAULT_ROWS * 2):
        amt = random.uniform(100, 50000)
        batch.append((
            random.choice(voucher_ids), random.choice(account_ids),
            amt, 0, f'Summary {i}'
        ))
        batch.append((
            random.choice(voucher_ids), random.choice(account_ids),
            0, amt, f'Summary {i}'
        ))
        if len(batch) >= BATCH_SIZE:
            cur.executemany("""
                INSERT INTO fin_voucher_details (voucher_id, account_id, debit, credit, summary)
                VALUES (%s, %s, %s, %s, %s)
            """, batch)
            conn.commit()
            batch = []
            print(f"    {i+1:,} 行")
    conn.commit()

    # 日记账
    print("  生成 fin_journal_entries (20,000 行)...")
    batch = []
    for i in range(DEFAULT_ROWS):
        amt = random.uniform(100, 50000)
        batch.append((
            f'JE{random_string(10).upper()}', random_date(365, 0),
            random.choice(account_ids), amt, 0,
            random.choice(voucher_ids), f'Journal entry {i}'
        ))
        if len(batch) >= BATCH_SIZE:
            cur.executemany("""
                INSERT INTO fin_journal_entries (entry_no, entry_date, account_id, debit, credit, voucher_id, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, batch)
            conn.commit()
            batch = []
            print(f"    {i+1:,} / {DEFAULT_ROWS:,}")
    if batch:
        cur.executemany("""
            INSERT INTO fin_journal_entries (entry_no, entry_date, account_id, debit, credit, voucher_id, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, batch)
        conn.commit()

def generate_pro_data(conn, cur, customer_ids, emp_ids):
    """生成项目模块数据"""
    print("\n>>> 生成 PRO 项目模块数据...")

    # 项目 - 500个
    print("  生成 pro_projects (500 行)...")
    project_ids = []
    for i in range(500):
        cur.execute("""
            INSERT INTO pro_projects (project_code, name, project_type, customer_id, start_date, end_date,
                total_budget, spent_amount, status, project_manager_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (f'PRJ{i+1:05d}', f'{random.choice(["系统集成", "软件开发", "咨询服务", "设备改造"])}项目{i+1}',
              random.choice(['software', 'consulting', 'integration', 'outsourcing']),
              random.choice(customer_ids), random_date(365, 60), random_date(60, 0),
              random.uniform(100000, 5000000), random.uniform(0, 1000000),
              random.choice(['planning', 'in_progress', 'completed', 'suspended']),
              random.choice(emp_ids)))
        project_ids.append(cur.fetchone()[0])
    conn.commit()

    # 项目任务
    print("  生成 pro_project_tasks (约 20,000 行)...")
    for i in range(DEFAULT_ROWS):
        cur.execute("""
            INSERT INTO pro_project_tasks (project_id, task_no, name, parent_task_id, assigned_to,
                start_date, end_date, planned_hours, actual_hours, progress, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (random.choice(project_ids), f'T{i+1:06d}', f'任务{i+1}',
              None, random.choice(emp_ids),
              random_date(180, 30), random_date(30, 0),
              random.uniform(8, 200), random.uniform(0, 200),
              random.uniform(0, 100), random.choice(['pending', 'in_progress', 'completed'])))
        if (i + 1) % BATCH_SIZE == 0:
            conn.commit()
            print(f"    {i+1:,} / {DEFAULT_ROWS:,}")
    conn.commit()

    # 项目里程碑
    print("  生成 pro_milestones (2,000 行)...")
    for i in range(DEFAULT_ROWS // 10):
        cur.execute("""
            INSERT INTO pro_milestones (project_id, milestone_no, name, planned_date, actual_date, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (random.choice(project_ids), f'M{i+1:04d}', f'{random.choice(["设计", "开发", "测试", "上线", "验收"])}里程碑',
              random_date(180, 30), random_date(30, 0) if random.random() > 0.5 else None,
              random.choice(['pending', 'achieved', 'delayed'])))
    conn.commit()

def generate_mrp_data(conn, cur, product_ids, emp_ids):
    """生成生产模块数据"""
    print("\n>>> 生成 MRP 生产模块数据...")

    # 生产工单 - 500个
    print("  生成 mrp_production_orders (500 行)...")
    po_ids = []
    for i in range(500):
        cur.execute("""
            INSERT INTO mrp_production_orders (order_no, product_id, quantity, order_date, start_date, end_date,
                workstation, total_cost, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (f'MO{random_string(8).upper()}', random.choice(product_ids),
              random.randint(10, 500), random_date(90, 0), random_date(60, 0),
              random_date(30, 0), random.choice(['车间A', '车间B', '车间C']),
              random.uniform(10000, 200000), random.choice(['planned', 'in_progress', 'completed'])))
        po_ids.append(cur.fetchone()[0])
    conn.commit()

    # BOM - 物料清单
    print("  生成 mrp_bom (2,000 行)...")
    for i in range(DEFAULT_ROWS // 10):
        cur.execute("""
            INSERT INTO mrp_bom (product_id, component_id, quantity, loss_rate, level)
            VALUES (%s, %s, %s, %s, %s)
        """, (random.choice(product_ids), random.choice(product_ids),
              random.uniform(1, 10), random.choice([0, 0.01, 0.02, 0.05]), random.randint(1, 3)))
    conn.commit()

    # 工序
    print("  生成 mrp_work_orders (2,000 行)...")
    for i in range(DEFAULT_ROWS // 10):
        cur.execute("""
            INSERT INTO mrp_work_orders (production_order_id, work_order_no, process_name, workstation,
                assigned_to, planned_start, planned_end, actual_start, actual_end, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (random.choice(po_ids), f'WO{random_string(8).upper()}',
              random.choice(['装配', '焊接', '涂装', '检测', '包装']),
              random.choice(['车间A', '车间B', '车间C']),
              random.choice(emp_ids),
              random_datetime(60, 30), random_datetime(30, 0),
              random_datetime(30, 15) if random.random() > 0.3 else None,
              random_datetime(15, 0) if random.random() > 0.5 else None,
              random.choice(['pending', 'in_progress', 'completed'])))
    conn.commit()

def generate_sys_data(conn, cur, emp_ids):
    """生成系统模块数据"""
    print("\n>>> 生成 SYS 系统模块数据...")

    # 用户 - 2000个
    print("  生成 sys_users (2,000 行)...")
    user_ids = []
    for i in range(2000):
        cur.execute("""
            INSERT INTO sys_users (username, password_hash, full_name, email, phone, employee_id, status, last_login)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (f'user{i+1:05d}', random_string(64), random_person_name(),
              f'user{i+1}@system.com', random_phone(),
              random.choice(emp_ids), 'active', random_datetime(30, 0)))
        user_ids.append(cur.fetchone()[0])
    conn.commit()

    # 角色 - 20个
    print("  生成 sys_roles...")
    role_ids = []
    for i in range(20):
        cur.execute("""
            INSERT INTO sys_roles (code, name, description, status)
            VALUES (%s, %s, %s, 'active') RETURNING id
        """, (f'ROLE{i+1:03d}',
              random.choice(['管理员', '经理', '主管', '专员', '助理', '审计员']),
              f'系统角色{i+1}'))
        role_ids.append(cur.fetchone()[0])
    conn.commit()

    # 用户角色
    print("  生成 sys_user_roles...")
    for user_id in user_ids:
        cur.execute("""
            INSERT INTO sys_user_roles (user_id, role_id)
            VALUES (%s, %s)
        """, (user_id, random.choice(role_ids)))
    conn.commit()

    # 权限 - 100个
    print("  生成 sys_permissions...")
    perm_ids = []
    for i in range(100):
        parent_id = random.choice(perm_ids) if perm_ids and random.random() > 0.6 else None
        cur.execute("""
            INSERT INTO sys_permissions (code, name, module, parent_id, level)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (f'PERM{i+1:04d}', f'权限{i+1}',
              random.choice(['hr', 'crm', 'inv', 'pur', 'sal', 'fin', 'pro', 'sys']),
              parent_id, 1 if parent_id is None else 2))
        perm_ids.append(cur.fetchone()[0])
    conn.commit()

    # 角色权限
    print("  生成 sys_role_permissions...")
    for role_id in role_ids:
        for perm_id in random.sample(perm_ids, random.randint(5, 20)):
            cur.execute("""
                INSERT INTO sys_role_permissions (role_id, permission_id)
                VALUES (%s, %s)
            """, (role_id, perm_id))
    conn.commit()

    # 审计日志 - 2万
    print("  生成 sys_audit_log (20,000 行)...")
    batch = []
    for i in range(DEFAULT_ROWS):
        batch.append((
            random.choice(user_ids), f'user{random.randint(1, 2000):05d}',
            random.choice(['login', 'logout', 'create', 'update', 'delete', 'query']),
            random.choice(['hr', 'crm', 'inv', 'pur', 'sal', 'fin', 'pro', 'sys']),
            random.choice(['employee', 'customer', 'order', 'product', 'voucher']),
            str(random.randint(1, 10000)),
            f'192.168.{random.randint(1, 255)}.{random.randint(1, 255)}',
            'Mozilla/5.0', None,
            random.choice(['success', 'failed']),
            None if random.random() > 0.1 else 'Error message'
        ))
        if len(batch) >= BATCH_SIZE:
            cur.executemany("""
                INSERT INTO sys_audit_log (user_id, username, action, module, object_type, object_id,
                    ip_address, user_agent, request_data, response_status, error_message)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, batch)
            conn.commit()
            batch = []
            print(f"    {i+1:,} / {DEFAULT_ROWS:,}")
    if batch:
        cur.executemany("""
            INSERT INTO sys_audit_log (user_id, username, action, module, object_type, object_id,
                ip_address, user_agent, request_data, response_status, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, batch)
        conn.commit()

def generate_wms_data(conn, cur, emp_ids, warehouse_ids):
    """生成排班模块数据"""
    print("\n>>> 生成 WMS 排班模块数据...")

    print("  生成 wms_employee_schedules (20,000 行)...")
    batch = []
    for i in range(DEFAULT_ROWS):
        batch.append((
            random.choice(emp_ids), random_date(30, 0),
            random.choice(['day', 'night', 'swing']),
            random.choice(warehouse_ids),
            f'{random.choice([8, 9])}:{random.randint(0, 59):02d}:00',
            f'{random.choice([17, 18, 19])}:{random.randint(0, 59):02d}:00',
            random.choice(['scheduled', 'confirmed', 'completed'])
        ))
        if len(batch) >= BATCH_SIZE:
            cur.executemany("""
                INSERT INTO wms_employee_schedules (employee_id, schedule_date, shift_type, warehouse_id,
                    work_start, work_end, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, batch)
            conn.commit()
            batch = []
            print(f"    {i+1:,} / {DEFAULT_ROWS:,}")
    if batch:
        cur.executemany("""
            INSERT INTO wms_employee_schedules (employee_id, schedule_date, shift_type, warehouse_id,
                work_start, work_end, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, batch)
        conn.commit()

def main():
    start_time = time.time()

    # 连接数据库并创建表
    conn, cur = setup_database()

    # 创建表结构
    create_tables(cur)
    conn.commit()

    # 生成数据
    emp_ids = generate_hr_data(conn, cur)
    customer_ids = generate_crm_data(conn, cur)
    supplier_ids = generate_scm_data(conn, cur)
    warehouse_ids, loc_ids, product_ids = generate_inv_data(conn, cur)

    # 采购、销售、财务、项目、生产、系统、排班需要其他模块的数据
    generate_pur_data(conn, cur, supplier_ids, product_ids)
    generate_sal_data(conn, cur, customer_ids, product_ids, emp_ids)
    generate_fin_data(conn, cur)
    generate_pro_data(conn, cur, customer_ids, emp_ids)
    generate_mrp_data(conn, cur, product_ids, emp_ids)
    generate_sys_data(conn, cur, emp_ids)
    generate_wms_data(conn, cur, emp_ids, warehouse_ids)

    # 创建索引
    print("\n>>> 创建索引...")
    indexes = [
        "CREATE INDEX idx_employees_dept ON hr_employees(department_id)",
        "CREATE INDEX idx_employees_pos ON hr_employees(position_id)",
        "CREATE INDEX idx_attendance_emp ON hr_attendance(employee_id)",
        "CREATE INDEX idx_attendance_date ON hr_attendance(work_date)",
        "CREATE INDEX idx_salary_emp ON hr_salary(employee_id)",
        "CREATE INDEX idx_customers_name ON crm_customers(name)",
        "CREATE INDEX idx_orders_customer ON sal_orders(customer_id)",
        "CREATE INDEX idx_orders_date ON sal_orders(order_date)",
        "CREATE INDEX idx_order_items_order ON sal_order_items(order_id)",
        "CREATE INDEX idx_deliveries_order ON sal_deliveries(order_id)",
        "CREATE INDEX idx_pur_orders_supplier ON pur_purchase_orders(supplier_id)",
        "CREATE INDEX idx_pur_receipts_order ON pur_goods_receipts(purchase_order_id)",
        "CREATE INDEX idx_inventory_product ON inv_inventory(product_id)",
        "CREATE INDEX idx_inventory_wh ON inv_inventory(warehouse_id)",
        "CREATE INDEX idx_products_code ON inv_products(product_code)",
        "CREATE INDEX idx_transactions_product ON inv_inventory_transactions(product_id)",
        "CREATE INDEX idx_transactions_date ON inv_inventory_transactions(created_at)",
        "CREATE INDEX idx_vouchers_date ON fin_vouchers(voucher_date)",
        "CREATE INDEX idx_voucher_details_voucher ON fin_voucher_details(voucher_id)",
        "CREATE INDEX idx_journal_date ON fin_journal_entries(entry_date)",
        "CREATE INDEX idx_projects_customer ON pro_projects(customer_id)",
        "CREATE INDEX idx_tasks_project ON pro_project_tasks(project_id)",
        "CREATE INDEX idx_work_orders_prod ON mrp_work_orders(production_order_id)",
        "CREATE INDEX idx_users_emp ON sys_users(employee_id)",
        "CREATE INDEX idx_audit_user ON sys_audit_log(user_id)",
        "CREATE INDEX idx_audit_date ON sys_audit_log(created_at)",
        "CREATE INDEX idx_schedules_emp ON wms_employee_schedules(employee_id)",
        "CREATE INDEX idx_schedules_date ON wms_employee_schedules(schedule_date)",
    ]

    for idx in indexes:
        try:
            cur.execute(idx)
            print(f"  ✓ {idx.split(' ')[2]}")
        except Exception as e:
            pass
    conn.commit()

    # 统计
    print("\n>>> 数据统计...")
    cur.execute("""
        SELECT table_name, pg_class.reltuples AS approximate_count
        FROM information_schema.tables
        JOIN pg_class ON information_schema.tables.table_name = pg_class.relname
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY pg_class.reltuples DESC
    """)
    total_rows = 0
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]:,.0f} 行")
        total_rows += row[1]

    print(f"\n>>> 总计: {total_rows:,.0f} 行数据")

    # 表大小
    cur.execute("""
        SELECT pg_size_pretty(pg_database_size(%s))
    """, (DB_CONFIG["database"],))
    db_size = cur.fetchone()[0]
    print(f">>> 数据库大小: {db_size}")

    cur.close()
    conn.close()

    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"✓ ERP 仿真数据生成完成!")
    print(f"✓ 耗时: {elapsed/60:.1f} 分钟")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
