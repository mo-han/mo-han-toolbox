pushd "%~dp0"
copy /y bilibili_adx.py %locallib_env%\_winbin\
copy /y lib_*.py %locallib_env%\_winbin\
copy /y nhentai.py %locallib_env%\_winbin\
copy /y hentai_cafe.py %locallib_env%\_winbin\
copy /y jijidown_rename.py %locallib_env%\_winbin\
copy /y ytdl_iwara_na2uploader.py %locallib_env%\_winbin\
copy /y bilidl_worker.py %locallib_env%\_winbin\
copy /y mykit.py %locallib_env%\_winbin\
popd