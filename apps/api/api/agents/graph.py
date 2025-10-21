from typing import Any, Dict, TypedDict, List

from api.agents.nodes import (
    query_understanding_node as q_node,
    hybrid_search_node as s_node,
    answer_generation_node as a_node,
    source_linking_node as l_node,
)
from langgraph.graph import StateGraph, START, END


class GraphState(TypedDict, total=False):
    query: str
    intent: str
    normalized_query: str
    is_broad_subject: bool
    expanded_keywords: List[str]
    results: List[Dict[str, Any]]
    answer: str
    sources: List[Dict[str, Any]]


async def _understand(state: GraphState) -> GraphState:
    updates = await q_node.run_node(state)  # type: ignore[arg-type]
    state.update(updates)
    return state


async def _search(state: GraphState) -> GraphState:
    updates = await s_node.run_node(state)  # type: ignore[arg-type]
    state.update(updates)
    return state


async def _answer(state: GraphState) -> GraphState:
    updates = await a_node.run_node(state)  # type: ignore[arg-type]
    state.update(updates)
    return state


async def _link(state: GraphState) -> GraphState:
    updates = await l_node.run_node(state)  # type: ignore[arg-type]
    state.update(updates)
    return state


_builder = StateGraph(GraphState)
_builder.add_node("understand_node", _understand)
_builder.add_node("search_node", _search)
_builder.add_node("answer_node", _answer)
_builder.add_node("link_node", _link)
_builder.add_edge(START, "understand_node")
_builder.add_edge("understand_node", "search_node")
_builder.add_edge("search_node", "answer_node")
_builder.add_edge("answer_node", "link_node")
_builder.add_edge("link_node", END)
_app = _builder.compile()


async def run_pipeline(query: str) -> Dict[str, Any]:
    initial: GraphState = {"query": query}
    final_state: GraphState = await _app.ainvoke(initial)
    return {
        "answer": final_state.get("answer", ""), 
        "sources": final_state.get("sources", []),
        "results": final_state.get("results", [])
    }


