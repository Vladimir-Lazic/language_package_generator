# SRT to DOCX Converter

This is a simple Python tool that converts `.srt` subtitle files into a `.docx` Word document with a clean table layout:

- Timecode (start → end without milliseconds)
- German (empty for translation)
- English (subtitle text from the SRT)
- Black table borders for a clean, printable format

---

## Requirements

- macOS
- Python 3.8 or newer
- pip (Python package manager)
- Internet connection (to install dependencies)

---

## Install Python on macOS

1. Check if Python is already installed:

   ```bash
   python3 --version
   ```

2. If not installed, install Homebrew (if you don’t have it):

   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

3. Then install Python:

   ```bash
   brew install python
   ```

4. Verify installation:

   ```bash
   python3 --version
   pip3 --version
   ```

---

## Project Setup

1. Download or clone the project into a folder.

2. Open Terminal and navigate to the folder:

   ```bash
   cd path/to/your/project
   ```

3. (Optional) Create a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### Basic usage

Convert an SRT file to DOCX in the same folder:

```bash
python srt_to_docx.py subtitles.srt
```

This will generate:

```
subtitles.docx
```

### Custom output path

```bash
python srt_to_docx.py subtitles.srt output/Dialogue_List.docx
```

---

## Example Output

| Timecode              | German | English              |
|-----------------------|--------|-----------------------|
| 00:00:01 --> 00:00:05 |        | Hello, everyone!      |
| 00:00:06 --> 00:00:09 |        | Welcome to the show.  |

- The table has black borders.
- The German column is empty for translation work.
- The English text is pulled directly from the SRT file.

---

## Deactivate Virtual Environment (Optional)

```bash
deactivate
```

---

## License

This project is released under the MIT License.

---

## Author

Created for fast and clean subtitle-to-dialogue conversion workflows.
