from langgraph.graph import END, StateGraph

from app.graph import nodes
from app.graph.state import LessonState


def build_graph():
    graph = StateGraph(LessonState)

    graph.add_node("retrieve_context", nodes.retrieve_context)
    graph.add_node("load_memory", nodes.load_memory)
    graph.add_node("generate_lesson", nodes.generate_lesson)
    graph.add_node("evaluate_lesson", nodes.evaluate_lesson)
    graph.add_node("finalize", nodes.finalize)

    graph.set_entry_point("retrieve_context")
    graph.add_edge("retrieve_context", "load_memory")
    graph.add_edge("load_memory", "generate_lesson")
    graph.add_edge("generate_lesson", "evaluate_lesson")
    graph.add_conditional_edges(
        "evaluate_lesson",
        nodes.route_after_evaluation,
        {"retry": "generate_lesson", "finalize": "finalize"},
    )
    graph.add_edge("finalize", END)

    return graph.compile()