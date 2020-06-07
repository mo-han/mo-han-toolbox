pushd "%~dp0"
mkdir %locallib_env%\_winbin\mylib
copy /y mylib %locallib_env%\_winbin\mylib
copy /y mykits %locallib_env%\_winbin
popd