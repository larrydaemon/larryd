# LARRYD's tool server in a container, for the MCP directories that start a server from a Dockerfile (Glama, Docker's
# MCP catalog). Built from this repository (the build context is the repository's root); the standard library only.
FROM python:3.14-slim
LABEL io.modelcontextprotocol.server.name="io.github.larrydaemon/larryd"
WORKDIR /src
COPY pyproject.toml README.md ./
COPY larryd ./larryd
RUN pip install --no-cache-dir . && rm -rf /src
WORKDIR /work
ENTRYPOINT ["larryd", "mcp"]
