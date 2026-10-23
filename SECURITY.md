# Security policy

Tramo receives documents uploaded by users, converts them to text and sends that text to a language model, so security is part of the design and not an afterthought. The protections that exist today are described in the Security section of the [README](README.md). This file explains how to report a problem and what to expect afterwards.

## Supported versions

Tramo is a prototype and it has no numbered releases yet. Only the latest commit of the `main` branch receives security fixes, so please check that the problem still exists there before reporting it.

## How to report a vulnerability

Please do not open a public issue for a security problem, because that would expose every user before a fix exists.

Use the private reporting channel of GitHub instead. Open the Security tab of this repository, go to Advisories, choose Report a vulnerability and describe the problem. Only the maintainer can read the report, and the conversation with the reporter stays private until a fix is published.

If that option is not available to you, contact me through [carlosjcastrog.com](https://carlosjcastrog.com) and ask for a private channel before sharing any details.

A useful report includes the affected file or endpoint, the steps needed to reproduce the problem, the version or commit you tested, what you expected to happen and what happened instead. A minimal example file or request is the most helpful thing you can attach. Please never attach real student records or documents that contain personal data, because a synthetic document is enough to demonstrate the issue.

## What to expect

Tramo is maintained by one person, so the following times are intentions and not guarantees. I will acknowledge your report within seven days, I will tell you whether I can reproduce the problem, and I will keep you informed until it is resolved. Confirmed problems are fixed as soon as I can, and I am glad to credit the reporter in the commit message or the release notes unless you prefer to stay anonymous.

## Automated checks

The repository uses the security features of GitHub to catch problems early. Dependabot alerts warn when a pinned dependency has a known vulnerability, CodeQL analyzes the Python and JavaScript code for common coding errors, and secret protection blocks credentials that are pushed by mistake. Findings are visible only to the maintainer and are handled with the same priority as a report from a person.

## Scope

The following areas are in scope.

- Upload handling, including files that bypass the signature check, the size limits, the page limit, the expanded size limit or the rejection of scripts, macros, embedded files and path traversal.
- Any text, in a document or in a field, that manages to change the coverage or the verdict, which must always be computed by plain code, or that makes the recommendation show numbers that code did not compute.
- Prompt injection that leads to anything beyond a degraded text answer, such as leaking data, bypassing validation or reaching other users.
- Bypasses of the per client rate limits, of the analysis gate or of the request body cap.
- Weaknesses in the security headers, in the content security policy, in the host validation or in the way errors are reported, including any response that echoes submitted text or exposes internals.
- Storage or logging of uploaded documents, which must never happen.

The following areas are out of scope.

- Mistakes of the model, such as a topic that is missed, a status that is debatable or a citation that is poor. These are known limits described in the README and they are welcome as ordinary issues, because they help improve the prompts.
- Problems that require an attacker who already controls the computer that runs Tramo or the Ollama server.
- Misconfigured deployments, for example exposing Tramo to the internet without a reverse proxy, without the host list or with `TRAMO_TRUST_PROXY` enabled when the proxy does not overwrite `X-Forwarded-For`.
- Denial of service that only consumes the hardware of the machine running the model, beyond what the configured limits are meant to prevent.
- Vulnerabilities in Ollama, in the models or in third party dependencies. Please report those to their own projects, and tell me if Tramo needs an update. When a vulnerability affects a pinned dependency of Tramo, updating the pinned version is part of the fix.

## Running Tramo safely

Tramo is designed to run on the computer of the person who uses it, and that is the recommended setup. If you publish it for other people, put it behind a reverse proxy with HTTPS, set `TRAMO_ALLOWED_HOSTS` to the public host name, enable `TRAMO_TRUST_PROXY` only when the proxy overwrites `X-Forwarded-For`, keep the default rate limits or make them stricter, and keep Ollama bound to the local machine so that it is not reachable from outside.

## Good faith

I will not take action against people who investigate Tramo in good faith, who test only against their own installation, who avoid harming other users and who give me a reasonable time to fix a problem before sharing it.
