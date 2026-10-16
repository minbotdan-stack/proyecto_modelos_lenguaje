import ollama
r = ollama.chat(model='qwen2.5:14b',
                messages=[{'role': 'user', 'content': 'Responde solo: ok'}])
print(r['message']['content'])