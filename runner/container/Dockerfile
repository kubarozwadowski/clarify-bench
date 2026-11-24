# Agent image for runner/claude_agent.py. It holds only Claude Code and Python:
# no benchmark files are copied in, and the run workspace is mounted at /workspace.
FROM node:22-bookworm-slim
ARG CLAUDE_CODE_VERSION=latest
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 ca-certificates \
    && ln -s /usr/bin/python3 /usr/local/bin/python \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION} \
    && npm cache clean --force
USER node
ENV DISABLE_AUTOUPDATER=1
WORKDIR /workspace
