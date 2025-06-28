import streamlit as st
from agent import runnable_graph, AgentState

st.set_page_config(page_title="TailorTalk AI", page_icon="🧠")

st.title("📅 TailorTalk AI - Calendar Assistant")
st.markdown("Ask me about your availability or to book a meeting.")

# Keep chat history across interactions
if "history" not in st.session_state:
    st.session_state.history = []

# Chat input box
user_input = st.chat_input("Say something...")

if user_input:
    st.session_state.history.append({"role": "user", "content": user_input})

    # Run LangGraph agent
    with st.spinner("Thinking..."):
        state = AgentState(user_input=user_input)
        result = runnable_graph.invoke(state)

        # Safe access of response
        response = result.response if hasattr(result, "response") else result.get("response", "❌ No response.")
        st.session_state.history.append({"role": "assistant", "content": response})

# Display conversation history
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
