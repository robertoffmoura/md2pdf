# md2pdf

A minimalist, high-fidelity Markdown-to-PDF converter written in Python. It parses Markdown files containing LaTeX mathematical formulas, renders them using KaTeX, and outputs a print-perfect PDF using a headless Chrome instance via Selenium.

## Features

- **High-Fidelity PDF Output**: Employs headless Google Chrome to print the rendered HTML layout to PDF, preserving pagination, fonts, margins, and alignments.
- **LaTeX Math Support**: Seamlessly renders inline math (`$...$`) and block math (`$$...$$`) via **KaTeX**.
- **Minimal Dependencies**: Requires only Python, Chrome/Chromium, and the Python `selenium` library.
- **Polished Typography**: Features premium, print-optimized font pairings (Source Serif 4, Source Sans 3, and Source Code Pro) loaded dynamically from Google Fonts.
- **Clean Markdown Parser**: A custom regex-based parser that translates standard Markdown elements into clean HTML while protecting LaTeX delimiters from markdown interference.

---

## Installation

### 1. Prerequisites
- **Python 3.x**
- **Google Chrome** or **Chromium** browser installed on your system.

### 2. Install Python Package
Install the Python dependencies via `pip`. It is recommended to use a virtual environment:

```bash
# Create and activate a virtual environment (optional)
python3 -m venv venv
source venv/bin/activate

# Install Selenium
pip install selenium
```

*Note: Selenium Manager will automatically locate and download the appropriate driver (`chromedriver`) for your Chrome version. No manual driver setup is needed.*

---

## Usage

Run the converter from your terminal:

```bash
python3 md2pdf.py <input.md> [output.pdf]
```

- **`<input.md>`**: The path to your input Markdown file.
- **`[output.pdf]`** *(Optional)*: The path for the output PDF file. If omitted, it defaults to the input file's name with a `.pdf` extension in the same directory.

### Example

Given a file `document.md` containing:

```markdown
# Physics Report

Let's discuss the Maxwell's equations. In differential form, Faraday's law of induction is:

$$\nabla \times \mathbf{E} = -\frac{\partial \mathbf{B}}{\partial t}$$

Where:
- $\mathbf{E}$ is the electric field.
- $\mathbf{B}$ is the magnetic field.
```

Convert it using:

```bash
python3 md2pdf.py document.md
```

This generates `document.pdf` with properly formatted headers, bulleted lists, and beautiful, high-resolution mathematical equations.

---

## Supported Markdown Elements

- **Headings**: `#` (H1), `##` (H2), and `###` (H3).
- **Inline Math**: `$ ... $` for inline formulas (e.g. $E = mc^2$).
- **Block Math**: `$$ ... $$` for centered display equations.
- **Unordered Lists**: `- item` and indented `- subitem`.
- **Text Styling**: `**bold**`, `*italic*`, and inline `` `code` `` fragments.
- **Paragraphs**: Contiguous lines are automatically joined into standard justified paragraphs.

---

## How It Works

1. **Preprocessing**: The script reads the input Markdown, identifies math blocks, and translates markdown elements (headers, lists, styling) to semantic HTML tags.
2. **HTML Generation**: It constructs a self-contained HTML document loading **KaTeX** stylesheets/scripts and applying typography rules.
3. **Rendering & Math Processing**: Selenium starts a headless Chrome browser, loads the HTML, and waits for KaTeX's auto-render extension to process the mathematical formatting.
4. **PDF Printing**: Headless Chrome's print-to-PDF functionality (`Page.printToPDF` via Chrome DevTools Protocol) is triggered with A4 measurements and standard margins to produce a high-fidelity document.
