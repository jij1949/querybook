FROM hub-docker-remote.artylab.expedia.biz/python:3.9.16
# Cannot upgrade to Python 3.10 until the following uWSGI release a new version:
# https://github.com/unbit/uwsgi/pull/2363
# This caused websocket to fail

ARG PRODUCTION=true
ARG EXTRA_PIP_INSTALLS=""

RUN apt-get update -y && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl gnupg jq nano openssl telnet dnsutils \
    && rm -rf /var/lib/apt/lists/*
COPY certs/* /usr/local/share/ca-certificates/
RUN update-ca-certificates

ENV NODE_MAJOR=16

## Install Querybook package requirements + NodeJS
# Installing build-essential and python-dev for uwsgi
RUN mkdir -p /etc/apt/keyrings && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_${NODE_MAJOR}.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y --allow-downgrades --allow-remove-essential --allow-change-held-packages \
    libsasl2-dev \
    libsasl2-modules \
    build-essential \
    libssl-dev \
    libldap2-dev \
    nodejs \
    && apt-get clean

# Install YARN
RUN npm i -g npm@8.5.0 \
    && npm i -g yarn@^1.22.10 \
    && npm explore npm --global -- npm install node-gyp@9.0.0 \
    && yarn config set cache-folder /mnt/yarn-cache/cache \
    && yarn config set yarn-offline-mirror /mnt/yarn-offline-mirror

#awscliv2 - https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
RUN mkdir -p /tmp/awscliv2 && cd /tmp/awscliv2 && \
    curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip -q awscliv2.zip && \
    ./aws/install && \
    rm -rf /tmp/awscliv2

WORKDIR /opt/querybook

COPY requirements requirements/
RUN pip install -r requirements/base.txt \
    && if [ "${PRODUCTION}" = "true" ] ; then \
    pip install -r requirements/prod.txt; \
    fi \
    && if  [ -n "$EXTRA_PIP_INSTALLS" ] ; then \
    for PACKAGE in $(echo $EXTRA_PIP_INSTALLS | sed "s/,/ /g") ; do \
    pip install -r requirements/${PACKAGE}; \
    done \
    fi \
    && pip install -r requirements/local.txt || true

COPY package.json yarn.lock ./
RUN yarn install --pure-lockfile

# Copy everything else
COPY . .

# Install patches
COPY patch/pyhive/hive.py /usr/local/lib/python3.9/site-packages/pyhive/hive.py

# Copy change log images
COPY docs_website/static/changelog/ querybook/static/changelog/

# Webpack if prod
RUN if [ "${PRODUCTION}" = "true" ] ; then ./node_modules/.bin/webpack --mode=production; fi

# Environment variables, override plugins path for customization
ENV QUERYBOOK_PLUGIN=/opt/querybook/plugins
ENV PYTHONPATH=/opt/querybook/querybook/server:/opt/querybook/plugins
ENV production=${PRODUCTION}

ENTRYPOINT ["/opt/querybook/containers/start-with-vault.sh"]
