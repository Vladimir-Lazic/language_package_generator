from deep_translator import GoogleTranslator

def translate_lines(subtitles, src_lang, dest_lang):
    translated = []
    translator = GoogleTranslator(source=src_lang, target=dest_lang)
    for s in subtitles:
        if s['text'].strip():
            text = translator.translate(s['text'])
        else:
            text = ''
        translated.append({'start': s['start'], 'end': s['end'], 'text': text})
    return translated
