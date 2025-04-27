# groq_llama_helper.py
from groq import Groq

client = Groq(api_key="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")  # Fill in from environment

def groq_llama_invoke(messages):
    completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=messages[-8:],  # Last 8 messages + system prompt if needed
        temperature=0.7,
        max_completion_tokens=1024,
        top_p=1.0,
        stream=False,
        stop=None,
    )

    return completion.choices[0].message.content.strip()

def langchain_to_groq_messages(messages):
    groq_messages = []
    for msg in messages:
        if msg.type == "human":
            role = "user"
        elif msg.type == "ai":
            role = "assistant"
        else:
            raise ValueError(f"Unknown message type: {msg.type}")
        groq_messages.append({"role": role, "content": msg.content})
    return groq_messages
