import os
import json
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI

# 读取 Perplexity 检索结果
data_path = "data/perplexity_results.json"
with open(data_path, "r", encoding="utf-8") as f:
    search_results = json.load(f)

# 加载本地 ChromaDB
client = chromadb.PersistentClient(path="data/chroma_db")
collection = client.get_or_create_collection("creditmag")

# 嵌入模型（使用 DeepSeek API）
embed_fn = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    model_name="text-embedding-ada-002"  # 或其他支持的模型
)

# 处理 Perplexity 的新输出格式
docs = []
for result in search_results:
    if result.get("content") and not result.get("error"):
        docs.append({
            "topic": result["topic"], 
            "content": result["content"]
        })

if not docs:
    print("没有找到有效的搜索结果")
    exit(1)

# 生成嵌入
texts = [d["content"] for d in docs]
embeddings = embed_fn(texts)

# 查询本地向量库，筛选最相关的文档
top_k = 5  # 先筛选出5篇，再用大模型精筛
query_results = collection.query(
    query_embeddings=embeddings, 
    n_results=top_k
)

# 用大模型进一步筛选出最优的2篇
client_deepseek = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1"
)

# 准备筛选提示
candidate_docs = []
for i, (doc, distance) in enumerate(zip(docs, query_results['distances'][0])):
    candidate_docs.append({
        "index": i,
        "topic": doc["topic"],
        "content": doc["content"][:1000],  # 限制长度
        "similarity": 1 - distance  # 转换为相似度
    })

# 用大模型筛选最优的2篇
filter_prompt = f"""
请从以下{len(candidate_docs)}篇关于信用评级和征信研究的文档中，选出最相关、最有价值的2篇。

筛选标准：
1. 内容与信用评级、征信体系建设、金融监管高度相关
2. 信息时效性强，具有实际参考价值
3. 来源权威，内容详实

候选文档：
{json.dumps(candidate_docs, ensure_ascii=False, indent=2)}

请返回JSON格式的结果，包含选中的2篇文档的索引号：
{{"selected_indices": [0, 1], "reason": "选择理由"}}
"""

try:
    response = client_deepseek.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": filter_prompt}],
        temperature=0.1
    )
    
    # 解析大模型的选择结果
    selection_result = json.loads(response.choices[0].message.content)
    selected_indices = selection_result.get("selected_indices", [])
    
    # 获取最终选中的文档
    final_results = []
    for idx in selected_indices[:2]:  # 确保最多2篇
        if idx < len(candidate_docs):
            final_results.append(candidate_docs[idx])
    
    print(f"大模型筛选结果：选中 {len(final_results)} 篇文档")
    
except Exception as e:
    print(f"大模型筛选失败，使用向量相似度最高的2篇: {e}")
    # 降级方案：选择相似度最高的2篇
    final_results = sorted(candidate_docs, key=lambda x: x["similarity"], reverse=True)[:2]

# 保存筛选结果
with open("data/filtered_results.json", "w", encoding="utf-8") as f:
    json.dump({
        "selected_documents": final_results,
        "total_candidates": len(candidate_docs),
        "selection_method": "vector_similarity + llm_filtering"
    }, f, ensure_ascii=False, indent=2) 