from src.llm import chat

history = []

if __name__ == "__main__":
    print("Chatbot sẵn sàng. Gõ 'exit' để thoát.\n")
    while True:
        q = input("Bạn: ")
        if q.lower() in ("exit", "quit"):
            break
        history.append({"role": "user", "content": q})
        answer = chat(history)
        history.append({"role": "assistant", "content": answer})
        print("AI:", answer, "\n")