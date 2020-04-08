@echo off
setlocal
call drawincmd.cmd line double
echo %*
pushd %1
for %%i in (*) do call conv.webp.lower "%%~i" %2
popd
