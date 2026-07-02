# Sample Document

This document showcases the formatting options supported by `md2pdf`. It serves as both a syntax reference and a test file.

## Mathematical Equations (LaTeX)

The tool leverages **KaTeX** to render math formulas with print-shop quality.

### 1. Inline Math
Equations can be placed inline with the text. For example, Einstein's famous equation is $E = mc^2$, and the quadratic formula is $x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$.

### 2. Block Math
For larger, centered equations, use double dollar signs `$$`:

$$\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}$$

$$\nabla \cdot \mathbf{E} = \frac{\rho}{\varepsilon_0}$$

$$\nabla \cdot \mathbf{B} = 0$$

$$\nabla \times \mathbf{E} = -\frac{\partial \mathbf{B}}{\partial t}$$

$$\nabla \times \mathbf{B} = \mu_0 \left( \mathbf{J} + \varepsilon_0 \frac{\partial \mathbf{E}}{\partial t} \right)$$

---

## Typography and Text Styling

You can style your text using standard Markdown syntax:
- **Bold Text**: Write it as \*\*bold text\*\* to emphasize key points.
- *Italic Text*: Write it as \*italic text\* for subtle emphasis.
- `Inline Code`: Write it as \`code\` to format code variables or commands.
- [Links](https://github.com/robertoffmoura/md2pdf): Write them as \[Anchor Text\](URL) to create hyperlinked text.

---

## Unordered Lists

You can create lists and sub-lists to organize information:
- Main bullet point
  - First nested bullet point
  - Second nested bullet point
- Another main bullet point

