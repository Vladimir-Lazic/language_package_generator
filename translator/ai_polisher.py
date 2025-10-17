import os

try:
    from openai import OpenAI
    # Initialize once at import time
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception:
    OpenAI = None

def polish_texts(translations, language):
    """
    Run translations through AI to improve grammar and style.
    Expects translations to be a list of dicts: [{'start':..., 'end':..., 'text':...}]
    Returns a polished list in the same format.
    """
    texts = [t['text'] for t in translations]
    polished = []

    for text in texts:
        if not text.strip():
            polished.append("")
            continue

        prompt = f"""
        You are a professional native {language} speaker and editor.
        Please polish and correct the following subtitle text, making sure it's clear, natural, and grammatically correct.
        Do NOT translate it to another language. Just improve style and fix issues.
        Text: "{text}"
        Polished:
        """
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": "You are a language editor."},
                          {"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=256
            )
            fixed = response.choices[0].message.content.strip()
            polished.append(fixed)
        except Exception as e:
            print(f"⚠️ AI polish failed for text: {text} — {e}")
            polished.append(text)

    # Return polished version in the same structure
    return [
        {"start": translations[i]["start"], "end": translations[i]["end"], "text": polished[i]}
        for i in range(len(translations))
    ]
