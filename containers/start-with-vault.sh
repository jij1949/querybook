#!/bin/bash

# Load secrets from Vault as environment variables
# This file is injected via a Vault sidecar container in RCP
if [ -f "/vault/secrets/secrets.json" ];
then
  echo "Loading secrets from Vault"
  eval "export $(cat /vault/secrets/secrets.json | jq -r 'to_entries | map("\(.key)=\(.value)") | @sh')"
else
  echo "No secrets.json file found in /vault/secrets"
fi

# Start the app
exec "$@"
