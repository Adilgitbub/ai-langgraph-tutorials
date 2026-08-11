# %%
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# %%
load_dotenv()

# %%
class SubState(TypedDict):

    input_text: str
    translated_text: str

# %%
subgraph_llm = ChatOpenAI(
    base_url="http://localhost:12434/engines/v1",
        api_key="not-needed",
        model="ai/llama3.2:3B-Q4_K_M"
        # model="ai/gemma4:E4B"
        )

# %% [markdown]
# 

# %%
def translate_text(state: SubState):

    prompt = f"""
Translate the following text to Hindi.
Keep it natural and clear. Do not add extra content.

Text:
{state["input_text"]}
""".strip()
    
    translated_text = subgraph_llm.invoke(prompt).content

    return {'translated_text': translated_text}

# %%
subgraph_builder = StateGraph(SubState)

subgraph_builder.add_node('translate_text', translate_text)

subgraph_builder.add_edge(START, 'translate_text')
subgraph_builder.add_edge('translate_text', END)

subgraph = subgraph_builder.compile()

# %%



# class SubState(TypedDict):
#     answer : str
#     answer_hin : str

# def generate_answers(state :SubState):
#    answer_hin= subgraph_llm.invoke(f"please generate a hindi reply for {SubState['messages']}").content;
#    return {'answer_hin':answer_hin}

# sub_graph=StateGraph(SubState)

# sub_graph.add_node("generate_answers",generate_answers)

# sub_graph.add_edge(START,"generate_answers")
# sub_graph.add_edge("generate_answers", END);

# sub_graph.compile

# %%
class ParentState(TypedDict):

    question: str
    answer_eng: str
    answer_hin: str
    
    

# %%
parent_llm = ChatOpenAI(
     base_url="http://localhost:12434/engines/v1",
    api_key="not-needed",
    model="ai/llama3.2:3B-Q4_K_M"
    # model="ai/gemma4:E4B"
    )

# %%
def generate_answer(state: ParentState):

    answer = parent_llm.invoke(f"You are a helpful assistant. Answer clearly.\n\nQuestion: {state['question']}").content
    return {'answer_eng': answer}

# %%
def translate_answer(state: ParentState):
    import requests
    
    # # Tell Docker Model Runner to unload gemma first
    # requests.delete("http://localhost:12434/engines/v1/models/ai/gemma4:E4B")
    # call the subgraph
    result = subgraph.invoke({'input_text': state['answer_eng']})

    return {'answer_hin': result['translated_text']}

# %%
parent_builder = StateGraph(ParentState)

parent_builder.add_node("answer", generate_answer)
parent_builder.add_node("translate", translate_answer)

parent_builder.add_edge(START, 'answer')
parent_builder.add_edge('answer', 'translate')
parent_builder.add_edge('translate', END)

# %%
graph = parent_builder.compile()

graph

# %%
graph.invoke({'question': 'What is quantum physics'})

# %%



