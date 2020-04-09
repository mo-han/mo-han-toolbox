pushd "%~dp0"

copy /y %locallib_env%\_winbin\drawincmd.cmd winscript\
copy /y %locallib_env%\_winbin\wincmdlib.cmd winscript\
copy /y %locallib_env%\_winbin\ytdl*.cmd winscript\
copy /y %locallib_env%\_winbin\conv.*.cmd winscript\
copy /y %locallib_env%\_winbin\fname.*.cmd winscript\
copy /y %locallib_env%\_winbin\delete.*.cmd winscript\
copy /y %locallib_env%\_winbin\wrap.*.cmd winscript\

copy /y %locallib_env%\_winbin\bilidl.cmd winscript\
copy /y %locallib_env%\_winbin\videoinfo.cmd winscript\

popd