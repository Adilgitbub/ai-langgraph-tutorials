from langgraph.graph import StateGraph, START, END
from state import EmailState
from nodes.intake import intake
from nodes.compose import compose_html
from nodes.review import auto_review, optimize, route_evaluation
from nodes.human import test_send_human, human_review, route_decision
from nodes.publish import publish, manual_handling, confirm_log
from db import get_checkpointer

def build_graph():
    graph = StateGraph(EmailState)

    graph.add_node("intake", intake)
    graph.add_node("compose_html", compose_html)
    graph.add_node("auto_review", auto_review)
    graph.add_node("optimize", optimize)
    graph.add_node("test_send_human", test_send_human)
    graph.add_node("human_review", human_review)
    graph.add_node("publish", publish)
    graph.add_node("manual_handling", manual_handling)
    graph.add_node("confirm_log", confirm_log)

    graph.add_edge(START, "intake")
    graph.add_edge("intake", "compose_html")
    graph.add_edge("compose_html", "auto_review")
    graph.add_conditional_edges(
        "auto_review", route_evaluation, {"pass": "test_send_human", "failed": "optimize"}
    )
    graph.add_edge("optimize", "auto_review")
    graph.add_edge("test_send_human", "human_review")
    graph.add_conditional_edges(
        "human_review", route_decision, {"approve": "publish", "reject": "manual_handling"}
    )
    graph.add_edge("publish", "confirm_log")
    graph.add_edge("manual_handling", END)
    graph.add_edge("confirm_log", END)

    checkpointer = get_checkpointer()
    return graph.compile(checkpointer=checkpointer)