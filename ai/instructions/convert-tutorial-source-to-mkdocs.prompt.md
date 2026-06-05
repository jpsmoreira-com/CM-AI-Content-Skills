---
name: "Convert Tutorial Source to MkDocs"
description: "Use when converting a DOCX, tutorial package, mixed source folder, extracted HTML, Markdown, images, or videos into MkDocs pages."
argument-hint: "sources, target folder, and optional asset folders"
agent: "agent"
---

Convert the tutorial source package I provide into this repository's MkDocs documentation structure.

Use the repository conversion workflow and conventions for tutorial-source-to-mkdocs.

Inputs to use:

- Source files or folders: the files and folders I reference in this chat.
- Target folder: the documentation folder I specify.
- Supporting assets: any referenced image or video folders.

Requirements:

- Treat DOCX-only requests and mixed-source tutorial requests with the same conversion workflow.
- Inspect nearby documentation before deciding the final structure.
- Create an MkDocs-compatible folder and Markdown structure.
- Prefer one topic per file.
- Create or update `.pages` files when needed.
- Store images in a nearby `images/` folder.
- Store videos in a nearby `videos/` folder and embed them in the most relevant scenario pages.
- Avoid duplicating the same video embed on summary pages.
- Add or preserve useful frontmatter when the surrounding content pattern expects it.
- Validate the content against the repository style guide when one exists.
- Do not update MkDocs configuration unless I explicitly ask.

At the end, report:

- files created
- files modified
- unresolved formatting issues
- manual follow-up needed
