def generate_text(prompt):
    print("調用 OpenAI API 前...")
    try:
        response = openai.Completion.create(
            engine="davinci",  # 使用 GPT-3.5 的 davinci 引擎
            prompt=prompt,
            max_tokens=50  # 生成的最大標記數
        )
        print("OpenAI API 響應：", response)
        generated_text = response.choices[0].text.strip()
        print("生成的文本：", generated_text)
        return generated_text
    except Exception as e:
        print("調用 OpenAI API 時出現異常：", e)
        return "抱歉，出了點問題，無法生成回答。"
