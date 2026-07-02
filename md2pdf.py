"""
Convert a Markdown file with LaTeX math to a polished PDF file using KaTeX
for math rendering and Selenium (headless Chrome) for printing.

Usage: python3 md2pdf.py <input.md> [output.pdf]
"""
import re
import sys
import os
import tempfile
import base64
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

# Execution logic is wrapped in main() at the bottom


# --- Step 1: Protect math blocks from markdown processing ---
# Extract display math $$ ... $$ and inline math $ ... $
# We'll convert markdown manually since we need fine control.

def md_to_html(md):
	"""Simple markdown to HTML converter that preserves LaTeX math."""
	lines = md.split('\n')
	html_lines = []
	in_list = False
	in_sublist = False
	i = 0

	while i < len(lines):
		line = lines[i]

		# Display math block
		if line.strip().startswith('$$'):
			if in_list:
				if in_sublist:
					html_lines.append('</ul></li>')
					in_sublist = False
				html_lines.append('</ul>')
				in_list = False
			# Collect all lines until closing $$
			math_content = []
			if line.strip() == '$$':
				i += 1
				while i < len(lines) and lines[i].strip() != '$$':
					math_content.append(lines[i])
					i += 1
				i += 1  # skip closing $$
			elif line.strip().endswith('$$') and line.strip() != '$$':
				# Single-line: $$...$$
				inner = line.strip()[2:-2]
				math_content.append(inner)
				i += 1
			else:
				# Opens with $$ but doesn't close on same line
				rest = line.strip()[2:]
				if rest:
					math_content.append(rest)
				i += 1
				while i < len(lines) and not lines[i].strip().endswith('$$'):
					math_content.append(lines[i])
					i += 1
				if i < len(lines):
					last = lines[i].strip()
					if last != '$$':
						math_content.append(last[:-2])
					i += 1

			latex = '\n'.join(math_content).strip()
			html_lines.append(f'<div class="math-display">$${latex}$$</div>')
			continue

		# Horizontal Rule
		if line.strip() == '---':
			if in_list:
				if in_sublist:
					html_lines.append('</ul></li>')
					in_sublist = False
				html_lines.append('</ul>')
				in_list = False
			html_lines.append('<hr>')
			i += 1
			continue

		# Headers
		if line.startswith('###'):
			if in_list:
				if in_sublist:
					html_lines.append('</ul></li>')
					in_sublist = False
				html_lines.append('</ul>')
				in_list = False
			html_lines.append(f'<h3>{process_inline(line.lstrip("#").strip())}</h3>')
			i += 1
			continue
		if line.startswith('##'):
			if in_list:
				if in_sublist:
					html_lines.append('</ul></li>')
					in_sublist = False
				html_lines.append('</ul>')
				in_list = False
			html_lines.append(f'<h2>{process_inline(line.lstrip("#").strip())}</h2>')
			i += 1
			continue
		if line.startswith('#'):
			if in_list:
				if in_sublist:
					html_lines.append('</ul></li>')
					in_sublist = False
				html_lines.append('</ul>')
				in_list = False
			html_lines.append(f'<h1>{process_inline(line.lstrip("#").strip())}</h1>')
			i += 1
			continue

		# List items (detect indent level)
		if line.strip().startswith('- '):
			# Determine indent level
			stripped = line.rstrip()
			leading_ws = len(stripped) - len(stripped.lstrip())
			is_sub = leading_ws >= 2 or stripped.startswith('\t-') or stripped.startswith('\t\t-')
			text = line.strip().lstrip('- ').strip()

			if is_sub:
				if not in_list:
					html_lines.append('<ul>')
					in_list = True
				if not in_sublist:
					html_lines.append('<li><ul>')
					in_sublist = True
				html_lines.append(f'<li>{process_inline(text)}</li>')
			else:
				if in_sublist:
					html_lines.append('</ul></li>')
					in_sublist = False
				if not in_list:
					html_lines.append('<ul>')
					in_list = True
				html_lines.append(f'<li>{process_inline(text)}</li>')
			i += 1
			continue

		# Close any open list
		if in_list and line.strip() == '':
			if in_sublist:
				html_lines.append('</ul></li>')
				in_sublist = False
			html_lines.append('</ul>')
			in_list = False
			i += 1
			continue

		# Empty line
		if line.strip() == '':
			i += 1
			continue

		# Regular paragraph — collect contiguous lines
		para_lines = [line]
		i += 1
		while i < len(lines):
			next_line = lines[i]
			if (next_line.strip() == '' or
				next_line.startswith('#') or
				next_line.strip().startswith('- ') or
				next_line.strip().startswith('$$')):
				break
			para_lines.append(next_line)
			i += 1

		if in_list:
			if in_sublist:
				html_lines.append('</ul></li>')
				in_sublist = False
			html_lines.append('</ul>')
			in_list = False

		paragraph = ' '.join(l.strip() for l in para_lines)
		html_lines.append(f'<p>{process_inline(paragraph)}</p>')

	# Close any remaining open list
	if in_sublist:
		html_lines.append('</ul></li>')
	if in_list:
		html_lines.append('</ul>')

	return '\n'.join(html_lines)


def process_inline(text):
	"""Process inline markdown: bold, italic, code, links, images, inline math."""
	# Protect escaped characters first (so they are not parsed as markdown syntax)
	escaped_chars = [
		(r'\\\\', '%%ESC_BS%%', '\\'),
		(r'\\\*', '%%ESC_AST%%', '*'),
		(r'\\\_', '%%ESC_UND%%', '_'),
		(r'\\`', '%%ESC_GRA%%', '`'),
		(r'\\\[', '%%ESC_LBR%%', '['),
		(r'\\\]', '%%ESC_RBR%%', ']'),
		(r'\\\$', '%%ESC_DOL%%', '$'),
	]
	for pattern, placeholder, _ in escaped_chars:
		text = re.sub(pattern, placeholder, text)

	# Protect inline math next — replace with placeholders
	math_parts = []
	def save_math(m):
		math_parts.append(m.group(0))
		return f'%%MATH{len(math_parts)-1}%%'

	text = re.sub(r'(?<!\$)\$(?!\$)(.+?)\$(?!\$)', save_math, text)

	# Images: ![alt](url)
	text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" />', text)
	# Links: [text](url)
	text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
	# Code
	text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
	# Bold
	text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
	# Italic
	text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)

	# Restore math
	for i, m in enumerate(math_parts):
		text = text.replace(f'%%MATH{i}%%', f'<span class="math-inline">{m}</span>')

	# Restore escaped characters to their literal symbols
	for _, placeholder, literal in escaped_chars:
		text = text.replace(placeholder, literal)

	return text


def main():
	if len(sys.argv) < 2:
		print("Usage: md2pdf <input.md> [output.pdf]")
		sys.exit(1)

	INPUT = sys.argv[1]
	if len(sys.argv) >= 3:
		OUTPUT_PDF = sys.argv[2]
	else:
		OUTPUT_PDF = os.path.splitext(os.path.basename(INPUT))[0] + ".pdf"

	with open(INPUT, "r") as f:
		md_text = f.read()

	TITLE = os.path.splitext(os.path.basename(INPUT))[0].replace('_', ' ').title()

	body_html = md_to_html(md_text)

	from pathlib import Path
	base_uri = Path(INPUT).resolve().parent.as_uri() + "/"

	full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<base href="{base_uri}">
<title>{TITLE}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.22/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.22/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.22/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body, {{
    delimiters: [
      {{left: '$$', right: '$$', display: true}},
      {{left: '$', right: '$', display: false}}
    ],
    throwOnError: false
  }});"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Source+Code+Pro:wght@400&display=swap');

  :root {{
    --text: #1a1a2e;
    --muted: #555;
    --accent: #2d5aa0;
    --border: #d0d7de;
    --bg-code: #f6f8fa;
  }}

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe WPC', 'Segoe UI', system-ui, 'Ubuntu', 'Droid Sans', sans-serif;
    font-size: 11pt;
    line-height: 1.7;
    color: var(--text);
    max-width: 680px;
    margin: 0 auto;
    padding: 48px 32px;
  }}

  h1 {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe WPC', 'Segoe UI', system-ui, 'Ubuntu', 'Droid Sans', sans-serif;
    font-size: 24pt;
    font-weight: 700;
    line-height: 1.25;
    margin: 36px 0 16px 0;
    padding-bottom: 4px;
    border-bottom: 1px solid var(--border);
    color: var(--text);
    letter-spacing: -0.02em;
  }}

  h2 {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe WPC', 'Segoe UI', system-ui, 'Ubuntu', 'Droid Sans', sans-serif;
    font-size: 17pt;
    font-weight: 700;
    line-height: 1.25;
    margin: 32px 0 16px 0;
    padding-bottom: 4px;
    border-bottom: 1px solid var(--border);
    color: var(--text);
    letter-spacing: -0.01em;
  }}

  h3 {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe WPC', 'Segoe UI', system-ui, 'Ubuntu', 'Droid Sans', sans-serif;
    font-size: 13pt;
    font-weight: 600;
    margin: 24px 0 6px 0;
    color: var(--accent);
  }}

  p {{
    margin: 10px 0;
    text-align: justify;
    hyphens: auto;
  }}

  hr {{
    border: 0;
    height: 1px;
    background: var(--border);
    margin: 12px 0 20px 0;
  }}

  ul {{
    margin: 4px 0;
    margin-left: 16px;
    padding-left: 24px;
  }}

  li {{
    margin-bottom: 5px;
  }}

  li:has(> ul) {{
    list-style-type: none;
  }}

  li > ul {{
    margin-top: 4px;
    margin-left: 16px;
    padding-left: 24px;
  }}

  strong {{
    font-weight: 600;
  }}

  code {{
    font-family: 'Source Code Pro', 'Menlo', 'Consolas', monospace;
    font-size: 0.9em;
    background: var(--bg-code);
    padding: 1px 5px;
    border-radius: 3px;
    border: 1px solid #e1e4e8;
  }}

  a {{
    color: var(--accent);
    text-decoration: none;
  }}

  a:hover {{
    text-decoration: underline;
  }}

  img {{
    max-width: 100%;
    height: auto;
    display: block;
    margin: 24px auto;
    border-radius: 4px;
  }}

  .math-display {{
    margin: 20px 0;
    text-align: center;
    overflow-x: auto;
  }}

  .math-inline .katex {{
    font-size: 1.0em;
  }}

  .math-display .katex {{
    font-size: 1.15em;
  }}

  /* Print-specific styles */
  @media print {{
    body {{
      padding: 0;
      max-width: none;
    }}
    h2 {{
      page-break-after: avoid;
    }}
    .math-display {{
      page-break-inside: avoid;
    }}
  }}
</style>
</head>
<body>
{body_html}
</body>
</html>
"""

	# Write HTML to a temporary file
	with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
		f.write(full_html)
		temp_html_path = f.name

	try:
		options = Options()
		options.add_argument('--headless')
		options.add_argument('--no-sandbox')
		options.add_argument('--disable-dev-shm-usage')

		# Point to playwright-installed chromium in test sandbox
		sandbox_chrome = "/home/agent/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome"
		if os.path.exists(sandbox_chrome):
			options.binary_location = sandbox_chrome

		# Create driver (Selenium Manager handles chromedriver automatically)
		driver = webdriver.Chrome(options=options)

		try:
			# Load the HTML file
			driver.get(f"file://{os.path.abspath(temp_html_path)}")

			# Wait for KaTeX to finish rendering
			WebDriverWait(driver, 10).until(
				lambda d: d.execute_script("""
					const mathElements = document.querySelectorAll('.math-display, .math-inline');
					if (mathElements.length === 0) return true;
					return document.querySelectorAll('.katex').length > 0;
				""")
			)

			# Print to PDF using CDP
			print_settings = {
				"printBackground": True,
				"paperWidth": 8.27,    # A4 width in inches
				"paperHeight": 11.69,  # A4 height in inches
				"marginTop": 0.5,      # 48px margin in inches (48 / 96 = 0.5)
				"marginBottom": 0.5,
				"marginLeft": 0.5,
				"marginRight": 0.5
			}

			result = driver.execute_cdp_cmd("Page.printToPDF", print_settings)
			pdf_data = base64.b64decode(result['data'])

			with open(OUTPUT_PDF, "wb") as pdf_file:
				pdf_file.write(pdf_data)

			print(f"PDF written to {os.path.abspath(OUTPUT_PDF)}")
		finally:
			driver.quit()
	except Exception as e:
		print(f"Error printing PDF via Selenium: {e}", file=sys.stderr)
		sys.exit(1)
	finally:
		if os.path.exists(temp_html_path):
			os.remove(temp_html_path)


if __name__ == '__main__':
	main()
