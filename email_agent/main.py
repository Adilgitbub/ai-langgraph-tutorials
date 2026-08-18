from graph import build_graph
from db import create_review_token

def main():
    workflow = build_graph()

    thread_id = "test-run-001"
    token = create_review_token(thread_id)
    print("Use this token in Postman:", token)

    initial_state = {
        "input": "Your email content here",
        "iteration": 0,
        "max_iteration": 3,
        "published": False,
        "use_snap_as_template": False,
    }

    result = workflow.invoke(
        initial_state,
        config={"configurable": {"thread_id": thread_id}}
    )
    print(result)

if __name__ == "__main__":
    main()