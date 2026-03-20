# test_neo4j_storage.py

import sys
import os

# 确保项目根目录在路径中，以便能导入 core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config.loader import ConfigLoader
from core.memory.storage.neo4j_storage import Neo4jStorage


def test_neo4j_connection():
    print("📂 正在通过 ConfigLoader 加载配置...")

    # 1. 按照你要求的格式读取配置
    config_loader = ConfigLoader("config_dev.yaml")
    # 获取 db 节点下的内容
    db_config = config_loader.get("semantic", {})
    neo4j_cfg = db_config.get("neo4j", {})

    # 提取参数
    uri = neo4j_cfg.get("uri")
    user = neo4j_cfg.get("user")
    pwd = neo4j_cfg.get("password")

    if not all([uri, user, pwd]):
        print("❌ 错误：config_dev.yaml 中缺少必要的 Neo4j 配置项！")
        return

    print(f"🌐 正在连接至云端图数据库: {uri}")
    storage = None

    try:
        # 2. 初始化存储服务
        storage = Neo4jStorage(uri=uri, user=user, password=pwd)

        # 3. 执行冒烟测试：写入并查询
        test_subject = "User"
        test_predicate = "计划"
        test_object = "3月15日去爬山"

        print(f"📝 写入测试数据: ({test_subject})-({test_predicate})->({test_object})")
        storage.add(test_subject, test_predicate, test_object, confidence=1.0)

        print("🔍 验证写入结果...")
        results = storage.query("爬山")

        if results:
            print("✅ [测试成功] 数据库连接正常，三元组已存入 Neo4j AuraDB！")
            for idx, res in enumerate(results):
                print(f"   结果 {idx + 1}: {res['subject']} --({res['predicate']})--> {res['object']}")
        else:
            print("⚠️ [测试异常] 连接成功，但未检索到刚刚写入的数据。")

    except Exception as e:
        print(f"💥 [测试失败] 连接或操作过程中出现异常: {e}")

    finally:
        if storage:
            storage.close()
            print("🔌 Neo4j 连接已安全关闭。")


if __name__ == "__main__":
    test_neo4j_connection()