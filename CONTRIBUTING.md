# Contributing to Tramo

Thank you for your interest in Tramo. The project is a decision support tool for university equivalencies, and it is small enough that a clear contribution can be reviewed quickly. This guide explains how to set up the project, which principles the code follows and what a good change looks like.

## Ways to help

You can report a problem, propose an improvement, test Tramo with synthetic study plans, improve a prompt or a document, adapt the equivalency rule to the regulation of another institution, or send a change that fixes something. If your university or faculty wants to validate Tramo with its own study plans, please open an issue first so that we can agree on how to do it without sharing personal data.

Mistakes of the model, such as a missed topic or a debatable status, are welcome as issues. Please include the two programs when you are allowed to share them, or a synthetic version that shows the same behavior, together with the report you obtained and the one you expected.

Security problems must not be reported in public issues. Follow [SECURITY.md](SECURITY.md) instead, which explains how to use the private reporting channel of GitHub.

## Never share personal data

Do not attach real student records, identification numbers, case files or resolutions to issues or pull requests. Study programs are institutional documents and they should be shared only when you have the right to do so. When in doubt, anonymize the document or write a short synthetic example.

## Setting up

You need Python 3, [Ollama](https://ollama.com) and the Gemma 4 e4b model.

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements_dev.txt
ollama pull gemma4:e4b
python -m pytest
python -m uvicorn app.api:app
```

On Linux and macOS the activation command is `source .venv/bin/activate`. The tests use fake model clients, so they run quickly and do not need Ollama. The server needs Ollama to run an analysis. All the settings are read from environment variables, and the list is in the README.

## Principles of the code

The code is organized in small modules, each with a single responsibility, and services receive their collaborators through the container, so a new behavior should usually be a new module or a small extension of an existing one and not a larger function. Please keep the code free of duplication, follow SOLID and CRUD practices where they apply, and write code that explains itself through clear names, because the project does not use comments in the code.

Some decisions are deliberate and must be preserved.

- **Code decides, the model proposes.** Coverage, the verdict, the pending topics and every recomputation after a professor overrides a status are plain code with tests. The model must never compute a number that the interface shows as a fact.
- **Structured and validated output.** Every request to the model sends a JSON schema, and every answer is validated, so that each topic is assessed once, cited sources exist and numbers that code did not compute are dropped.
- **Documents are data.** Program text is sent between delimiters, the delimiters are removed from the input, and anything that tries to instruct the model must raise a visible warning. Please do not weaken these protections.
- **Nothing is stored.** Documents are processed in memory and never written to the disk or to logs.
- **Visible degradation.** When something falls back, such as the rule based topic splitter, the report must say so.

## Interface

The interface is plain HTML, CSS and ES modules, with no framework and no build step. The content security policy forbids inline scripts and styles, so a style that depends on a value is applied through the CSS object model. Please keep the interface accessible and usable with a keyboard, keep the texts in Spanish, keep both the light and the dark variants working, and respect the animation toggle, which must leave the progress visible when animations are off. Avoid em dashes and hyphens used as punctuation in the texts shown to users.

## Tests

Every change in the policy, in the assessment, in the advisor, in the extraction or in the security layers needs a test that fails without the change. Run the whole suite with `python -m pytest` before sending anything, and make sure it passes. A change in the prompts should come with a note describing what you tested and which behavior changed, because prompt behavior is the hardest part to check automatically.

## Commits and pull requests

Commit messages are written in English, start with a conventional prefix such as `feat:`, `fix:`, `add:`, `docs:`, `refactor:`, `test:`, `style:`, `build:` or `chore:`, and do not use scopes. Each commit covers one topic, so a change that fixes a bug and adds a feature should be two commits.

A pull request should explain what problem it solves and why the approach was chosen, mention the tests that were added or changed, and include a screenshot or a short recording when it changes the interface. Please keep pull requests focused, because a small change is reviewed and merged much faster. The repository runs CodeQL analysis, so a pull request should not introduce new findings, and a change that adds or updates a dependency should pin its version in the requirements files.

## Licensing of contributions

By sending a contribution you agree that it is published under the MIT license of this project. Institutions that need other terms can contact the maintainer, as explained in the README.

## Respect

Please treat everyone with courtesy and patience. Discussions should stay on the work, criticism should be about the code and the ideas and not about the people, and harassment or discrimination of any kind is not accepted. The maintainer may close discussions or remove comments that do not follow this rule.
