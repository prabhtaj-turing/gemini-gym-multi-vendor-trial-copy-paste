# File Conversion System for Simulated APIs

This system converts various file formats to JSON representations that can be handled by simulated Google APIs (Drive, Sheets, Slides, Docs).

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create your input folder structure:
```
input-data/
  files/          # Put your files here
    document.docx
    spreadsheet.xlsx
    presentation.pptx
    image.png
    etc.
```

## Usage

Run the conversion script:

```bash
python main.py files
```

Process a specific subfolder (use quotes for paths with spaces):

```bash
python main.py "files/MP-42825 Files-20250619T235923Z-1-001/MP-42825 Files/F111"
```

Or specify a custom output folder:

```bash
python main.py files --output-folder converted_files
```

**Note:** Input paths should be relative to the `input-data/` folder. Don't include `input-data/` in your path argument.

## File Type Conversions

| Input Format | Output Format | API Simulation |
|-------------|---------------|----------------|
| `.xlsx`, `.xls` | Google Sheets JSON | Google Sheets API |
| `.pptx`, `.ppt` | Google Slides JSON | Google Slides API |
| `.docx`, `.doc` | Google Docs JSON | Google Docs API (via Drive) |
| `.txt`, `.html`, `.csv`, etc. | Google Drive JSON | Google Drive API |
| `.pdf`, `.png`, `.jpg`, etc. | Google Drive JSON (base64) | Google Drive API |

## Output Structure

The system creates JSON files in the `output-data/` folder that match the structure expected by the simulated APIs:

### Google Sheets Format
```json
{
  "id": "sheet_abc123",
  "name": "My Spreadsheet",
  "mimeType": "application/vnd.google-apps.spreadsheet",
  "sheets": [...],
  "data": {
    "Sheet1!A1:C10": [["Header1", "Header2", "Header3"], ...]
  }
}
```

**Note:** Sheet data ranges use **A1 notation** format (e.g., `"Sheet1!A1:C10"`) which is compatible with Google Sheets API expectations. Datetime values from Excel files are automatically converted to ISO format strings.

### Google Slides Format
```json
{
  "presentationId": "pres_abc123",
  "title": "My Presentation",
  "slides": [
    {
      "objectId": "slide1_page1",
      "pageType": "SLIDE",
      "pageElements": [...]
    }
  ]
}
```

### Google Drive Format
```json
{
  "id": "file_abc123",
  "name": "my_file.txt",
  "mimeType": "text/plain",
  "content": {
    "data": "file content or base64 data",
    "encoding": "text" | "base64"
  }
}
```

## Module Structure

- `main.py` - Main conversion pipeline
- `gdrive_converter.py` - Handles general files and text/binary content
- `gsheets_converter.py` - Converts Excel files to Google Sheets format
- `gslides_converter.py` - Converts PowerPoint files to Google Slides format

## Examples

### Convert all files in the 'files' subfolder:
```bash
python main.py files
```

### Convert a specific subfolder with spaces in the name:
```bash
python main.py "files/MP-42825 Files-20250619T235923Z-1-001/MP-42825 Files/F111"
```

### Convert with custom output folder:
```bash
python main.py files --output-folder my_converted_files
```

### Check available input subfolders:
```bash
python main.py nonexistent_folder
# Will show available subfolders and files in input-data/
``` 