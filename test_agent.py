from agent import runnable_graph, AgentState

print("🤖 TailorTalk Agent is ready! Type your query below.\n")

while True:
    user_msg = input("You: ")
    if user_msg.lower() in ["exit", "quit"]:
        break
    state = AgentState(user_input=user_msg)
    result = runnable_graph.invoke(state)
    print("Agent:", result["response"])
