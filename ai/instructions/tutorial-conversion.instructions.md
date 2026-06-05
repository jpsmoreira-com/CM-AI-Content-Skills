---
description: "Use when converting a DOCX, tutorial package, mixed-source content, extracted HTML, images, or video folders into MkDocs documentation."
name: "Tutorial Conversion Workflow"
applyTo:
  - "docs/tutorials/**/*.md"
---

# Tutorial Conversion Workflow

- Inspect nearby documentation before deciding the final folder and file structure.
- Create an MkDocs-compatible layout under the requested documentation target.
- Prefer one topic per file and preserve the source document hierarchy where it still makes sense.
- Create or update `.pages` files when the surrounding section uses them.
- Store images in a nearby `images/` folder and videos in a nearby `videos/` folder.
- Embed videos only on the most relevant scenario or procedure pages; avoid repeating the same embed on summary pages.
- Add or preserve useful frontmatter when the surrounding content pattern expects it.
- Do not update MkDocs configuration unless explicitly requested.
- Validate the result against the repository style guide before finishing when a guide exists.
