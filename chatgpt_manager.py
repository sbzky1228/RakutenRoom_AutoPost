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
        client = OpenAI(api_key = OPENAI_API_KEY)
        
        system_prompt = """あなたは楽天ROOMの商品紹介文を作成するプロです。
        
以下の作成ルールに従って、購買意欲が湧く紹介文を作成してください：

【作成ルール】
1. ターゲット像の明確化
   - 「誰が（どんな生活の中で）」この商品を使っているか具体的に描写する
   - 読み手が自分のことだと感じられる設定を盛り込む

2. ベネフィット（生活の底上げ）を中心に
   - 「買ったことで、暮らしがどう底上げされたか」を最優先で伝える
   - 商品のスペックではなく、購入後の生活の変化に焦点を当てる
   
3. 信頼感と共感を大切に
   - 押し売り感を消し、「ポジティブな共感」で着地させる
   - 読み手の気持ちに寄り添う優しいトーンで書く
   - 一個人の体験・感動を共有する形式が効果的

4. 文字数制限
   -  150文字以内でコンパクトにまとめる
        
5. 文章校正
   - メリットを最初の1行で記載
   - 次にデメリットを記載
   - 最後に再度メリットを記載し、ポジティブな印象で締める"""
        
        prompt = f'''"{item_name}"を楽天ROOMで紹介する紹介文を作成してください。

作成ルールに基づき、以下を意識してください：
- どんな人がどんな場面で使っているかを想像させる
- 使うことでどんなプラスが生まれるかを伝える
- 思わず共感してしまう、温かみのあるトーンで書く'''
        
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        description = response.choices[0].message.content.strip()
        print(f"✓ 商品 '{item_name}' の紹介文を生成しました")
        return description
    
    except Exception as e:
        print(f"✗ ChatGPTで紹介文の生成に失敗しました: {e}")
        return ""
