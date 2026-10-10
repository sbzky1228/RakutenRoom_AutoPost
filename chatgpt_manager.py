"""
ChatGPT マネージャー - ChatGPTを使用した紹介文生成
"""
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL


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

        system_prompt = (
            "あなたは楽天ROOMの商品紹介文を作成するプロです。\n\n"
            "以下の作成ルールに従って、購買意欲が湧く紹介文を作成してください。\n\n"
            "【作成ルール】\n"
            "1. ターゲット像の明確化\n"
            "   - 「誰が（どんな生活の中で）」この商品を使っているか具体的に描写する\n"
            "   - 読み手が自分のことだと感じられる設定を盛り込む\n\n"
            "2. ベネフィット（生活の底上げ）を中心に\n"
            "   - 「買ったことで、暮らしがどう底上げされたか」を最優先で伝える\n"
            "   - 商品のスペックではなく、購入後の生活の変化に焦点を当てる\n\n"
            "3. 信頼感と共感を大切に\n"
            "   - 押し売り感を消し、「ポジティブな共感」で着地させる\n"
            "   - 読み手の気持ちに寄り添う優しいトーンで書く\n"
            "   - 一個人の体験・感動を共有する形式が効果的\n"
            "   - 文章のトーンが統一されているか確認する\n"
            "   - 読み手が「自分も使ってみたい」と思えるような文章にする\n\n"
            "4. 文字数制限\n"
            "   - 1～3行以内にすること\n"
            "   - 150文字以内でコンパクトにまとめる\n\n"
            "5. 文章校正\n"
            "   - 一番のメリットを最初の1行で記載\n"
            "   - 2行目以降はデメリット、メリットの順で最後はメリットで終わるようにしポジティブな印象で締める\n"
            "   - 読みやすい文章にするため、句読点の使い方に注意する\n"
            "   - 誤字脱字がないか確認する\n"
            "   - 必ず句読点（。）のあとに改行（\\n）を入れること\n"
            "   - 出力形式の例：\n"
            "     「忙しい毎日でも、これひとつで気分が上がる。\n"
            "      使うたびに、丁寧な暮らしを実感できる。\n"
            "      #楽天ROOM #商品紹介 #おすすめ」\n"
            "6. 検索エンジン最適化（SEO）を意識\n"
            "   - タグを意識した文章にする\n"
            "   - 商品名や関連キーワードを自然に文章に組み込む\n"
            "   - 文章の最後に「#楽天ROOM #商品紹介」などの商品に適したハッシュタグを3つ入れる\n\n"
        )

        prompt = (
            f'"{item_name}"を楽天ROOMで紹介する紹介文を作成してください。\n\n'
            "作成ルールに基づき、以下を意識してください：\n"
            "- どんな人がどんな場面で使っているかを想像させる\n"
            "- 使うことでどんなプラスが生まれるかを伝える\n"
            "- 思わず共感してしまう、温かみのあるトーンで書く"
        )

        # GPT-5/6系はmax_tokens/temperatureが使えず、推論トークンも出力枠を消費するため
        # max_completion_tokensを広めに取り、推論量は最小限（low）にする
        # （noneは一部モデル(gpt-6.1-sol等)で非対応のため、全モデルで使えるlowを使う）
        params = {"max_completion_tokens": 2000}
        if OPENAI_MODEL.startswith(("gpt-5", "gpt-6")):
            params["reasoning_effort"] = "low"
        else:
            params["temperature"] = 0.7

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            **params,
        )

        content = response.choices[0].message.content
        # 行末の余分な空白（Markdown改行用のスペース等）を除去する
        description = "\n".join(line.rstrip() for line in (content or "").strip().splitlines())
        if not description:
            print(f"✗ ChatGPTの応答が空でした (finish_reason={response.choices[0].finish_reason})")
            return ""
        print(f"✓ 商品 '{item_name}' の紹介文を生成しました")
        return description

    except Exception as e:
        print(f"✗ ChatGPTで紹介文の生成に失敗しました: {e}")
        return ""
