# onePagerLauncher

onePagerLauncher is a small Python-based project for serving and previewing single‑page HTML content. The repository contains a Python entrypoint, an authentication helper, HTML templates, and containerization files so you can run it locally or in Docker.

This README was created from the repository layout (main.py, auth.py, templates/, Dockerfile, docker-compose.yml, requirements.txt). For exact runtime flags and configuration options, consult main.py and requirements.txt in the repo.

## Quick overview

- Language: Python + HTML
- Entrypoint: main.py
- Auth helper: auth.py
- Templates: templates/ (HTML/Jinja-style templates)
- Container support: Dockerfile, docker-compose.yml
- Dependency file: requirements.txt
- License: LICENSE

## Repository structure

- .gitignore
- Dockerfile
- docker-compose.yml
- LICENSE
- README.md (this file)
- auth.py
- main.py
- requirements.txt
- templates/ (directory with HTML templates)

## Prerequisites

- Python 3.8+ (or the version used in your environment)
- pip
- Docker


## Docker

Build the Docker image:
docker build -t onepagerlauncher .

Run the container (example mapping port 8080):
docker run -p 8080:8080 onepagerlauncher

Or use docker-compose:
docker-compose up --build

Adjust port mappings and environment variables in docker-compose.yml as needed.

## Configuration & Extensibility

- The templates/ directory contains the HTML used by the application — edit or add templates there.
- auth.py contains authentication-related logic; review it before enabling any production-facing authentication.
- main.py is the application entrypoint; it likely contains server startup logic and any CLI/config parsing.

If you want to add TLS, custom ports, alternate index files, or other runtime behavior, implement the changes in main.py and/or add a configuration file that the app reads.

## Development

- Make changes on feature branches (git checkout -b feat/your-feature).
- Run tests (if any) and linting as appropriate for the project.
- Update requirements.txt when adding new Python packages:
  pip freeze > requirements.txt

## Troubleshooting

- Port already in use: change the port when launching the app or via docker run -p.
- Missing dependency: inspect requirements.txt and install the missing package manually.
- Templates not rendering: confirm templates/ contains the expected files and paths referenced by HTML.

## Contributing

Contributions are welcome. Typical workflow:
1. Open an issue describing the change.
2. Fork the repository and create a branch.
3. Implement your change and add tests if applicable.
4. Open a pull request with a description of the change.

## License

This repository includes a LICENSE file. Review it to understand the terms of use.

## Notes

This README is tailored to the repository structure present in the project root (main.py, auth.py, templates/, Dockerfile, docker-compose.yml, requirements.txt). For command syntax, flags, and runtime configuration, see main.py and requirements.txt directly.
