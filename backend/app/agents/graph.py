from typing import TypedDict

from langgraph.graph import END, StateGraph


class GraphState(TypedDict, total=False):
	query: str
	mode: str


def build_graph():
	graph = StateGraph(GraphState)

	def passthrough(state: GraphState) -> GraphState:
		return state

	graph.add_node("start", passthrough)
	graph.set_entry_point("start")
	graph.add_edge("start", END)
	return graph.compile()
