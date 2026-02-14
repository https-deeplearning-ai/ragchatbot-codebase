重构backend文件夹中的内容，将rag_system修改为一个通用的rag系统，输入改为任意的md文件，保持各文件名不变；
不再需要使用大模型接口，不再需要ai_generator.py文件、session_manager.py文件；
rag_system对外提供两个接口：
1. 初始化接口，输入为文件夹路径，输出为初始化完成的rag系统；
2. 查询接口，输入为查询语句，输出为查询结果；2