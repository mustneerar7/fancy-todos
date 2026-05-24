#!/usr/bin/env bash

set -e
set -x

ruff check app scripts
ruff format app scripts --check
