# Upstream ACL files and license notices

The unmodified ACL files in this directory were downloaded from the official
[acl-org/acl-style-files repository](https://github.com/acl-org/acl-style-files)
on 9 October 2026, at commit
`d5adc823ff0f80f98c80405ca0ab66c68e684409` (29 June 2026).
`upstream.json` records their individual SHA-256 checksums and pinned download URLs.

`acl_natbib.bst` retains its original headers, including Patrick W. Daly's
1994–2011 copyright notice and the permission to redistribute or modify under
the LaTeX Project Public License, version 1 or later. Its urlbst modification
header retains Norman Gray's 2002–2023 copyright and LPPL notice. The official
[LPPL 1.3c text](https://www.latex-project.org/lppl/lppl-1-3c.txt) is included as
`LPPL-1.3c.txt`; its source and hash are recorded in `upstream.json`.

The upstream root did not contain a repository-wide LICENSE file at this commit.
`acl.sty`, the example documents, and the other upstream documentation are
preserved byte for byte with their existing notices and acknowledgments. This
note does not assign a new license to them or imply that the report's license
governs third-party files.

The official style supports `preprint` mode, which displays author names and page
numbers without review line numbers. Using the style does not imply submission,
acceptance, endorsement, or publication by ACL.

For a build from `paper/`, place `vendor/` in `TEXINPUTS` and `BSTINPUTS` and use
`\usepackage[preprint]{acl}`. The style itself selects `acl_natbib`; do not add a
second `\bibliographystyle` command.
