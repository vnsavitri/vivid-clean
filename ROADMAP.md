# Roadmap

## Formatting-preserving document editing

The Markdown round-trip is the biggest risk still hanging around. It can flatten Word runs, footnotes, fields, tables, slide layouts, speaker notes, and legal formatting.

Before building an in-place editor, run a small spike that answers:

- Can `python-docx` replace text across runs without losing styles, fields, comments, tracked changes, links, or numbering?
- Can `python-pptx` update text frames while preserving geometry, theme inheritance, notes, and animation references?
- Which structures must make the run fail rather than accept a lossy edit?
- What before-and-after fixtures prove meaning and package structure survived?

The spike should produce an architecture note and seeded fixtures. Don't ship an in-place rewrite until those failure rules are settled.
