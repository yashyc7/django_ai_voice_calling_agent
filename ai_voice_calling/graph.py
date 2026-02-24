from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    name: str
    age: str
    weight: str
    current_step: str
    user_input: str
    messages: Annotated[list, operator.add]

def start_node(state: AgentState) -> AgentState:
    return {
        "current_step": "ask_name",
        "messages": [SystemMessage(content="Welcome! What is your name?")]
    }

def ask_name(state: AgentState) -> AgentState:
    name = state.get("user_input", "").strip()
    if name:
        return {
            "name": name,
            "user_input": "",
            "current_step": "ask_age",
            "messages": [SystemMessage(content=f"Nice to meet you {name}. What is your age?")]
        }
    return {
        "current_step": "ask_name",
        "messages": [SystemMessage(content="Sorry, I didn't catch that. What is your name?")]
    }

def ask_age(state: AgentState) -> AgentState:
    age = state.get("user_input", "").strip()
    if age:
        return {
            "age": age,
            "user_input": "",
            "current_step": "ask_weight",
            "messages": [SystemMessage(content=f"Got it, {age} years old. What is your weight in kilograms?")]
        }
    return {
        "current_step": "ask_age",
        "messages": [SystemMessage(content="Sorry, I didn't catch that. What is your age?")]
    }

def ask_weight(state: AgentState) -> AgentState:
    weight = state.get("user_input", "").strip()
    if weight:
        return {
            "weight": weight,
            "user_input": "",
            "current_step": "save_data",
            "messages": [SystemMessage(content=f"Perfect. I have recorded your weight as {weight} kilograms.")]
        }
    return {
        "current_step": "ask_weight",
        "messages": [SystemMessage(content="Sorry, I didn't catch that. What is your weight in kilograms?")]
    }

def save_data(state: AgentState) -> AgentState:
    from .utils import save_to_excel
    save_to_excel(state.get("name", ""), state.get("age", ""), state.get("weight", ""))
    return {
        "current_step": "__end__",
        "messages": [SystemMessage(content="All done! Your information has been saved. Goodbye!")]
    }

def route(state: AgentState) -> str:
    return state.get("current_step", "__end__")

graph = StateGraph(AgentState)
graph.add_node("start", start_node)
graph.add_node("ask_name", ask_name)
graph.add_node("ask_age", ask_age)
graph.add_node("ask_weight", ask_weight)
graph.add_node("save_data", save_data)

graph.set_entry_point("start")
graph.add_edge("start", "ask_name")

graph.add_conditional_edges("ask_name", route, {
    "ask_age": "ask_age",
    "ask_name": "ask_name",
})
graph.add_conditional_edges("ask_age", route, {
    "ask_weight": "ask_weight",
    "ask_age": "ask_age",
})
graph.add_conditional_edges("ask_weight", route, {
    "save_data": "save_data",
    "ask_weight": "ask_weight",
})
graph.add_edge("save_data", END)

checkpointer = MemorySaver()

# ✅ interrupt_before pauses graph BEFORE each node, waiting for user input
app = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["ask_name", "ask_age", "ask_weight"]
)