@echo off
setlocal
call drawincmd.cmd line double
echo %*
pushd %1
for %%i in (*) do (
    call conv.pic2webp.smart "%%~i" %2
)
call delete.nonwebp.infolder .
popd
