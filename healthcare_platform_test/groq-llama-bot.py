from groq import Groq

# Groq key: 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

client = Groq()
prompt = '''
You are vedya, an ai assistant, giving user the information to user about coffees. anser in 2-3 lines only
'''
messages = [
    {
        "role": "system",
        "content": (prompt)
    }
]

def get_response(user_input):
    messages.append({"role": "user", "content": user_input})
    completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[messages[0]] + messages[-8:], 
        temperature=1.0,
        max_completion_tokens=1024,
        top_p=1.0,
        stream=True,
        stop=None,
    )

    response_chunks = []
    for chunk in completion:
        delta = chunk.choices[0].delta.content or ""
        print(delta, end="", flush=True)
        response_chunks.append(delta)
    print()

    response_text = "".join(response_chunks)
    messages.append({"role": "assistant", "content": response_text})
    return response_text

if __name__ == "__main__":
    print("bot: How can I help you today?")
    print()
    while True:
        # print("\n")
        user_input = input("You: ")
        if user_input.strip().lower() in ("exit", "quit", "bye"):
            print("bot: Goodbye!")
            break
        print("Vedya: ", end='')
        get_response(user_input)
        print()
