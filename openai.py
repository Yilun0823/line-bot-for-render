import openai

# 設置你的 OpenAI GPT-3 密鑰
openai.api_key = "OPENAI_API_KEY"

def generate_text(prompt):
    response = openai.Completion.create(
        engine="davinci",  # 使用 GPT-3.5 的 davinci 引擎
        prompt=prompt,
        max_tokens=50  # 生成的最大標記數
    )
    return response.choices[0].text.strip()

if __name__ == "__main__":
    prompt = "在未來的世界里，人類和機器將會"
    generated_text = generate_text(prompt)
    print("生成的文本：", generated_text)
