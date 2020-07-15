pushd "%~dp0"
mkdir %locallib_env%\_winbin\mylib
xcopy /s /y mylib %locallib_env%\_winbin\mylib
xcopy /s /y mykits %locallib_env%\_winbin
popd