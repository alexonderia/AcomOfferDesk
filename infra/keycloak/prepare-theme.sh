#!/bin/sh
set -e
set -u

THEME_NAME="${KEYCLOAK_LOGIN_THEME:-acom-offerdesk}"
THEME_SRC_DIR="/opt/keycloak/themes-src/${THEME_NAME}"
THEME_DST_DIR="/opt/keycloak/themes/${THEME_NAME}"
THEME_PROPERTIES_FILE="${THEME_DST_DIR}/login/theme.properties"
THEME_RESOURCES_DIR="${THEME_DST_DIR}/login/resources"

if [ ! -d "$THEME_SRC_DIR" ]; then
  echo "Keycloak theme source not found: $THEME_SRC_DIR" >&2
  exit 1
fi

rm -rf "$THEME_DST_DIR"
mkdir -p "/opt/keycloak/themes"
cp -R "$THEME_SRC_DIR" "$THEME_DST_DIR"

if [ -d "$THEME_RESOURCES_DIR" ]; then
  ASSET_VERSION="$(
    find "$THEME_RESOURCES_DIR" -type f -print \
      | LC_ALL=C sort \
      | xargs sha256sum \
      | sha256sum \
      | cut -c1-12
  )"
else
  ASSET_VERSION="$(date +%s)"
fi

TMP_FILE="$(mktemp)"
sed "s/__AOD_ASSET_VERSION__/${ASSET_VERSION}/g" "$THEME_PROPERTIES_FILE" > "$TMP_FILE"
mv "$TMP_FILE" "$THEME_PROPERTIES_FILE"

echo "Prepared Keycloak theme '${THEME_NAME}' with asset version ${ASSET_VERSION}"
