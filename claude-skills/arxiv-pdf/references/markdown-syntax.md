# Markdown Body Syntax

## Sections

Standard markdown headings map to LaTeX sections (auto-numbered by `--number-sections`):

```markdown
# Introduction           → \section{Introduction}          (1)
## Background            → \subsection{Background}         (1.1)
### Specific Topic       → \subsubsection{Specific Topic}  (1.1.1)
#### Detail              → \paragraph{Detail}
```

## Equations

**Inline math**: Use single `$...$`:
```markdown
The energy is $E = mc^2$ where $m$ is mass.
```

**Display math**: Use `$$...$$` (renders as `equation` environment):
```markdown
The Butler-Volmer equation:
$$
j = j_0 \left[ \exp\left(\frac{\alpha_a F \eta}{RT}\right) - \exp\left(-\frac{\alpha_c F \eta}{RT}\right) \right]
$$
```

**Aligned equations**: Use `aligned` inside `$$`:
```markdown
$$
\begin{aligned}
\nabla \cdot \mathbf{E} &= \frac{\rho}{\epsilon_0} \\
\nabla \times \mathbf{B} &= \mu_0 \mathbf{J} + \mu_0 \epsilon_0 \frac{\partial \mathbf{E}}{\partial t}
\end{aligned}
$$
```

**Numbered equations with labels** (for cross-referencing):
```markdown
$$
\frac{\partial c}{\partial t} = D^* \nabla^2 c
$$ {#eq:diffusion}

As shown in Equation @eq:diffusion, ...
```

## Figures

```markdown
![Caption text for the figure.](figures/my_figure.png){width=80%}
```

With label for cross-referencing:
```markdown
![SEM image of the gate-stack cross-section.](figures/sem_image.png){#fig:sem width=70%}

As shown in Figure @fig:sem, the oxide thickness is approximately 5 nm.
```

Side-by-side figures (use raw LaTeX):
```markdown
\begin{figure}[htbp]
\centering
\begin{subfigure}{0.48\textwidth}
  \includegraphics[width=\textwidth]{figures/before.png}
  \caption{Before anneal}
\end{subfigure}
\hfill
\begin{subfigure}{0.48\textwidth}
  \includegraphics[width=\textwidth]{figures/after.png}
  \caption{After anneal}
\end{subfigure}
\caption{Comparison of gate-oxide surface morphology.}
\label{fig:comparison}
\end{figure}
```

## Tables

Pandoc pipe tables with caption:

```markdown
| Material | Dielectric Constant | Band Gap (eV) |
|----------|:-------------------:|:-------------:|
| SiO2     | 3.9                 | 8.9           |
| Si3N4    | 7.5                 | 5.3           |
| HfO2     | ~20                 | 5.7           |

: Gate-dielectric constants and band gaps. {#tbl:alloys}
```

Grid tables for complex layouts:
```markdown
+----------+-------------------+------------------+
| Material | Dielectric Const. | Crystal Structure|
+==========+===================+==================+
| SiO2     | 3.9               | amorphous        |
+----------+-------------------+------------------+
| HfO2     | ~20               | monoclinic       |
+----------+-------------------+------------------+
```

## Citations

With `bibliography: refs.bib` in frontmatter, use pandoc citation syntax:

```markdown
Previous work has shown promising results [@smith2024; @jones2023].
According to @smith2024, the dielectric constant is...
Smith et al. [-@smith2024] demonstrated that...
```

The `.bib` file uses standard BibTeX format:
```bibtex
@article{smith2024,
  author  = {Smith, Alice and Jones, Bob},
  title   = {Assert-Driven Parametric Design for Printed Parts},
  journal = {Journal of Practical Examples},
  year    = {2024},
  volume  = {9},
  pages   = {1234--1245},
  doi     = {10.0000/example.2026.001}
}
```

## Cross-References

Pandoc-crossref syntax (requires pandoc-crossref filter, or use raw LaTeX `\ref{}`):

```markdown
See Figure @fig:sem, Table @tbl:alloys, and Equation @eq:diffusion.
```

If pandoc-crossref is not installed, use inline LaTeX:
```markdown
See Figure \ref{fig:sem} and Equation \ref{eq:diffusion}.
```

## Code Blocks

````markdown
```python
import numpy as np
x = np.linspace(0, 1, 100)
```
````

## Footnotes

```markdown
This is important.^[This footnote will appear at the bottom of the page.]
```

## Raw LaTeX

For anything not expressible in Markdown, embed raw LaTeX:

````markdown
```{=latex}
\begin{theorem}
For all $x > 0$, we have $\log(1+x) \leq x$.
\end{theorem}
```
````
