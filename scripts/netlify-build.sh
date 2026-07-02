#!/usr/bin/env bash
set -euo pipefail

npm ci

cd frontend
npm ci
npm run build
