# test_intake_app.py
import streamlit as st
import os, uuid
from nodes.graph import build_graph

st.title("Newsletter Intake — Test Harness")

message = st.text_area(
    "Your message", height=200,
    placeholder="Hi, please prepare a newsletter...\ncontent: ...\nsnap: refer attached for layout\npng: add in middle..."
)
snap_file = st.file_uploader("Reference snap (optional)", type=["png", "jpg", "jpeg"])
png_file = st.file_uploader("Image to embed (optional)", type=["png"])
bcc_input = st.text_input("BCC (optional, comma-separated — leave blank to test the missing-field flow)")

if st.button("Send"):
    run_dir = f"./uploads/{uuid.uuid4().hex[:8]}"
    os.makedirs(run_dir, exist_ok=True)

    snap_path = None
    if snap_file:
        snap_path = os.path.join(run_dir, "client_snap.png")
        open(snap_path, "wb").write(snap_file.read())

    png_path = None
    if png_file:
        png_path = os.path.join(run_dir, "embed_image.png")
        open(png_path, "wb").write(png_file.read())

    initial_state = {
        "input": message,
        "client_snap_path": snap_path,
        "embed_image_path": png_path,
        "bcc": [b.strip() for b in bcc_input.split(",")] if bcc_input else None,
        "subject": None,
    }

    print("\n--- INTAKE INPUT ---\n", initial_state)
    
    # result= workflow.invoke(initial_state);
    # result = intake(initial_state)
    result =build_graph().invoke(initial_state, config={"configurable": {"thread_id": 'thread-comp1'}})
    print("\n--- INTAKE OUTPUT ---\n", result)

    if result.get("needs_clarification"):
        st.warning(result["clarification_question"])
    else:
        st.success("Intake complete — check terminal for full output.")