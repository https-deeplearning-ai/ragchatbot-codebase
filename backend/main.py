from rag_system import RAGSystem
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

def main():
    """主函数：初始化RAG系统，加载数据并提供查询接口"""
    print("正在初始化RAG系统...")

    # 初始化RAG系统，使用data文件夹
    rag_system = RAGSystem(folder_path="./data")

    print("RAG系统初始化完成。")
    print("正在加载data文件夹中的文档...")

    # 加载并向量化data文件夹中的内容
    total_docs, total_chunks = rag_system.load_md_folder("./data", clear_existing=False)
    print(f"文档加载完成：共加载 {total_docs} 个文档，生成 {total_chunks} 个分块。")

    # 获取统计信息
    stats = rag_system.get_document_stats()
    print(f"当前系统状态：总文档数 {stats['total_documents']}，文件列表：{stats['file_names']}")

    print("\n=== RAG查询系统启动 ===")
    print("输入查询内容进行搜索，输入 'quit' 或 'exit' 退出程序。\n")

    while True:
        try:
            # 获取用户输入
            query_text = input("请输入查询内容：").strip()

            if query_text.lower() in ['quit', 'exit']:
                print("感谢使用，再见！")
                break

            if not query_text:
                print("查询内容不能为空，请重新输入。\n")
                continue

            print(f"\n正在查询：'{query_text}'")
            print("-" * 50)

            # 执行查询
            result = rag_system.query(query_text)

            # 检查结果并输出
            if "搜索错误" in result["answer"]:
                print("❌ 查询失败：" + result["answer"])
            elif result["answer"] == "未找到相关内容":
                print("❌ 未找到相关内容，请尝试其他查询词。")
            else:
                print("✅ 查询成功！")
                print("\n📝 答案：")
                print(result["answer"])

                print(f"\n🔗 来源信息（共 {len(result['sources'])} 个）：")
                for i, source in enumerate(result["sources"], 1):
                    print(f"  {i}. {source}")

                print(f"\n📊 原始结果（共 {len(result['results'])} 个）：")
                for i, res in enumerate(result["results"], 1):
                    print(f"  {i}. 距离: {res['distance']:.4f}")
                    print(f"     内容: {res['content'][:200]}..." if len(res['content']) > 200 else f"     内容: {res['content']}")
                    print()

            print("-" * 50)

        except KeyboardInterrupt:
            print("\n\n程序被用户中断，感谢使用！")
            break
        except Exception as e:
            print(f"❌ 查询过程中发生错误：{e}")
            print("请检查系统配置或重试。\n")


if __name__ == "__main__":
    main()
