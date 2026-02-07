
import os
import openai

def generate_item_descriptions_with_chatgpt(items):
    """
    ChatGPTを使用して商品紹介文を生成する関数

    Args:
        items (list): 商品情報のリスト（各要素は辞書形式）
    """
    # OpenAI APIキーを環境変数から取得
    openai.api_key = os.getenv('OPENAI_API_KEY')

    if not openai.api_key:
        print("OpenAI APIキーが設定されていません。紹介文生成をスキップします。")
        return

    for item in items:
        if 'description' not in item or not item['description']:
            # 商品名と価格から紹介文を生成
            prompt = f"以下の商品の魅力を伝える紹介文を100文字以内で作成してください。\n商品名: {item.get('name', '')}\n価格: {item.get('price', '')}"

            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "あなたは商品紹介の専門家です。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=100
                )
                generated_description = response.choices[0].message.content.strip()
                item['description'] = generated_description
                print(f"商品 '{item['name']}' の紹介文を生成しました。")
            except Exception as e:
                print(f"紹介文生成エラー: {e}")
                item['description'] = "紹介文生成に失敗しました。"