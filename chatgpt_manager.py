"""
ChatGPT マネージャー - ChatGPTを使用した紹介文生成
"""
from typing import Dict
import openai
from config import OPENAI_API_KEY


class ChatGPTManager:
    """ChatGPT APIを操作するクラス"""
    
    def __init__(self):
        openai.api_key = OPENAI_API_KEY
    
    def generate_description(self, item_name: str) -> str:
        """
        ChatGPTで商品紹介文を生成
        
        Args:
            item_name: 商品名
        
        Returns:
            str: 生成された紹介文
        """
        try:
            prompt = f'"{item_name}"を楽天ROOMに紹介するため、200文字以内で紹介文を作成して。'
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたは楽天ROOMの商品紹介文を作成するアシスタントです。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            description = response['choices'][0]['message']['content'].strip()
            print(f"✓ 商品 '{item_name}' の紹介文を生成しました")
            return description
        
        except Exception as e:
            print(f"✗ ChatGPTで紹介文の生成に失敗しました: {e}")
            return ""


def generate_descriptions_for_items(items: list) -> Dict:
    """
    複数の商品に対して紹介文を生成
    
    Args:
        items: 商品リスト
    
    Returns:
        Dict: item_codeをキーとした紹介文の辞書
    """
    manager = ChatGPTManager()
    descriptions = {}
    
    for item in items:
        item_code = item.get('ItemCode', '')
        item_name = item.get('ItemName', '')
        
        if item_code and item_name:
            description = manager.generate_description(item_name)
            descriptions[item_code] = description
    
    return descriptions
