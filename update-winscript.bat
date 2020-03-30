pushd "%~dp0"
copy /y %locallib_env%\_winbin\ytdl*.cmd winscript\
copy /y %locallib_env%\_winbin\bilidl.cmd winscript\
copy /y %locallib_env%\_winbin\conv.*.cmd winscript\
copy /y %locallib_env%\_winbin\drawincmd.cmd winscript\
copy /y %locallib_env%\_winbin\cmdbatchlib.cmd winscript\
copy /y %locallib_env%\_winbin\delete.nonwebp.cmd winscript\
copy /y %locallib_env%\_winbin\videoinfo.cmd winscript\
popd