# AI Development Workflow

## Source of truth

- The GitHub repository `shabydevelop-code/Salesforce-AI-Lab` is the sole source of truth for project code and development documentation.
- The AI assistant must inspect the actual repository contents before proposing or implementing changes. Do not rely on outdated conversation summaries or documentation as evidence of the current code state.
- All AI-authored code and documentation changes must be committed directly to the repository's `main` branch. Do not create feature branches or pull requests unless the user explicitly changes this rule.
- The user has granted permission for the AI assistant to read, create, update, and commit files in this repository without requesting approval for each routine change.
- The user performs `git pull` on their Windows machine to retrieve changes. Do not ask the user to edit, copy, or create project source files locally as a substitute for GitHub changes.
- Do not use the user's local working directory as a source of truth. Local commands may be requested only for deployment, runtime verification, or diagnostics that cannot be performed through GitHub; explain why they are needed.
- If repository access or file discovery is unavailable, report the specific limitation rather than guessing paths, claiming a commit, or shifting development work to the user's machine.
- After each successful change, provide the commit SHA, a concise description of the changes, and the exact pull/deploy/test commands where applicable.

## Documentation scope

- Keep this file focused on stable operating rules, not a running project status, implementation backlog, or speculative description of current code.
- Record reusable technical execution instructions or known pitfalls in dedicated documentation when warranted; verify them against the actual repository first.

## Chat language and direction

- All assistant responses in the Salesforce-AI-Lab project chat must be written in Hebrew, right-to-left (RTL).
- Apply RTL consistently to explanations, headings, lists, and tables wherever the chat interface supports it.
- Preserve technical identifiers, file paths, commands, code, and Salesforce/API field names in their original left-to-right (LTR) form to avoid corrupting syntax.
- When Hebrew and English appear together, format them for clear RTL reading without changing the literal technical text.
