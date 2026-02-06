import psycopg
import sys

# 真实 DB 地址
DB_URL = "postgresql://postgres.myproject:hanyu416@192.168.2.70:9432/postgres"

def reset_checkpoints():
    print(f"\n🗑️  RESETTING DATABASE CHECKPOINTS at {DB_URL}...")
    try:
        with psycopg.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                # 按照依赖关系顺序清空
                cur.execute("TRUNCATE TABLE checkpoint_writes CASCADE;")
                cur.execute("TRUNCATE TABLE checkpoint_blobs CASCADE;")
                cur.execute("TRUNCATE TABLE checkpoints CASCADE;")
                print("✅ Tables truncated: checkpoints, checkpoint_blobs, checkpoint_writes")
                
            conn.commit()
            print("✨ Database reset complete.")
            
    except Exception as e:
        print(f"❌ Database Reset Failed: {e}")
        # 如果表不存在，可能不需要 truncate，打印出来即可
        if "relation" in str(e) and "does not exist" in str(e):
             print("ℹ️  Tables might not exist yet, which is fine.")

if __name__ == "__main__":
    reset_checkpoints()
