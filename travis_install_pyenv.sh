#!/usr/bin/env bash

brew uninstall pyenv
export PYENV_ROOT="$HOME/.pyenv_repo"
PYENV_RELEASE="v1.2.9"

mkdir "$PYENV_ROOT"
curl -fsSL "https://github.com/yyuu/pyenv/archive/$PYENV_RELEASE.tar.gz" | tar -xz -C "$PYENV_ROOT" --strip-components 1

export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

pyenv install "$PYTHON"
pyenv global "$PYTHON"
