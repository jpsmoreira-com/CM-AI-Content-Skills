---
name: tutorial-source-to-mkdocs
description: 'Use for tutorial conversion requests such as converting DOCX to MkDocs, processing a tutorial package, reorganizing extracted tutorial pages, or combining Markdown, HTML, images, and video folders into an MkDocs-compatible structure validated against the repository style guide.'
argument-hint: 'source files or folders, target docs path, and optional asset folders'
---

# Tutorial Source to MkDocs

Use this skill when the user asks to:

- convert a DOCX to MkDocs
- process a DOCX file into Markdown
- convert a tutorial into MkDocs
- process a tutorial package with documents, images, or videos
- reuse a conversion workflow with different tutorial source formats
- reorganize extracted tutorial pages into a clean MkDocs folder structure
- convert a DOCX plus a videos folder into documentation pages
- validate converted tutorial content against the repository style guide

## Supported Source Types

This skill is intended for tutorial conversions where the source can be one or more of the following:

- DOCX files
- existing Markdown files
- HTML exports
- mixed folders with images and supporting assets
- separate video folders that must be embedded into the resulting tutorial pages
- partially converted content that still needs restructuring and cleanup

## Required Inputs

- One or more tutorial source files or folders
- A target folder, usually under `docs/...`
- Any related asset folders, such as videos or images, when available
- The shared style guide bundled with the `style-guide-validator` skill
- Any repository-specific local guidance, if one exists

## Workflow

1. Identify the source material and the final target folder.
1. Inspect existing documentation near the target path to match naming, hierarchy, and navigation patterns.
1. Propose the target MkDocs structure briefly before major edits.
1. Extract or reuse the source content and split it into topic-focused Markdown files.
1. Keep introductory, setup, legal, and asset-index pages at the tutorial root when that structure improves navigation.
1. Move scenario or reason-specific pages into a second folder when the tutorial has a natural grouped subsection.
1. Create or update `.pages` files when the surrounding documentation uses them.
1. Add frontmatter when nearby pages use it.
1. Rename extracted assets to clear, contextual filenames when practical.
1. Store images in a nearby `images/` folder and videos in a nearby `videos/` folder under the tutorial path.
1. Link videos from the scenario pages where they are most useful, and avoid duplicating the same video embed on summary pages.
1. Update all internal links and asset links to use correct relative paths after any reorganization.
1. Validate the converted content against the shared style guide and any repository-specific local guidance when available.
1. Preserve technical meaning, product terminology, UI labels, and scenario intent.
1. Do not update MkDocs configuration unless explicitly requested.
1. Do not overwrite unrelated existing files without first checking how they are already used.
1. Summarize created files, modified files, unresolved formatting issues, and manual follow-up.

## DOCX-Only Note

Use this same skill for DOCX-only requests. If the source is only a DOCX file, follow the same workflow with a simpler input set and skip the steps that depend on external asset folders.

## Structure Guidance

Prefer a structure like this when it fits the source material:

- tutorial root
  - `index.md`
  - overview or setup pages
  - `images/`
  - `videos/`
  - grouped subfolder for scenarios, reason types, or use cases

Use nearby examples in the repository to choose folder names such as:

- `reason-types`
- `scenarios`
- `use-cases`

## Validation Guidance

Check the converted output for:

- style-guide compliance
- correct heading hierarchy
- correct ordered-list formatting
- meaningful image alt text
- valid relative links
- duplicate video embeds that should be reduced to in-context usage
- unique aliases when the repository uses aliases

## Conventions

- Prefer one topic per file.
- Prefer minimal edits over broad rewrites.
- Keep wording intact unless cleanup is required for clarity or style-guide compliance.
- Use relative Markdown links.
- Use lowercase folder and file names that match the repository's current documentation naming convention and nearby examples.
- Keep video embeds inline in the page where the scenario is described.
