#!/usr/bin/env python3
import argparse
import concurrent.futures
from pathlib import Path
from translator.srt_parser import parse_srt
from translator.translator_service import translate_lines
from translator.srt_writer import write_srt
from translator.docx_writer import write_docx
from translator.ai_polisher import polish_texts


def process_language(input_path, input_language, output_language, original_subs):
    """Translate subtitles for a single language and return them (buffered in-memory)."""
    translated_subs = translate_lines(original_subs, src_lang=input_language, dest_lang=output_language)
    print(f"✅ Translated buffer ready for: {output_language}")
    return output_language, translated_subs


def main():
    parser = argparse.ArgumentParser(description="Generate translated SRT language packages and one DOCX")
    parser.add_argument('--input_file', required=True, help="Path to the input SRT file")
    parser.add_argument('--input_language', required=True, help="Source language code (e.g. en)")
    parser.add_argument('--output_languages', nargs='+', required=True, help="Target languages")
    parser.add_argument('--ai_polish', action='store_true', help="Run AI overview on all translations")

    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"File not found: {input_path}")

    original_subs = parse_srt(input_path)
    translations = {}

    # Translate concurrently into in-memory buffers
    print("✨ Translating. Started")
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(args.output_languages)) as executor:
        futures = [
            executor.submit(process_language, input_path, args.input_language, lang, original_subs)
            for lang in args.output_languages
        ]
        for f in concurrent.futures.as_completed(futures):
            lang_code, subs = f.result()
            translations[lang_code] = subs
    print("✨ Translating. Done")

    # AI polish each in-memory buffer if requested
    if args.ai_polish and OpenAI is not None:
        print("🤖 AI polishing. Started")
        for lang_code, subs in list(translations.items()):
            polished = polish_texts(subs, language=lang_code)
            translations[lang_code] = polished
            print(f"🤖 AI polished: {lang_code}")
        print("🤖 AI polishing. Done")
    else:
        print("🤖 AI polishing skipped")

    # Write SRT files from polished buffers
    for lang_code, subs in translations.items():
        output_file = input_path.with_name(f"{input_path.stem}_{lang_code}{input_path.suffix}")
        write_srt(subs, output_file)
        print(f"✅ Generated SRT: {output_file}")

    # Generate single DOCX file using all polished translations
    docx_output = input_path.with_suffix('.docx')
    write_docx(
        original_subs=original_subs,
        translations=translations,
        output_languages=args.output_languages,
        input_language=args.input_language,
        output_file=docx_output
    )
    print(f"📄 DOCX generated: {docx_output}")


if __name__ == "__main__":
    main()
