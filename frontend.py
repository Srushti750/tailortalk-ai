import streamlit as st
from agent import runnable_graph, AgentState

st.set_page_config(
    page_title="TailorTalk AI", 
    page_icon="🧠",
    layout="centered"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #f0f2f6;
    }
    .assistant-message {
        background-color: #e6f7ff;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📅 TailorTalk AI - Calendar Assistant")
st.markdown("Ask me about your availability or to book a meeting.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Say something..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Create AgentState with required user_input
                state = AgentState(user_input=prompt)
                # Pass the complete state dictionary
                result = runnable_graph.invoke({"state": state})
                # Safely extract response
                response = result.get("state", {}).get("response", "No response generated")
            except Exception as e:
                response = f"Sorry, I encountered an error: {str(e)}"
            
            st.markdown(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})