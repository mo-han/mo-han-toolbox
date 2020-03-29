pushd "%~dp0"
copy /y %locallib_env%\_winbin\ytdl*.bat winscript\
copy /y %locallib_env%\_winbin\bilidl.bat winscript\
copy /y %locallib_env%\_winbin\conv.*.bat winscript\
copy /y %locallib_env%\_winbin\drawincmd.bat winscript\
copy /y %locallib_env%\_winbin\cmdbatchlib.bat winscript\
copy /y %locallib_env%\_winbin\delete.nonwebp.bat winscript\
copy /y %locallib_env%\_winbin\videoinfo.bat winscript\
popd