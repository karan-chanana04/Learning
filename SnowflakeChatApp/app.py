import streamlit as st
from datetime import datetime, timezone
import uuid
from typing import List, Dict, Callable, Optional
from pathlib import Path
from dotenv import load_dotenv
import os
import requests
import re
from bs4 import BeautifulSoup, Comment
from urllib.parse import urljoin, urldefrag

# LangChain & ML imports
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.memory import ConversationBufferMemory
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from langchain.agents import initialize_agent, AgentType

# ==============================
# Snowflake bot — Streamlit App
# ==============================

def load_env_vars():
    global_env_path = Path.home() / ".env"
    load_dotenv(global_env_path)
    return os.getenv("GOOGLE_API_KEY"), os.getenv("TAVILY_API_KEY")

def crawl_snowflake_docs(start_url, max_pages=200):
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (compatible; SimpleBFSBot/1.0; +https://example.local)"
    }
    TIMEOUT = 15
    all_texts = []
    all_urls = set()
    resp = requests.get(start_url, headers=HEADERS, timeout=TIMEOUT)
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "template", "svg", "canvas", "iframe", "picture", "source"]):
        tag.decompose()
    for tag in soup(["header", "footer", "nav", "aside"]):
        tag.decompose()
    for c in soup.find_all(string=lambda text: isinstance(text, Comment)):
        c.extract()
    text = soup.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{2,}", "\n", text)
    all_texts.append(text)
    for a in soup.find_all("a", href=True):
        abs_url = urljoin(start_url, a["href"])
        abs_url, _ = urldefrag(abs_url)
        all_urls.add(abs_url)
    # Limit crawl to max_pages
    for url in list(all_urls)[:max_pages]:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            ctype = resp.headers.get("Content-Type", "")
            if not ("text/html" in ctype.lower() or "application/xhtml+xml" in ctype.lower()):
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "noscript", "template", "svg", "canvas", "iframe", "picture", "source"]):
                tag.decompose()
            for tag in soup(["header", "footer", "nav", "aside"]):
                tag.decompose()
            for c in soup.find_all(string=lambda text: isinstance(text, Comment)):
                c.extract()
            text = soup.get_text(separator="\n", strip=True)
            text = re.sub(r"\n{2,}", "\n", text)
            all_texts.append(text)
        except Exception:
            continue
    return all_texts

def build_vector_store(all_texts):
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    text_splitter = RecursiveCharacterTextSplitter(separators=["\n\n", "\n", " ", ""], chunk_size=1000, chunk_overlap=200)
    documents = text_splitter.create_documents(all_texts)
    vector = FAISS.from_documents(documents, embeddings)
    return vector

def build_rag_chain(vector, google_api_key):
    output_parser = StrOutputParser()
    template = ChatPromptTemplate.from_messages(
        [("system", "You are an assistant for question-answering tasks. Use the provided pieces of retrieved context to answer the question. If you don't know the answer, say that you don't know. Always provide the detailed answer.\n\n"),
         ("human", "Hello, What is Snowflake warehouse used for?"),
         ("ai", "Warehouses are required for queries, as well as all DML operations, including loading data into tables."),
         ("human", "{input}")])
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2, google_api_key=google_api_key)
    retriever = vector.as_retriever()
    document_chain = template | llm
    rag_chain = create_retrieval_chain(retriever, document_chain)
    return rag_chain, llm

def build_agent(rag_chain, llm, tavily_api_key):
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    @tool
    def retriever_tool(query: str) -> str:
        """Searches and returns answer to the query from the provided documentation."""
        response = rag_chain.invoke({"input": query})
        return response["answer"]
    search = TavilySearch(tavily_api_key=tavily_api_key)
    tools = [retriever_tool]
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        memory=memory,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True
    )
    return agent

def handle_user_message(agent, user_input):
    response = agent.run(user_input)
    return response

# ---------- Streamlit UI ----------
def main():
    st.set_page_config(page_title="Snowflake bot", page_icon="❄️", layout="centered")
    if "messages" not in st.session_state or not isinstance(st.session_state["messages"], list):
        st.session_state["messages"] = []
    st.markdown("# Snowflake bot")
    cols = st.columns([1, 1, 6])
    with cols[0]:
        reset_clicked = st.button("Reset", help="Clear the entire chat history.")
    #with cols[1]:
    #    show_json = st.checkbox("Show JSON", value=True, help="Toggle to show raw message array.")
    if reset_clicked:
        st.session_state["messages"] = []
        st.success("Chat history cleared.")
        # if isinstance(st.session_state["messages"], list) and len(st.session_state["messages"]) == 0:
        #     st.caption("✅ Validation: messages list exists and is empty after reset.")
        # else:
        #     st.caption("⚠️ Validation failed: reinitializing messages list.")
        #     st.session_state["messages"] = []
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state["messages"]:
            with st.chat_message("user" if msg["role"] == "user" else "assistant"):
                st.write(msg["content"])
    user_input = st.chat_input("Type your question and press Enter…")
    # Load environment and build pipeline only once
    if "agent" not in st.session_state:
        GOOGLE_API_KEY, TAVILY_API_KEY = load_env_vars()
        all_texts = crawl_snowflake_docs("https://docs.snowflake.com/en/guides")
        vector = build_vector_store(all_texts)
        rag_chain, llm = build_rag_chain(vector, GOOGLE_API_KEY)
        agent = build_agent(rag_chain, llm, TAVILY_API_KEY)
        st.session_state["agent"] = agent
    agent = st.session_state["agent"]
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    def new_message(role: str, content: str) -> Dict:
        return {
            "id": str(uuid.uuid4()),
            "timestamp": utc_now_iso(),
            "role": role,
            "content": content
        }
    if user_input is not None:
        user_msg = new_message("user", user_input)
        st.session_state["messages"].append(user_msg)
        # if st.session_state["messages"] and st.session_state["messages"][-1]["id"] == user_msg["id"]:
        #     st.caption("✅ Validation: user message appended correctly.")
        # else:
        #     st.caption("⚠️ Validation failed: attempting to re-append user message.")
        #     st.session_state["messages"].append(user_msg)
        try:
            reply_text = handle_user_message(agent, user_input)
            ai_msg = new_message("ai", reply_text)
        except Exception as e:
            ai_msg = new_message("ai", "Sorry, something went wrong processing your request.")
            with st.expander("Error details (for debugging)"):
                st.exception(e)
        st.session_state["messages"].append(ai_msg)
        # if st.session_state["messages"] and st.session_state["messages"][-1]["id"] == ai_msg["id"]:
        #     st.caption("✅ Validation: AI message appended correctly.")
        # else:
        #     st.caption("⚠️ Validation failed: attempting to re-append AI message.")
        #     st.session_state["messages"].append(ai_msg)
        with chat_container:
            with st.chat_message("user"):
                st.write(user_msg["content"])
            with st.chat_message("assistant"):
                st.write(ai_msg["content"])
    #if show_json:
        # st.subheader("Messages (JSON)")
        # msgs: List[Dict] = st.session_state.get("messages", [])
        # st.json(msgs)
        #st.subheader("Messages (JSON)")
        #msgs: List[Dict] = st.session_state.get("messages", [])
        # Show only the content of each message, not the full JSON
        #contents = [m["content"] for m in msgs]
        #st.write(contents)
    is_list = isinstance(st.session_state.get("messages", None), list)
    in_order = True
    try:
        iso_times = [m["timestamp"] for m in st.session_state["messages"]]
        in_order = all(isinstance(t, str) and t.endswith("Z") for t in iso_times)
    except Exception:
        in_order = False
    # if is_list and in_order:
    #     st.caption("✅ Validation: message store is a list with ISO8601 UTC timestamps; display order is oldest → newest.")
    # else:
    #     st.caption("⚠️ Validation: repairing message structure.")
    #     if not is_list:
    #         st.session_state["messages"] = []

if __name__ == "__main__":
    main()