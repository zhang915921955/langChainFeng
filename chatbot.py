import os
import traceback
from dotenv import load_dotenv
from langchain_dashscope import ChatDashScope

load_dotenv()

class Chatbot:
    def __init__(self):
        self.llm = None
        self.knowledge_base = ""
        self._init_llm()
        self._load_knowledge_base()

    def _init_llm(self):
        try:
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if not api_key:
                raise ValueError("DASHSCOPE_API_KEY 环境变量未设置")
            
            self.llm = ChatDashScope(
                temperature=0.7,
                dashscope_api_key=api_key,
                model="qwen-plus"
            )
            print("LLM 初始化成功")
        except Exception as e:
            print(f"LLM 初始化失败: {type(e).__name__}: {str(e)}")
            self.llm = None

    def _load_knowledge_base(self):
        try:
            from langchain_community.document_loaders import DirectoryLoader, TextLoader
            loader = DirectoryLoader(
                './knowledge_base',
                glob="*.md",
                loader_cls=TextLoader,
                loader_kwargs={"encoding": "utf-8"}
            )
            documents = loader.load()
            for doc in documents:
                self.knowledge_base += doc.page_content + "\n\n"
            print(f"知识库加载成功，共 {len(documents)} 个文件")
        except Exception as e:
            print(f"知识库加载失败: {type(e).__name__}: {str(e)}")
            self.knowledge_base = "这是一个智能客服系统。"

    def _web_search(self, query):
        """执行联网搜索"""
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
                if results:
                    search_content = "\n\n".join([f"【{i+1}】{result['title']}\n{result['body']}\n来源: {result['href']}" 
                                                  for i, result in enumerate(results)])
                    return search_content, [result['href'] for result in results]
                return "", []
        except Exception as e:
            print(f"搜索失败: {type(e).__name__}: {str(e)}")
            return "", []

    def chat(self, question, use_web_search=True):
        if not self.llm:
            return "抱歉，客服系统初始化失败，请检查 API Key 配置。", ["系统错误"]
        
        try:
            knowledge_content = self.knowledge_base
            
            web_content = ""
            web_sources = []
            if use_web_search:
                web_content, web_sources = self._web_search(question)
                print(f"联网搜索完成，获取到 {len(web_sources)} 条结果")
            
            search_section = f"【联网搜索结果】\n{web_content}" if web_content else ""
            prompt = f"""请根据以下信息回答用户的问题。

【参考信息】
{knowledge_content}
{search_section}

问题:
{question}

回答要求:
1. 仔细阅读并分析上述参考信息
2. 从参考信息中寻找与问题相关的内容
3. 如果找到相关信息，请基于这些信息给出详细、准确的回答
4. 如果参考信息中有多个来源，请综合所有相关信息进行回答
5. 回答要自然、友好，符合日常对话习惯
6. 直接给出答案，不要说"不知道"或类似的话
"""
            
            result = self.llm.predict(prompt)
            
            sources = ["knowledge_base"]
            if web_sources:
                sources.extend(web_sources[:3])
            
            return result, sources
        except Exception as e:
            print(f"聊天错误: {type(e).__name__}: {str(e)}")
            traceback.print_exc()
            return f"抱歉，处理您的问题时发生错误: {str(e)}", ["系统错误"]

    def chat_stream(self, question, use_web_search=True):
        """流式响应版本"""
        if not self.llm:
            yield "抱歉，客服系统初始化失败，请检查 API Key 配置。", ["系统错误"]
            return
        
        try:
            knowledge_content = self.knowledge_base
            
            web_content = ""
            web_sources = []
            if use_web_search:
                web_content, web_sources = self._web_search(question)
                print(f"联网搜索完成，获取到 {len(web_sources)} 条结果")
            
            search_section = f"【联网搜索结果】\n{web_content}" if web_content else ""
            prompt = f"""请根据以下信息回答用户的问题。

【参考信息】
{knowledge_content}
{search_section}

问题:
{question}

回答要求:
1. 仔细阅读并分析上述参考信息
2. 从参考信息中寻找与问题相关的内容
3. 如果找到相关信息，请基于这些信息给出详细、准确的回答
4. 如果参考信息中有多个来源，请综合所有相关信息进行回答
5. 回答要自然、友好，符合日常对话习惯
6. 在知识库中如果找不到相关信息，请回答'不知道'
7. 联网搜索时直接给出答案，不要说"不知道"或类似的话
"""
            
            from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
            llm_stream = ChatDashScope(
                temperature=0.7,
                dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
                model="qwen-plus",
                streaming=True,
                callbacks=[StreamingStdOutCallbackHandler()]
            )
            
            result = llm_stream.predict(prompt)
            
            sources = ["knowledge_base"]
            if web_sources:
                sources.extend(web_sources[:3])
            
            yield result, sources
        except Exception as e:
            print(f"聊天错误: {type(e).__name__}: {str(e)}")
            traceback.print_exc()
            yield f"抱歉，处理您的问题时发生错误: {str(e)}", ["系统错误"]

if __name__ == "__main__":
    print("正在初始化智能客服...")
    bot = Chatbot()
    print("智能客服已就绪！")
    print("输入'退出'结束对话")
    while True:
        question = input("用户: ")
        if question.lower() == "退出":
            break
        answer, sources = bot.chat(question)
        print(f"客服: {answer}")
        print(f"来源: {', '.join(sources)}")