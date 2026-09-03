
# server.py
import logging

logging.basicConfig(
    filename="[파일 경로]//mcp_server.log",
    level=logging.DEBUG
)
from fastmcp import FastMCP
import chromadb
import os
from sentence_transformers import SentenceTransformer
from hybrid_search import hybrid_search, sentence_model, rerank
import json


client = chromadb.PersistentClient(path='[폴더 위치]/mcp_server/novel_rag.db') #db 생성 혹은 불러오기
collection = client.get_or_create_collection('novels')

#db 내용 불러오기
a_docs = collection.get(include=["documents", "embeddings"])
documents = a_docs["documents"]
embeddings = a_docs["embeddings"]
ids = a_docs["ids"]


mcp = FastMCP("my-server")

@mcp.tool()
def read_n_write_file(path: str) -> str:
	"""사용자가 소설 경로를 알려주면 자동으로 호출.
	(저장해달라는 말이 없어도 소설, 창작물 등을 보여준다고 하면 호출하기)"""
	content = ""
	with open(f"/mnt/c/{path}.txt", "r") as f:
	        content = f.read()
	embedding = sentence_model.encode("passage: " + content)
	title = path.split('/')[-1]
	collection.add(
	        documents = [content],
                embeddings = [embedding],
                ids = [title]
	)

	documents.append(content)
	embeddings.append(embedding)
	ids.append(title)
	return content


@mcp.tool()
async def novel_rag(question: str) -> str:
	"""
		소설 내용에 관한 질문 중, 컨텍스트에 저장된 내용(요약본 포함) 만으로 답변하기 어려울 때 호출하세요.
 		사용자 질의와 유사하다고 생각되는 소설 3개가 반환됩니다.
	 	반환된 소설들을 참고하여 답변하면 되지만, 모든 소설을 참고할 필요는 없습니다(엉뚱한 소설이 섞여 있을 수 있으니 주의하셍).
		만일 답변을 찾기 어렵다면 지어내지 말고 사용자에게 솔직하게 알려주세요.

	"""
	
	documents = a_docs['documents']
	embeddings = a_docs['embeddings'] #chroma db에 저장된 임베딩
	ids = a_docs['ids']

	candidates = hybrid_search(question, documents, embeddings) #하이브리드 검색
	docs = [documents[i] for i in candidates]
	results = await rerank(docs, question, candidates) #재순위화

	top_3_docs = {ids[x]: documents[x] for x in results}
	logging.debug(f"rag 반환 문서들: {top_3_docs.keys()}")

	return json.dumps(top_3_docs, ensure_ascii=False)

@mcp.tool
def novel_search(titles: list[str]) -> str:
	"""
		사용자 질의가 아래와 같고, 컴팩션 이전에 읽어 현재 컨텍스트에 원문이 없는데 소설 전체를 확인할 필요가 있을 때 호출하세요.
		1. 사용자가 정확한 소설 제목을 포함하여 질문한 경우
		2. 사용자의 질의에 응답하기 위해 어떤 소설들을 읽어야 할지 파악할 수 있는 경우
		반환 받을 소설의 제목(소설명+N화 형식)을 모두 담아 리스트 형태로 전달하세요. 소설 원문들을 반환합니다. """

	logging.debug(f"입력받은 제목들: {titles}")
	results = collection.get(ids=titles) #소설 불러오기

	novels = """ """
	for i, r in enumerate(results['documents']):
		novels += (titles[i] + "\n")
		novels += (r +"\n\n")
	logging.debug(f"반환할 텍스트 앞부분: {novels[:50]}")

	return novels

if __name__ == "__main__":
    mcp.run()
