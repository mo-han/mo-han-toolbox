#!/bin/bash

pushd "$(dirname "$(realpath "$0")")"
install -v -m 644 snippets/* /etc/nginx/snippets/
install -v -m 664 sites-available/* /etc/nginx/sites-available/
popd