
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import math
import numpy as np
from typing import List
from transformers import PreTrainedTokenizer, AutoTokenizer
from collections import defaultdict
import time
import os
import cohere
from dotenv import load_dotenv
import asyncio
from model import sentence_model, b_tokenizer

sentence_model = SentenceTransformer('intfloat/multilingual-e5-base')
b_tokenizer = AutoTokenizer.from_pretrained('klue/roberta-base')

#cohere api 키 로드
load_dotenv()
api_key = os.getenv("COHERE_API_KEY")

co = cohere.AsyncClient(api_key) #비동기

def dense_vector_search(query, contents, embeddings, k):
    emd = sentence_model.encode("query: " + query) 
    sim_scores = [cosine_similarity([embeddings[i]], [emd]) for i in range(len(contents))]
    index = range(0, len(contents))
    pairs = zip(sim_scores, index)
    result = sorted(pairs, reverse=True)[:k]
    return zip(*result)

class BM25:
  def __init__(self, corpus:List[List[str]], tokenizer:PreTrainedTokenizer):
    self.tokenizer = tokenizer
    self.corpus = corpus

  def build_bm25(self):
    self.tokenized_corpus = self.tokenizer(self.corpus, add_special_tokens=False)
    self.n_docs = len(self.tokenized_corpus['input_ids'])
    self.avg_doc_lens = sum(len(lst) for lst in self.tokenized_corpus) / len(self.tokenized_corpus)
    self.idf = self._calculate_idf()
    self.term_freqs = self._calculate_term_freqs()

  def _calculate_idf(self):
    idf = defaultdict(float)
    for doc in self.tokenized_corpus:
      for token_id in set(doc):
        idf[token_id] += 1
    for token_id, doc_frequency in idf.items():
      idf[token_id] = math.log(((self.n_docs - doc_frequency + 0.5) / (doc_frequency + 0.5)) + 1)
    return idf

  def _calculate_term_freqs(self):
    term_freqs = [defaultdict(int) for _ in range(self.n_docs)]
    for i, doc in enumerate(self.tokenized_corpus):
      for token_id in doc:
        term_freqs[i][token_id] += 1
    return term_freqs

  def get_scores(self, query:str, k1:float = 1.2, b:float=0.75):
    query = self.tokenizer([query], add_special_tokens=False)['input_ids'][0]
    scores = np.zeros(self.n_docs)
    for q in query:
      idf = self.idf[q]
      for i, term_freq in enumerate(self.term_freqs):
        q_frequency = term_freq[q]
        doc_len = len(self.tokenized_corpus[i])
        score_q = idf * (q_frequency * (k1 + 1)) / ((q_frequency) + k1 * (1 - b + b * (doc_len / self.avg_doc_lens)))
        scores[i] += score_q
    return scores

  def get_top_k(self, query:str, k:int):
    self.build_bm25()
    scores = self.get_scores(query)
    top_k_indices = np.argsort(scores)[-k:][::-1]
    top_k_scores = scores[top_k_indices]
    return top_k_scores, top_k_indices


def new_rank(scores:List[List[int]], rankings):
    rrf = defaultdict(float)
    for i in range(len(scores[0])):
            rrf[rankings[0][i]] +=  scores[0][i] * 0.1
            rrf[rankings[1][i]] +=  scores[1][i] * 0.9
    return sorted(rrf, key=rrf.get, reverse=True)


def hybrid_search(query, contents, embeddings):
  bm25 = BM25(contents, b_tokenizer)

  ## 임베딩과 키워드 검색 비동기 처리
  #(d_scores, dense_search_ranking), (b_scores, bm25_search_ranking) = await asyncio.gather(
  #	asyncio.to_thread(dense_vector_search, query, contents, embeddings, 30),
  #	asyncio.to_thread(bm25.get_top_k, query, 30)
  #)

  d_scores, dense_search_ranking = dense_vector_search(query, contents, embeddings, 30) #임베딩(의미) 검색
  b_scores, bm25_search_ranking = bm25.get_top_k(query, 30) # bm25(키워드) 검색

  for i in range(len(b_scores)):
    b_scores[i] /=  (10 + b_scores[i])
  results = []
  results = new_rank(scores = [d_scores, b_scores], rankings=[dense_search_ranking, bm25_search_ranking]) #순위 조합
  return results[:15]

async def rerank(docs: list, query: str, ids: list, top_k: int = 3) -> list:

    response = await co.rerank(
    model="rerank-v3.5",
    query=query,
    documents=docs,
    top_n=top_k
    )
    results = response.results
    return [ids[x.index] for x in results]



