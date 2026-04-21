#!/bin/sh
set -e

MY_USERNAME="${MY_USERNAME:-nextcloud}"
MY_GROUP="${MY_GROUP:-${MY_USERNAME}}"
MY_UID="${MY_UID:-1000}"
MY_GID="${MY_GID:-${MY_UID}}"

if getent group "${MY_GROUP}" > /dev/null 2>&1; then
  echo "INFO: Group exists; skipping creation"
else
  echo "INFO: Group doesn't exist; creating..."
  if getent group "${MY_GID}" > /dev/null 2>&1; then
    echo "INFO: GID exists with different name; renaming..."
    existing_group=$(getent group "${MY_GID}" | cut -d: -f1)
    groupmod -n "${MY_GROUP}" "${existing_group}"
  else
    groupadd -g "${MY_GID}" "${MY_GROUP}"
  fi
fi

if id -u "${MY_USERNAME}" > /dev/null 2>&1; then
  echo "INFO: User exists; skipping creation"
else
  echo "INFO: User doesn't exist; creating..."
  if getent passwd "${MY_UID}" > /dev/null 2>&1; then
    echo "INFO: UID exists with different name; renaming..."
    existing_user=$(getent passwd "${MY_UID}" | cut -d: -f1)
    usermod -l "${MY_USERNAME}" -g "${MY_GROUP}" -s /sbin/nologin "${existing_user}"
  else
    useradd -u "${MY_UID}" -g "${MY_GROUP}" -s /sbin/nologin -M "${MY_USERNAME}"
  fi
fi

mkdir -p /nextcloud-data
chown -R "${MY_USERNAME}:${MY_GROUP}" /nextcloud-data

exec gosu "${MY_USERNAME}" "/sync.sh"