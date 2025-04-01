#!/bin/bash

#
# Load secrets from Vault as environment variables
# These files are injected via a Vault sidecar container in RCP
# If the Vault secrets are not injected, the app will still start with the default values
#
# Managed database secrets, if available, will be used to replace the placeholders
# in DATABASE_CONN and ELASTICSEARCH_HOST environment variables
#
# Expected format:
#   DATABASE_CONN=mysql+pymysql://<username>:<password>@test-aurora-mysql-egdataplatform-querybook...
#   ELASTICSEARCH_HOST=<username>:<password>@100.72.88.36:9200
#

echo "Looking for secrets.json file in /vault/secrets"

# Check if secrets.json file exists
if [ -f "/vault/secrets/secrets.json" ];
then
  eval "export $(cat /vault/secrets/secrets.json | jq -r 'to_entries | map("\(.key)=\(.value)") | @sh')"
  echo "Exported secrets from Vault"
fi

# Schema Deploy managed database secrets
# https://expediagroup.atlassian.net/wiki/spaces/DAPS/pages/500376374/Integrate+Schema+Deploy+managed+database+secrets+with+RCP

echo "Looking for managed-database.json file in /vault/secrets"

# Check if managed-database.json file exists
if [ -f "/vault/secrets/managed-database.json" ];
then
  ## MYSQL ##
  # Parse the JSON file and extract user_name and password for active db secrets with platform=mysql
  mysql_username=$(jq -r '.db_secrets[] | select(.active == true and .database_name == "querybook2" and .user_type == "APP_USER") | .user_name' /vault/secrets/managed-database.json)
  mysql_password=$(jq -r '.db_secrets[] | select(.active == true and .database_name == "querybook2" and .user_type == "APP_USER") | .password' /vault/secrets/managed-database.json)

  # Export the extracted values as environment variables
  export MYSQL_USERNAME="$mysql_username"
  export MYSQL_PASSWORD="$mysql_password"

  # Replace the placeholders in DATABASE_CONN with the actual values
  export DATABASE_CONN="${DATABASE_CONN/<username>/$MYSQL_USERNAME}"
  export DATABASE_CONN="${DATABASE_CONN/<password>/$MYSQL_PASSWORD}"

  ## ELASTICSEARCH ##
  # Parse the JSON file and extract user_name and password for active db secrets with platform=elasticsearch
  elastic_username=$(jq -r '.db_secrets[] | select(.active == true and .database_name == "querybook" and .user_type == "APP_USER") | .user_name' /vault/secrets/managed-database.json)
  elastic_password=$(jq -r '.db_secrets[] | select(.active == true and .database_name == "querybook" and .user_type == "APP_USER") | .password' /vault/secrets/managed-database.json)

  # Export the extracted values as environment variables
  export ELASTIC_USERNAME="$elastic_username"
  export ELASTIC_PASSWORD="$elastic_password"

  # Replace the placeholders in ELASTICSEARCH_HOST with the actual values
  export ELASTICSEARCH_HOST="${ELASTICSEARCH_HOST/<username>/$ELASTIC_USERNAME}"
  export ELASTICSEARCH_HOST="${ELASTICSEARCH_HOST/<password>/$ELASTIC_PASSWORD}"

  echo "Exported managed-database secrets from Vault"
fi

# Start the app
exec "$@"
