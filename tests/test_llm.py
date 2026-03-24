"""
pytest 配置
"""
import pytest


@pytest.fixture
def sample_connection():
    """示例数据库连接"""
    return {
        "name": "test_db",
        "db_type": "mysql",
        "host": "localhost",
        "port": 3306,
        "database": "test_db",
        "username": "root",
        "password": "test"
    }


@pytest.fixture
def sample_sql():
    """示例 SQL 查询"""
    return "SELECT * FROM users LIMIT 10"
