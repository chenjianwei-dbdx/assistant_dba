#!/usr/bin/env python3
"""
数据库高频操作模拟脚本
模拟多个工作人员并发执行查询、删除、更新操作
用于产生慢查询、死锁等可观测问题
"""
import psycopg2
import random
import string
import time
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import signal
import sys

# 连接配置
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "database": "erp_simulation",
    "user": "cjwdsg"
}

# 模拟参数
NUM_WORKERS = 10  # 并发工作线程数
OPERATIONS_PER_WORKER = 100  # 每个worker执行的操作次数
RUN_DURATION = 300  # 运行时间（秒），0表示无限

# 全局停止标志
stop_flag = threading.Event()

def signal_handler(signum, frame):
    """处理 Ctrl+C """
    print("\n>>> 收到停止信号，正在停止...")
    stop_flag.set()
    sys.exit(0)

class DBOperations:
    """数据库操作模拟器"""

    def __init__(self, worker_id):
        self.worker_id = worker_id
        self.conn = None
        self.cur = None
        self.stats = {
            'queries': 0,
            'updates': 0,
            'deletes': 0,
            'errors': 0,
            'slow_queries': 0
        }

    def connect(self):
        """建立数据库连接"""
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.conn.autocommit = False
        self.cur = self.conn.cursor()

    def close(self):
        """关闭连接"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

    def log_operation(self, op_type, duration, queryPreview):
        """记录操作日志"""
        slow = duration > 1.0  # 超过1秒视为慢查询
        if slow:
            self.stats['slow_queries'] += 1
            print(f"  [Worker-{self.worker_id}] ⚠️ SLOW {op_type} ({duration:.2f}s): {queryPreview[:80]}...")

    # ========== 查询操作 ==========

    def execute_query(self, query, op_name="SELECT"):
        """执行查询并记录统计"""
        start = time.time()
        try:
            self.cur.execute(query)
            result = self.cur.fetchall()
            duration = time.time() - start
            self.stats['queries'] += 1
            self.log_operation(op_name, duration, query)
            return result
        except Exception as e:
            self.stats['errors'] += 1
            print(f"  [Worker-{self.worker_id}] ❌ {op_name} ERROR: {e}")
            return None

    def query_employees_with_dept(self):
        """查询员工及其部门信息（多表JOIN）"""
        query = f"""
            SELECT e.id, e.name, e.employee_code, d.name as dept_name, p.name as position_name
            FROM hr_employees e
            LEFT JOIN hr_departments d ON e.department_id = d.id
            LEFT JOIN hr_positions p ON e.position_id = p.id
            WHERE e.status = 'active'
            ORDER BY e.id
            LIMIT {random.randint(100, 500)}
        """
        return self.execute_query(query, "QUERY_JOIN")

    def query_orders_with_details(self):
        """查询订单及其明细（全表扫描场景）"""
        query = f"""
            SELECT o.id, o.order_no, o.total_amount, o.status,
                   c.name as customer_name, c.contact_phone,
                   oi.id as item_id, oi.quantity, oi.unit_price, oi.amount,
                   p.name as product_name, p.product_code
            FROM sal_orders o
            JOIN crm_customers c ON o.customer_id = c.id
            JOIN sal_order_items oi ON o.id = oi.order_id
            JOIN inv_products p ON oi.product_id = p.id
            WHERE o.order_date >= CURRENT_DATE - INTERVAL '180 days'
            AND o.status IN ('draft', 'approved', 'shipped')
            ORDER BY o.order_date DESC
            LIMIT {random.randint(200, 1000)}
        """
        return self.execute_query(query, "QUERY_FULL_SCAN")

    def query_inventory_summary(self):
        """查询库存汇总（聚合查询）"""
        query = f"""
            SELECT i.warehouse_id, w.name as warehouse_name,
                   COUNT(DISTINCT i.product_id) as product_count,
                   SUM(i.quantity) as total_quantity,
                   AVG(i.unit_cost) as avg_cost
            FROM inv_inventory i
            JOIN inv_warehouses w ON i.warehouse_id = w.id
            GROUP BY i.warehouse_id, w.name
            HAVING SUM(i.quantity) > 0
            ORDER BY total_quantity DESC
        """
        return self.execute_query(query, "QUERY_AGGREGATE")

    def query_financial_summary(self):
        """查询财务报表（复杂子查询）"""
        query = f"""
            SELECT
                va.account_code,
                va.account_name,
                va.account_type,
                COALESCE(SUM(fd.debit), 0) as total_debit,
                COALESCE(SUM(fd.credit), 0) as total_credit,
                COALESCE(SUM(fd.debit) - SUM(fd.credit), 0) as balance
            FROM fin_accounts va
            LEFT JOIN fin_voucher_details fd ON va.id = fd.account_id
            LEFT JOIN fin_vouchers fv ON fd.voucher_id = fv.id AND fv.status = 'posted'
            WHERE va.account_type IN ('asset', 'liability', 'revenue', 'expense')
            GROUP BY va.id, va.account_code, va.account_name, va.account_type
            ORDER BY va.account_code
        """
        return self.execute_query(query, "QUERY_SUBQUERY")

    def query_customer_with_orders(self):
        """查询客户及其订单（相关子查询）"""
        query = f"""
            SELECT c.id, c.customer_code, c.name,
                   c.industry, c.credit_rating,
                   (SELECT COUNT(*) FROM sal_orders WHERE customer_id = c.id) as order_count,
                   (SELECT COALESCE(SUM(total_amount), 0) FROM sal_orders WHERE customer_id = c.id) as total_sales,
                   (SELECT MAX(order_date) FROM sal_orders WHERE customer_id = c.id) as last_order_date
            FROM crm_customers c
            WHERE c.status = 'active'
            ORDER BY total_sales DESC
            LIMIT {random.randint(50, 200)}
        """
        return self.execute_query(query, "QUERY_CORRELATED")

    def query_project_progress(self):
        """查询项目进度（多表关联）"""
        query = f"""
            SELECT p.id, p.project_code, p.name, p.status, p.total_budget, p.spent_amount,
                   t.task_count, t.completed_tasks,
                   m.milestone_count, m.achieved_milestones,
                   e.name as manager_name
            FROM pro_projects p
            LEFT JOIN (SELECT project_id, COUNT(*) as task_count,
                             SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks
                      FROM pro_project_tasks GROUP BY project_id) t ON p.id = t.project_id
            LEFT JOIN (SELECT project_id, COUNT(*) as milestone_count,
                             SUM(CASE WHEN status = 'achieved' THEN 1 ELSE 0 END) as achieved_milestones
                      FROM pro_milestones GROUP BY project_id) m ON p.id = m.project_id
            LEFT JOIN hr_employees e ON p.project_manager_id = e.id
            WHERE p.status IN ('planning', 'in_progress')
            ORDER BY p.start_date
            LIMIT {random.randint(50, 150)}
        """
        return self.execute_query(query, "QUERY_MULTI_JOIN")

    def query_production_status(self):
        """查询生产状态（生产模块查询）"""
        query = f"""
            SELECT mo.id, mo.order_no, mo.quantity, mo.status, mo.total_cost,
                   p.name as product_name, p.product_code,
                   wo.work_order_count,
                   (SELECT COUNT(*) FROM mrp_work_orders WHERE production_order_id = mo.id AND status = 'completed') as completed_wo,
                   (SELECT COUNT(*) FROM mrp_work_orders WHERE production_order_id = mo.id) as wo_count
            FROM mrp_production_orders mo
            JOIN inv_products p ON mo.product_id = p.id
            LEFT JOIN (SELECT production_order_id, COUNT(*) as work_order_count
                      FROM mrp_work_orders GROUP BY production_order_id) wo ON mo.id = wo.production_order_id
            WHERE mo.status IN ('planned', 'in_progress')
            ORDER BY mo.start_date
            LIMIT {random.randint(30, 100)}
        """
        return self.execute_query(query, "QUERY_PROD")

    def query_salary_analysis(self):
        """查询工资分析（窗口函数）"""
        query = f"""
            SELECT s.id, s.salary_month, s.base_salary, s.net_salary, s.bonus, s.deduction,
                   e.name as employee_name, e.employee_code,
                   d.name as department_name,
                   AVG(s.base_salary) OVER (PARTITION BY d.id) as dept_avg_salary,
                   RANK() OVER (PARTITION BY s.salary_month ORDER BY s.net_salary DESC) as salary_rank
            FROM hr_salary s
            JOIN hr_employees e ON s.employee_id = e.id
            JOIN hr_departments d ON e.department_id = d.id
            WHERE s.status = 'paid'
            ORDER BY s.salary_month DESC, salary_rank
            LIMIT {random.randint(100, 500)}
        """
        return self.execute_query(query, "QUERY_WINDOW")

    def query_attendance_report(self):
        """查询考勤报表（多条件聚合）"""
        query = f"""
            SELECT a.employee_id, a.work_date, a.status, a.overtime_hours,
                   e.name, e.employee_code, d.name as department_name,
                   COUNT(*) OVER (PARTITION BY e.department_id, a.status) as status_count,
                   SUM(CASE WHEN a.status = 'late' THEN 1 ELSE 0 END) OVER (PARTITION BY e.department_id) as dept_late_count
            FROM hr_attendance a
            JOIN hr_employees e ON a.employee_id = e.id
            JOIN hr_departments d ON e.department_id = d.id
            WHERE a.work_date >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY a.work_date DESC, e.id
            LIMIT {random.randint(200, 800)}
        """
        return self.execute_query(query, "QUERY_REPORT")

    def query_inventory_transactions(self):
        """查询库存事务（时序数据查询）"""
        query = f"""
            SELECT it.id, it.transaction_no, it.transaction_type, it.quantity,
                   it.before_quantity, it.after_quantity, it.created_at,
                   p.name as product_name, p.product_code,
                   w.name as warehouse_name,
                   u.username as operator
            FROM inv_inventory_transactions it
            JOIN inv_products p ON it.product_id = p.id
            JOIN inv_warehouses w ON it.warehouse_id = w.id
            LEFT JOIN sys_users u ON it.operator_id = u.id
            WHERE it.created_at >= CURRENT_TIMESTAMP - INTERVAL '7 days'
            ORDER BY it.created_at DESC
            LIMIT {random.randint(100, 500)}
        """
        return self.execute_query(query, "QUERY_TRANSACTION")

    def query_audit_logs(self):
        """查询审计日志（大量数据筛选）"""
        query = f"""
            SELECT al.id, al.username, al.action, al.module, al.object_type,
                   al.ip_address, al.response_status, al.created_at,
                   u.full_name, u.email
            FROM sys_audit_log al
            LEFT JOIN sys_users u ON al.user_id = u.id
            WHERE al.created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
            AND al.action IN ('login', 'logout', 'create', 'update', 'delete')
            ORDER BY al.created_at DESC
            LIMIT {random.randint(200, 1000)}
        """
        return self.execute_query(query, "QUERY_AUDIT")

    # ========== 更新操作 ==========

    def execute_update(self, query, op_name="UPDATE"):
        """执行更新并记录统计"""
        start = time.time()
        try:
            self.cur.execute(query)
            self.conn.commit()
            duration = time.time() - start
            self.stats['updates'] += 1
            self.log_operation(op_name, duration, query)
            return True
        except Exception as e:
            self.conn.rollback()
            self.stats['errors'] += 1
            print(f"  [Worker-{self.worker_id}] ❌ {op_name} ERROR: {e}")
            return False

    def update_employee_status(self):
        """更新员工状态"""
        emp_id = random.randint(1, 20000)
        status = random.choice(['active', 'inactive', 'on_leave'])
        query = f"""
            UPDATE hr_employees
            SET status = '{status}', updated_at = NOW()
            WHERE id = {emp_id}
        """
        return self.execute_update(query, "UPDATE_EMP_STATUS")

    def update_order_status(self):
        """更新订单状态"""
        order_id = random.randint(1, 20000)
        status = random.choice(['draft', 'approved', 'shipped', 'closed'])
        query = f"""
            UPDATE sal_orders
            SET status = '{status}', updated_at = NOW()
            WHERE id = {order_id}
        """
        return self.execute_update(query, "UPDATE_ORDER")

    def update_inventory_quantity(self):
        """更新库存数量"""
        inv_id = random.randint(1, 20000)
        qty_change = random.randint(-100, 100)
        query = f"""
            UPDATE inv_inventory
            SET quantity = quantity + {qty_change},
                available_quantity = available_quantity + {qty_change},
                updated_at = NOW()
            WHERE id = {inv_id}
        """
        return self.execute_update(query, "UPDATE_INV")

    def update_project_progress(self):
        """更新项目进度"""
        project_id = random.randint(1, 500)
        spent = random.randint(1000, 50000)
        query = f"""
            UPDATE pro_projects
            SET spent_amount = spent_amount + {spent}, updated_at = NOW()
            WHERE id = {project_id}
        """
        return self.execute_update(query, "UPDATE_PROJECT")

    def update_salary_status(self):
        """更新工资状态"""
        salary_id = random.randint(1, 20000)
        status = random.choice(['pending', 'paid'])
        query = f"""
            UPDATE hr_salary
            SET status = '{status}', paid_at = CASE WHEN '{status}' = 'paid' THEN NOW() ELSE NULL END
            WHERE id = {salary_id}
        """
        return self.execute_update(query, "UPDATE_SALARY")

    def update_customer_credit(self):
        """更新客户信用额度"""
        cust_id = random.randint(1, 20000)
        credit = random.randint(100000, 5000000)
        query = f"""
            UPDATE crm_customers
            SET credit_limit = {credit}, updated_at = NOW()
            WHERE id = {cust_id}
        """
        return self.execute_update(query, "UPDATE_CREDIT")

    def update_voucher_status(self):
        """更新凭证状态"""
        voucher_id = random.randint(1, 20000)
        status = random.choice(['draft', 'approved', 'posted'])
        query = f"""
            UPDATE fin_vouchers
            SET status = '{status}', approved_at = CASE WHEN '{status}' != 'draft' THEN NOW() ELSE NULL END
            WHERE id = {voucher_id}
        """
        return self.execute_update(query, "UPDATE_VOUCHER")

    # ========== 删除操作 ==========

    def execute_delete(self, query, op_name="DELETE"):
        """执行删除并记录统计"""
        start = time.time()
        try:
            self.cur.execute(query)
            self.conn.commit()
            duration = time.time() - start
            self.stats['deletes'] += 1
            self.log_operation(op_name, duration, query)
            return True
        except Exception as e:
            self.conn.rollback()
            self.stats['errors'] += 1
            print(f"  [Worker-{self.worker_id}] ❌ {op_name} ERROR: {e}")
            return False

    def delete_attendance_records(self):
        """删除旧考勤记录（模拟数据清理）"""
        # 只删除测试数据，不影响主数据
        query = """
            DELETE FROM hr_attendance
            WHERE id IN (SELECT id FROM hr_attendance WHERE work_date < CURRENT_DATE - INTERVAL '90 days' LIMIT 10)
        """
        return self.execute_delete(query, "DELETE_ATTENDANCE")

    def delete_audit_logs(self):
        """删除旧审计日志"""
        query = """
            DELETE FROM sys_audit_log
            WHERE id IN (SELECT id FROM sys_audit_log WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '30 days' LIMIT 10)
        """
        return self.execute_delete(query, "DELETE_AUDIT")

    def delete_inventory_transactions(self):
        """删除旧库存事务"""
        query = """
            DELETE FROM inv_inventory_transactions
            WHERE id IN (SELECT id FROM inv_inventory_transactions WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '180 days' LIMIT 10)
        """
        return self.execute_delete(query, "DELETE_TRANS")

    # ========== 复杂操作（可能产生死锁）============

    def cross_update_departments(self):
        """交叉更新部门（可能产生死锁）"""
        # 随机选两个部门
        dept1 = random.randint(1, 50)
        dept2 = random.randint(1, 50)
        if dept1 == dept2:
            return

        # 模拟不同worker以不同顺序更新，可能产生死锁
        if self.worker_id % 2 == 0:
            query1 = f"UPDATE hr_departments SET status = 'active' WHERE id = {dept1}"
            query2 = f"UPDATE hr_departments SET status = 'active' WHERE id = {dept2}"
        else:
            query2 = f"UPDATE hr_departments SET status = 'active' WHERE id = {dept2}"
            query1 = f"UPDATE hr_departments SET status = 'active' WHERE id = {dept1}"

        try:
            self.cur.execute(query1)
            time.sleep(random.uniform(0.001, 0.01))  # 模拟处理时间
            self.cur.execute(query2)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            self.stats['errors'] += 1
            if 'deadlock' in str(e).lower():
                print(f"  [Worker-{self.worker_id}] 💀 DEADLOCK DETECTED!")
            else:
                print(f"  [Worker-{self.worker_id}] ❌ ERROR: {e}")

    def transfer_inventory(self):
        """库存调拨（涉及多表更新）"""
        inv_id = random.randint(1, 20000)
        from_wh = random.randint(1, 20)
        to_wh = random.randint(1, 20)
        qty = random.randint(1, 100)

        if from_wh == to_wh:
            return

        try:
            # 减少源仓库库存
            self.cur.execute(f"""
                UPDATE inv_inventory
                SET quantity = quantity - {qty}, available_quantity = available_quantity - {qty}
                WHERE id = {inv_id} AND warehouse_id = {from_wh}
            """)
            # 增加目标仓库库存
            self.cur.execute(f"""
                UPDATE inv_inventory
                SET quantity = quantity + {qty}, available_quantity = available_quantity + {qty}
                WHERE id = {inv_id} AND warehouse_id = {to_wh}
            """)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            self.stats['errors'] += 1
            print(f"  [Worker-{self.worker_id}] ❌ TRANSFER ERROR: {e}")

    def complete_order_flow(self):
        """完成订单流程（多步更新）"""
        order_id = random.randint(1, 20000)

        try:
            # 1. 更新订单状态
            self.cur.execute(f"""
                UPDATE sal_orders SET status = 'shipped' WHERE id = {order_id} AND status = 'approved'
            """)
            # 2. 更新发货单
            self.cur.execute(f"""
                UPDATE sal_deliveries SET status = 'delivered', received_at = NOW()
                WHERE order_id = {order_id}
            """)
            # 3. 扣减库存（这里简化处理）
            self.cur.execute(f"""
                UPDATE inv_inventory
                SET reserved_quantity = GREATEST(0, reserved_quantity - 1)
                WHERE id IN (SELECT id FROM inv_inventory ORDER BY id LIMIT 1)
            """)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            self.stats['errors'] += 1
            print(f"  [Worker-{self.worker_id}] ❌ ORDER_FLOW ERROR: {e}")

    def process_payment(self):
        """处理支付（财务模块）"""
        order_id = random.randint(1, 20000)
        amount = random.uniform(1000, 50000)

        try:
            # 1. 更新订单已付金额
            self.cur.execute(f"""
                UPDATE sal_orders
                SET paid_amount = paid_amount + {amount}
                WHERE id = {order_id}
            """)
            # 2. 创建凭证
            voucher_no = 'V' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            self.cur.execute(f"""
                INSERT INTO fin_vouchers (voucher_no, voucher_type, voucher_date, total_debit, total_credit, status)
                VALUES ('{voucher_no}', 'receipt', CURRENT_DATE, {amount}, {amount}, 'draft')
            """)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            self.stats['errors'] += 1
            print(f"  [Worker-{self.worker_id}] ❌ PAYMENT ERROR: {e}")

    def run_operations(self, duration=0):
        """运行一系列操作"""
        self.connect()

        operations = [
            # 查询操作（70%）
            (self.query_employees_with_dept, 0.15),
            (self.query_orders_with_details, 0.10),
            (self.query_inventory_summary, 0.08),
            (self.query_financial_summary, 0.08),
            (self.query_customer_with_orders, 0.08),
            (self.query_project_progress, 0.05),
            (self.query_production_status, 0.05),
            (self.query_salary_analysis, 0.05),
            (self.query_attendance_report, 0.05),
            (self.query_inventory_transactions, 0.05),
            (self.query_audit_logs, 0.06),

            # 更新操作（20%）
            (self.update_employee_status, 0.04),
            (self.update_order_status, 0.03),
            (self.update_inventory_quantity, 0.04),
            (self.update_project_progress, 0.02),
            (self.update_salary_status, 0.02),
            (self.update_customer_credit, 0.02),
            (self.update_voucher_status, 0.03),

            # 删除操作（5%）
            (self.delete_attendance_records, 0.02),
            (self.delete_audit_logs, 0.015),
            (self.delete_inventory_transactions, 0.015),

            # 复杂操作（5%）
            (self.cross_update_departments, 0.01),
            (self.transfer_inventory, 0.015),
            (self.complete_order_flow, 0.015),
            (self.process_payment, 0.01),
        ]

        start_time = time.time()
        op_count = 0

        while not stop_flag.is_set():
            # 根据权重随机选择操作
            chosen = random.choices(operations, weights=[o[1] for o in operations])[0]
            op = chosen[0]

            try:
                op()
                op_count += 1
            except Exception as e:
                self.stats['errors'] += 1
                print(f"  [Worker-{self.worker_id}] ❌ UNEXPECTED ERROR: {e}")

            # 检查运行时间
            if duration > 0 and (time.time() - start_time) > duration:
                break

            # 随机休眠，模拟真实工作节奏
            time.sleep(random.uniform(0.01, 0.1))

        self.close()
        return op_count, self.stats

def run_worker(worker_id, duration=0):
    """工作线程函数"""
    ops = DBOperations(worker_id)
    op_count, stats = ops.run_operations(duration)
    return worker_id, op_count, stats

def main():
    print("=" * 60)
    print("数据库高频操作模拟器")
    print("=" * 60)
    print(f"并发工作线程: {NUM_WORKERS}")
    print(f"运行时间: {'无限' if RUN_DURATION == 0 else f'{RUN_DURATION}秒'}")
    print("=" * 60)

    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)

    start_time = time.time()
    total_ops = 0
    total_stats = {
        'queries': 0,
        'updates': 0,
        'deletes': 0,
        'errors': 0,
        'slow_queries': 0
    }

    print("\n>>> 开始模拟，按 Ctrl+C 停止...\n")

    try:
        with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
            # 提交所有工作线程
            futures = [
                executor.submit(run_worker, i, RUN_DURATION)
                for i in range(NUM_WORKERS)
            ]

            # 收集结果
            for future in as_completed(futures):
                worker_id, op_count, stats = future.result()
                total_ops += op_count
                for key in total_stats:
                    total_stats[key] += stats[key]

                elapsed = time.time() - start_time
                print(f"Worker-{worker_id}: {op_count} ops | "
                      f"Q: {stats['queries']} U: {stats['updates']} D: {stats['deletes']} "
                      f"Err: {stats['errors']} Slow: {stats['slow_queries']}")

    except KeyboardInterrupt:
        print("\n>>> 收到停止信号...")
    finally:
        elapsed = time.time() - start_time

        print("\n" + "=" * 60)
        print("模拟结束 - 统计报告")
        print("=" * 60)
        print(f"总运行时间: {elapsed:.1f} 秒")
        print(f"总操作次数: {total_ops:,}")
        print(f"操作/秒: {total_ops/elapsed:.1f}")
        print(f"\n操作分类:")
        print(f"  查询 (SELECT): {total_stats['queries']:,}")
        print(f"  更新 (UPDATE): {total_stats['updates']:,}")
        print(f"  删除 (DELETE): {total_stats['deletes']:,}")
        print(f"\n异常统计:")
        print(f"  错误数: {total_stats['errors']:,}")
        print(f"  慢查询: {total_stats['slow_queries']:,}")
        print("=" * 60)

if __name__ == "__main__":
    main()
