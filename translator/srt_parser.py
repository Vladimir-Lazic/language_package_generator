import re

def parse_srt(file_path):
    """Parse SRT file into list of dicts with time and text."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = r'(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\s+([\s\S]*?)(?=\n\n|\Z)'
    matches = re.findall(pattern, content)
    subtitles = []
    for num, start, end, text in matches:
        clean_text = ' '.join(line.strip() for line in text.splitlines())
        subtitles.append({
            "num": num,
            "start": start,
            "end": end,
            "text": clean_text
        })
    return subtitles
