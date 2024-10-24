#!/usr/bin/env bash

set -euxo pipefail

PYTHON_VERSION=3.12

PS4='+${BASH_SOURCE[0]}:$LINENO: '
if [[ -t 1 ]] && type -t tput >/dev/null; then
  if (( "$(tput colors)" == 256 )); then
    PS4='$(tput setaf 10)'$PS4'$(tput sgr0)'
  else
    PS4='$(tput setaf 2)'$PS4'$(tput sgr0)'
  fi
fi

# Install prerequisite packages.
sudo apt-get -y update
sudo apt-get -y dist-upgrade
sudo apt-get clean
sudo rm -rf /var/lib/apt/lists/*

sudo chown vscode:vscode /workspaces
sudo chown -R vscode:vscode /workspaces/majsoul-liqi-json/.venv

# Install uv.
curl -LsSf https://astral.sh/uv/install.sh | sh
. "$HOME/.cargo/env"
uv python install $PYTHON_VERSION --no-progress

export UV_LINK_MODE=copy

pushd /workspaces/majsoul-liqi-json
pushd .venv
rm -rf *
rm -rf ./.*
popd
uv venv
uv sync
popd
