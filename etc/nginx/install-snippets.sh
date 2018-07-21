#!/bin/bash

pushd "$(dirname "$(realpath "$0")")"
install -m 644 snippets/* /etc/nginx/snippets/
popd