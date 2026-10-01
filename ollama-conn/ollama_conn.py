from ollama import chat
from ollama import ChatResponse

content = input("Enter your prompt: ")

response: ChatResponse = chat(
  model='qwen2.5:7b',
  messages=[
    {
      'role': 'user',
      'content': content,
    },
  ],
)

print(response['message']['content'])
print(response.message.content)