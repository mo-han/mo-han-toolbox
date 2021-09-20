#!/usr/bin/env python3
import os

ez_path_is_file = os.path.isfile
ez_path_is_dir = os.path.isdir
ez_path_exists = os.path.exists
ez_path_dirname = os.path.dirname
ez_path_basename = os.path.basename
ez_path_common = os.path.commonpath
ez_path_common_prefix = os.path.commonprefix
ez_path_join = os.path.join
ez_path_user_tilde = os.path.expanduser
ez_path_env_var = os.path.expandvars
ez_path_split = os.path.split
ez_path_split_ext = os.path.splitext
ez_path_absolute = os.path.abspath
ez_path_real = os.path.realpath
ez_path_relative = os.path.relpath
ez_path_normalize = os.path.normpath
ez_path_get_size = os.path.getsize
ez_path_get_ctime = os.path.getctime
ez_path_get_mtime = os.path.getmtime
