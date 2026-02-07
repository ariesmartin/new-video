#!/usr/bin/env python3
"""
应用数据库迁移脚本 - 使用PostgreSQL直接连接
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# 加载环境变量
load_dotenv("/Users/ariesmartin/Documents/new-video/backend/.env")

# 获取数据库连接信息
database_url = os.getenv("DATABASE_URL")

if not database_url:
    print("❌ 错误: 找不到DATABASE_URL配置")
    sys.exit(1)

print(f"✅ 数据库配置已加载")
print(
    f"   连接地址: {database_url.split('@')[1] if '@' in database_url else 'localhost'}"
)


def apply_migration():
    """应用迁移脚本"""
    migration_file = "/Users/ariesmartin/Documents/new-video/backend/supabase/migrations/005_theme_knowledge_base.sql"

    print(f"\n📖 读取迁移文件: {migration_file}")

    with open(migration_file, "r", encoding="utf-8") as f:
        sql_content = f.read()

    print(f"   SQL长度: {len(sql_content)} 字符")

    # 连接到数据库
    print(f"\n🔌 连接到PostgreSQL...")
    conn = psycopg2.connect(database_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    print(f"   ✅ 连接成功\n")

    # 执行SQL
    try:
        print("🚀 执行迁移...")
        cursor.execute(sql_content)
        print("   ✅ 迁移成功完成！")
        success = True
    except psycopg2.Error as e:
        print(f"   ❌ 错误: {e}")
        # 如果是已存在的错误，不算失败
        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
            print("   ⚠️ 部分对象已存在，继续执行...")
            success = True
        else:
            success = False
    finally:
        cursor.close()
        conn.close()

    return success


def verify_tables():
    """验证表是否创建成功"""
    print("\n🔍 验证表结构...")

    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()

    expected_tables = [
        "themes",
        "theme_elements",
        "theme_examples",
        "hook_templates",
        "market_insights",
    ]

    for table in expected_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  ✅ {table}: 表存在 ({count} 条记录)")
        except psycopg2.Error as e:
            print(f"  ❌ {table}: 表不存在或无法访问")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 数据库迁移工具")
    print("=" * 60)

    # 应用迁移
    success = apply_migration()

    if success:
        # 验证
        verify_tables()

    print("\n" + "=" * 60)
    if success:
        print("✅ 迁移完成！")
        print("\n📝 提示: 现在可以运行数据导入脚本 import_to_supabase.py")
    else:
        print("⚠️ 迁移过程中有错误，请检查")
