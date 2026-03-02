FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY src/ src/
COPY policies/ policies/

# Install the package
RUN pip install --no-cache-dir -e ".[all]"

# Download spaCy model
RUN python -m spacy download en_core_web_lg

# Create audit directory and non-root user
RUN mkdir -p /app/audit && \
    groupadd -r anonymcp && \
    useradd -r -g anonymcp -d /app -s /sbin/nologin anonymcp && \
    chown -R anonymcp:anonymcp /app

EXPOSE 8100

ENV ANONYMCP_TRANSPORT=streamable-http
ENV ANONYMCP_HOST=0.0.0.0
ENV ANONYMCP_PORT=8100

USER anonymcp

CMD ["anonymcp"]
