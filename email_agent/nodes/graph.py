from langgraph.graph import StateGraph, START, END
from state import EmailState
from nodes.intake import intake
from nodes.compose import compose_html
from nodes.review import auto_review, optimize, route_evaluation
from nodes.human import test_send_human, human_review, route_decision
from nodes.publish import publish, manual_handling, confirm_log
from db import get_checkpointer

def build_graph():
        email_graph = StateGraph(EmailState)

        email_graph.add_node("intake", intake)
        email_graph.add_node("compose_html", compose_html)
        email_graph.add_node("auto_review", auto_review)
        email_graph.add_node("optimize", optimize)
        email_graph.add_node("test_send_human", test_send_human)
        email_graph.add_node("human_review", human_review)
        email_graph.add_node("publish", publish)
        email_graph.add_node("manual_handling", manual_handling)
        email_graph.add_node("confirm_log", confirm_log)

        # email_graph.add_edge(START, "human_review")
        # # email_graph.add_edge("intake", "compose_html")
        # email_graph.add_edge("human_review", "publish")
        # email_graph.add_edge("publish", END)

        email_graph.add_edge(START, "intake")
        email_graph.add_edge("intake", "compose_html")
        email_graph.add_edge("compose_html", "auto_review")
        email_graph.add_conditional_edges(
            "auto_review", route_evaluation, {"pass": "test_send_human", "failed": "optimize"}
        )
        email_graph.add_edge("optimize", "auto_review")
        email_graph.add_edge("test_send_human", "human_review")
        email_graph.add_conditional_edges(
            "human_review", route_decision, {"approve": "publish", "reject": "manual_handling"}
        )
        email_graph.add_edge("publish", "confirm_log")
        email_graph.add_edge("manual_handling", END)
        email_graph.add_edge("confirm_log", END)

        checkpointer = get_checkpointer()
        return email_graph.compile(checkpointer=checkpointer)