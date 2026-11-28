# Security Policy

## Supported Versions

Security fixes are released for the latest `0.5.x` patch release and the upcoming `0.6.x` release line.

| Version | Supported |
| ------- | --------- |
| `0.6.x` | Yes |
| `0.5.0.3+` | Yes |
| `< 0.5.0.3` | No |

## Reporting a Vulnerability

Please **do not** report security vulnerabilities through public GitHub issues, discussions, or pull requests.

Instead, report vulnerabilities privately through one of the following channels:

1. **GitHub Private Security Advisories** (preferred): open a private advisory in the `Kanaries/pygwalker` repository under **Security → Advisories → Report a vulnerability**.
2. **Email**: send details to `support@kanaries.net` with the subject prefix `[SECURITY]`.

Please include:
- Affected PyGWalker version(s) and deployment mode (e.g., Jupyter, local web server, Streamlit, Gradio, Reflex, marimo).
- Minimal reproduction steps or proof-of-concept.
- Assessment of impact and any suggested mitigation.

We aim to acknowledge reports within 3 business days and coordinate a disclosure timeline with the reporter before publishing an advisory.

## Deployment Security Guidance

- **Database `Connector` credentials**: Always configure `Connector` with a **read-only, least-privilege** database account scoped only to the tables or views intended for visualization.
- **Public web applications (Streamlit, Gradio, Reflex, marimo)**: Treat the entire dataset backing a shared renderer as readable by any visitor who can access the application, including when rendering filtered views or single charts. Apply authentication at the application/reverse-proxy layer for sensitive datasets.
- **Local web server (`pyg.walk()` outside Jupyter)**: Do not share the tokenized localhost URL printed at startup with untrusted users or processes.
