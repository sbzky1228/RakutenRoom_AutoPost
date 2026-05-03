"""
ChatGPT マネージャー - ChatGPTを使用した紹介文生成
"""
from openai import OpenAI
from config import OPENAI_API_KEY


def generate_description(item_name: str) -> str:
    """
    ChatGPTで商品紹介文を生成
    
    Args:
        item_name: 商品名
    
    Returns:
        str: 生成された紹介文
    """
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = f'"{item_name}"を楽天ROOMで紹介するため、200文字以内で紹介文を作成してください。紹介文を見た人が商品を購入することで生活がどのように改善されるとかが伝わるような紹介文をお願いします。'
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "あなたは楽天ROOMの商品紹介文を作成するプロです。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        description = response.choices[0].message.content.strip()
        print(f"✓ 商品 '{item_name}' の紹介文を生成しました")
        return description
    
    except Exception as e:
        print(f"✗ ChatGPTで紹介文の生成に失敗しました: {e}")
        return ""
