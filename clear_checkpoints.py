"""
清理有问题的 checkpoint 数据

删除存储了错误消息格式的 checkpoint 记录，这样下次冷启动会通过正确的 LangGraph 流程生成新的 checkpoint。
"""

import asyncio
import sys
sys.path.insert(0, "/Users/ariesmartin/Documents/new-video")

from backend.graph.checkpointer import checkpointer_manager


async def clear_problematic_checkpoints():
    """清理所有 checkpoint 数据"""
    print("🧹 开始清理 checkpoint 数据...")
    
    await checkpointer_manager.initialize()
    
    # 获取数据库连接
    async with checkpointer_manager._pool.connection() as conn:
        # 删除所有 checkpoint 相关的数据
        tables = [
            "checkpoint_blobs",
            "checkpoint_writes",
            "checkpoints",
        ]
        
        for table in tables:
            try:
                result = await conn.execute(f"DELETE FROM {table}")
                print(f"  ✅ 清理表 {table}: {result.rowcount} 行")
            except Exception as e:
                print(f"  ⚠️ 清理表 {table} 失败: {e}")
        
        # 提交事务
        await conn.commit()
    
    print("\n✅ Checkpoint 数据清理完成！")
    print("   请刷新页面重新开始对话。")


if __name__ == "__main__":
    asyncio.run(clear_problematic_checkpoints())
