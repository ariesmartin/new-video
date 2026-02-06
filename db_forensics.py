import psycopg
from datetime import datetime
import json
import uuid

DB_URL = "postgresql://postgres.myproject:hanyu416@192.168.2.70:9432/postgres"

def inspect_db():
    print(f"\n🔍 [Step 1] Database Forensics: Connecting to real DB...")
    try:
        with psycopg.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                print("✅ Connected!")
                
                # 查询最近的 5 条记录
                cur.execute("""
                    SELECT thread_id, metadata
                    FROM checkpoints 
                    ORDER BY checkpoint_id DESC 
                    LIMIT 5
                """)
                
                rows = cur.fetchall()
                print(f"\n📋 Recent Threads in Database ({len(rows)}):")
                for row in rows:
                    tid, meta = row
                    print(f"   🔹 ThreadID: {tid}")
                    if meta:
                        print(f"      Metadata: {json.dumps(meta, default=str)}")
                        
                # 还可以验证我刚才测试用的 ID 是否在里面
                # 之前的测试 ID 类似 test-thread-d2d0...
                cur.execute("SELECT thread_id FROM checkpoints WHERE thread_id LIKE 'test-thread-%' LIMIT 1")
                test_row = cur.fetchone()
                if test_row:
                    print(f"\n✅ FOUND test thread: {test_row[0]}")
                else:
                    print("\n⚠️ Test thread NOT found (maybe different DB?)")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    inspect_db()
