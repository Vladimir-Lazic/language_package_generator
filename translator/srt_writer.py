def write_srt(subtitles, output_path):
    """Write translated subtitles back to an SRT file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, entry in enumerate(subtitles, start=1):
            f.write(f"{i}\n")  # numbering regenerated automatically
            f.write(f"{entry['start']} --> {entry['end']}\n")
            f.write(f"{entry['text']}\n\n")
