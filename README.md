# 소설 RAG

## 목차
1. 개요
2. 주요 기능
3. mcp 연결
4. 폴더 구조

## 1. 개요
* 사용자 질의가 들어오면 저장해두었던 소설 목록에서 유사한 소설 3개를 뽑아 ai에게 반환해주는 mcp 서버

### 개발 과정
#### (1) 베이스 버전
* colab 환경, 랭체인과 구글 gemma 모델 api 이용
* 검색 품질을 높이기 위한 튜닝 과정을 거쳐 RAG 파이프라인을 구축했다.
#### (2) mcp 서버로 확장
* 우분투 LTS 환경에 서버 구현한 뒤 클로드 데스크톱과 연결했다.
* 처음엔 코랩 환경에서 rag 챗봇을 만드는 것이 목표였지만, 개발 도중 mcp를 접하고 mcp 서버로 확장하게 되었다.

### 기술 스택
|분류|기술|
|---|---|
|언어|Python|
|프레임워크|Langchain*|
|AI/API|Google ai api*, Claude, Cohere (rerank)|
|임베딩|Sentence Transformers|
|vector db|Chroma|

*표시된 항목들은 베이스 버전에서만 사용


## 2. 주요 기능
### (1) rag 기능
* 지금까지 읽은(db에 저장된) 소설에 관한 질문을 하면, 관련 소설들을 참고하여 답변한다.

#### 베이스 버전
<pre><img  width="1915" height="760" alt="Image" src="https://github.com/user-attachments/assets/9717f809-fd7b-47e5-8656-a121a01ce4eb" /></pre>

#### mcp 서버 버전
 <pre><img width="754" height="448" alt="Image" src="https://github.com/user-attachments/assets/c116385e-056e-491c-b0a5-a227b95055b4" />
  
* rag 기능 안 썼을 때
<img width="713" height="203" alt="Image" src="https://github.com/user-attachments/assets/36736c8b-5af2-4e7d-a530-40d1ed6be119" /></pre>

* 허깅페이스의 소설 데이터와 ai가 생성한 질문으로 hit rate@3(반환된 상위 3개 소설 중 정답 소설이 있는 것들의 비율)을 테스트 및 튜닝한 결과, **66%** (639/970)에서 최종 **약 94%** 까지 올렸다.
  * 자세한 건 DETAIL.md 파일 참고
### (2) 소설 읽기 기능_mcp 서버에 추가한 기능
* 요약, 오타 검열 등 자신이 원하는 작업을 미리 요청한 뒤 파일 경로를 입력하면 클로드는 해당 위치에 있는 소설 내용을 읽고 작업을 수행한다.

<pre>
 * 소설 읽고 요약해달라고 요청한 상태
 <img width="700" height="649" alt="Image" src="https://github.com/user-attachments/assets/becd9e78-3b3e-49ab-83af-98383b5555cf" /></pre>
 

### (3) search 기능_mcp 서버에 추가한 기능
* 죄와벌 1화, 2화에서 박 신부는 어떤 인물?" 처럼 소설 회차가 명시되어 있는 질문이 들어올 때 호출되어, 해당 소설들을 참고하여 답변한다.

<pre><img width="662" height="530" alt="Image" src="https://github.com/user-attachments/assets/38e314b5-f936-4fed-a9e1-32f1504162d6" /></pre>

## 3. 실행
### 베이스 버전 실행 (코랩 기준)
* colab_prototyoe의 novel_rag.ipynb 과 novel_summary.csv 다운로드 후 구글 드라이브에 추가
* novel_rag.ipynb 실행 후 novel_summary.csv 위치 수정
* Screts(보안 비밀)에 구글 ai 스튜디오 api 키 추가 (GOOGLE_API_KEY)
* 차례대로 셀 실행 후 chatbot 입력 칸에 질의 입력(quit 또는 exit 입력 시 중단)
  * 채팅 요약본 생성 셀은 생략해도 무방하다. (소설 저장하는 작업을 한 뒤 질의를 입력한다는 가정 하에, 대화 내용을 기억하도록 요약본을 생성하도록 했다.) 생략할 경우 chat_summary 변수를 새로 정의해야 한다.
### mcp 서버 실행 (우분투 기준)
#### clone & install
<pre><code> git clone https://github.com/won2133/novel_rag.git
 cd mcp_server
 pip install -r requirements.txt
</code></pre>
#### 설정
* server.py의 log 주소, chroma 주소 변경
<pre><code>#log 주소 수정
 logging.basicConfig(
    filename="[파일 경로]/mcp_server.log",
    level=logging.INFO
 )
# chroma db 주소 수정_ 기존 데이터 없이 새로 시작하고 싶다면 db 이름이나 collection 이름 수정하여 새로 생성
 client = chromadb.PersistentClient(path='[파일 경로]/novel_rag.db')
 collection = client.get_or_create_collection('novels')
</code></pre>
* cohere api 키 생성 후 .env 파일에 저장하기
<pre><code>COHERE_API_KEY = YOUR_API_KEY</code></pre>
#### mcp 연결
* claude desktop 앱의 설정-개발자-구성편집 클릭 후 claude_desktop_config.json 파일 수정
<pre></code>
"mcpServers": {
  "[서버 이름]" : {
    "command" : "wsl"
    "args" : {
      "[가상환경 절대 경로]/python3",
      "[프로젝트 절대 경로]/server.py"
    }
  }
}
</code></pre>

* 파일 저장하고 클로드 데스크톱 앱 재시작하면 연결 완료.
 * 연결은 됐어도 언급 없이 바로 파일 경로나 질의를 입력하면 안 되는 경우가 있어서 mcp 서버가 연결됐는지 확인하고 진행하는 게 안전하다.
 * read 기능의 현재 설정 위치는 '/mnt/c' (c드라이브)이다. 클로드에게 경로를 알려줄 때 c드라이브 제외 전체 위치를 입력하거나 서버에 설정된 위치를 샹황에 맞게 수정해서 사용하면 된다.
#### log 확인 방법
<pre><code>tail -f [파일 경로]/mcp_server.log</code></pre>
* 현재 logging 레벨은 INFO로 되어 있으니 파이썬 코드에서 직접 logging.DEBUG로 추가한 내용들을 보려면 레벨을 DEBUG로 수정해야 한다.

## 4. 폴더 구조
### colab_prototype
* 베이스 버전에서 사용한 텍스트 파일 및 코드들
* 소설 질문, 소설 요약본, 파라미터 설정을 위한 검증용 파일, rag 베이스 버전 파일

### mcp_server
* mcp 서버 버전에서 사용한 파일 및 코드들
* db, 서버 파일, 클라이언트(비동기 처리 구현을 위한 요청 테스트 파일. 자세한 건 DETAIL.md 참고) 등

### detail.md
* 아키텍처, 파라미터 설정 과정, 고민한 과정들을 담은 파일
