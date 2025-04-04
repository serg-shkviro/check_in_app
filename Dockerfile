FROM python:3.12-slim-bookworm AS python-base

ENV PIP_NO_CACHE_DIR=1 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  PIP_DEFAULT_TIMEOUT=100 \
  PIP_ROOT_USER_ACTION=ignore \
  GID=23176 \
  UID=23176

SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

RUN apt-get update && apt-get upgrade -y \
  dumb-init

WORKDIR /app

RUN mkdir -p /app/certs

RUN openssl req -x509 -newkey rsa:4096 -keyout /app/certs/key.pem -out /app/certs/cert.pem \
  -days 365 -nodes -subj "/CN=localhost" > /dev/null 2>&1

RUN groupadd -g ${GID} -r check_in_group && useradd -u ${UID} \
  -d /home/check_in_user -m -r -g check_in_group -l check_in_user \
  && chown -R check_in_user:check_in_group /app

USER check_in_user

COPY --chown=check_in_user:check_in_user ./app /app/app/
COPY --chown=check_in_user:check_in_user ./requirements.txt ./run.py /app/
COPY --chmod=0755 --chown=check_in_user:check_in_group ./entrypoint.sh /app/entrypoint.sh

RUN pip install -r /app/requirements.txt

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["/app/entrypoint.sh"]
