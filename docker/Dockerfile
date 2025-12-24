# First, build the application in the `/app` directory
FROM ghcr.io/astral-sh/uv:bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Omit development dependencies
ENV UV_NO_DEV=1

# Configure the Python directory so it is consistent
ENV UV_PYTHON_INSTALL_DIR=/python

# Only use the managed Python version
ENV UV_PYTHON_PREFERENCE=only-managed
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install Python before the project for caching
RUN uv python install 3.14.2

WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

#########################################
FROM debian:bookworm-slim

RUN apt update -y
RUN apt install -y curl libmagic1

# Setup a non-root user
ENV USER=lyricardsbot

# Define the group and ID for Telegram Local API server
ENV TG_SERVER_GROUP_NAME=telegram
ENV TG_SERVER_GID=101
# Create the group with the specified GID
RUN groupadd -g $TG_SERVER_GID $TG_SERVER_GROUP_NAME

RUN groupadd --system --gid 1000 $USER \
 && useradd --system --gid 1000 --uid 1000 --create-home $USER

# Add user to group 101 which to have access to /var/lib/tg* directory which owned by local API server
RUN usermod -aG $TG_SERVER_GID $USER

# Create directory for the app user
ENV HOME=/home/$USER
RUN mkdir -p $HOME

# Copy the Python version
COPY --from=builder --chown=python:python /python /python

# Copy the application from the builder
COPY --from=builder --chown=${USER}:${USER} /app /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app
USER $USER

# Create directory for the bot data
ENV DATA_DIR_NAME=appdata
ENV DATA_DIR_PATH=${HOME}/${DATA_DIR_NAME}
RUN mkdir -p $DATA_DIR_PATH

