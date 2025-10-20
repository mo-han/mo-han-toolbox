#!/usr/bin/env python3
# encoding=utf8
import mimetypes
import random
from math import log

import ffmpeg
import filetype

import oldezpykit.stdlib.os.common
import mylib.easy
import mylib.easy.io
import mylib.ext.tricks
from mylib.__deprecated__ import fs_find_iter
from mylib.easy import *
from mylib.easy.filename_tags import EnclosedFilenameTags
from mylib.easy.logging import ez_get_logger, LOG_FMT_MESSAGE_ONLY
from mylib.ext import fstk, tui, ostk

S_ORIGINAL = "original"
S_SEGMENT = "segment"
S_NON_SEGMENT = "non segment"
S_FILENAME = "filename"
S_VIDEO = "video"
S_OTHER = "other"
S_MORE = "more"
S_ALL = "all"
S_ONLY_VIDEO = "only video"
S_ONLY_PICTURE = "only picture"
S_ONLY_AUDIO = "only audio"
S_ONLY_SUBTITLE = "only subtitle"
S_ONLY_DATA = "only data"
S_ONLY_ATTACHMENT = "only attachment"
S_NO_VIDEO = "no video"
S_NO_AUDIO = "no audio"
S_NO_SUBTITLE = "no subtitle"
S_NO_DATA = "no data"
S_NO_ATTACHMENT = "no attachment"
S_FIRST_VIDEO = "first video"
STREAM_MAP_PRESET_TABLE = {
    S_ALL: ["0"],
    S_ONLY_VIDEO: ["0:V"],
    S_ONLY_AUDIO: ["0:a"],
    S_ONLY_SUBTITLE: ["0:s"],
    S_ONLY_ATTACHMENT: ["0:t"],
    S_ONLY_DATA: ["0:d"],
    S_NO_VIDEO: ["0", "-0:V"],
    S_NO_AUDIO: ["0", "-0:a"],
    S_NO_SUBTITLE: ["0", "-0:s"],
    S_NO_ATTACHMENT: ["0", "-0:t"],
    S_NO_DATA: ["0", "-0:d"],
    S_FIRST_VIDEO: ["0:V:0"],
    S_ONLY_PICTURE: ["0:v", "-0:V"],
}
CODEC_NAME_TO_FILEXT_TABLE = {
    "mjpeg": ".jpg",
    "png": ".png",
    "hevc": ".mp4",
    "h264": ".mp4",
    "vp9": ".webm",
}
OLD_TAILS = [".__origin__", ".hevc8b"]
TAILS_D = {
    "o": ".origin",
    "a8": ".avc8b",
    "h8": ".hevc8b",
    "aq8": ".qsvavc8b",
    "hq8": ".qsvhevc8b",
}
TAILS_L = TAILS_D.values()
VALID_TAILS = OLD_TAILS + list(TAILS_L)
VIDEO_CODECS_A10N = {
    "a": "h264",
    "h": "hevc",
    "v": "vp9",
    "aq": "h264_qsv",
    "hq": "hevc_qsv",
}
CODEC_TAGS_DICT = {
    "o": "origin",
    "a8": "avc8b",
    "h8": "hevc8b",
    "aq8": "qsvavc8b",
    "hq8": "qsvhevc8b",
    **VIDEO_CODECS_A10N,
}
CODEC_TAGS_SET = set(CODEC_TAGS_DICT.values())

decorator_choose_map_preset = mylib.easy.deco_factory_param_value_choices(
    {"map_preset": STREAM_MAP_PRESET_TABLE.keys()}
)


def file_is_video(filepath):
    guess = filetype.guess(filepath)
    # ext = os.path.splitext(filepath)[-1]
    if guess and "video" in guess.mime:
        return True
    guess = mimetypes.guess_type(filepath)[0]
    if guess and "video" in guess:
        return True
    return False


def file_is_audio(filepath):
    guess = filetype.guess(filepath)
    # ext = os.path.splitext(filepath)[-1]
    if guess and "audio" in guess.mime:
        return True
    guess = mimetypes.guess_type(filepath)[0]
    if guess and "audio" in guess:
        return True
    return False


def filext_from_codec_name(x) -> str:
    d = CODEC_NAME_TO_FILEXT_TABLE
    if isinstance(x, str):
        return d[x]
    elif isinstance(x, dict) and "codec_name" in x:
        return d[x["codec_name"]]
    else:
        raise TypeError(x)


def excerpt_single_video_stream(filepath: str) -> dict:
    d = {}
    data = ffmpeg.probe(filepath)
    file_format = data["format"]
    streams = data["streams"]
    if len(streams) == 1:
        single_stream = streams[0]
        if (
            single_stream["codec_type"] == "video"
            and single_stream["disposition"]["attached_pic"] == 0
        ):
            d["size"] = int(file_format["size"])
            try:
                d["start_time"] = start_time = float(
                    single_stream.get("start_time", file_format["start_time"])
                )
                duration = float(single_stream.get("duration", file_format["duration"]))
                d["duration"] = round((duration - start_time), 6)
            except KeyError:
                d["duration"] = float(file_format["duration"])
            d["bit_rate"] = int(8 * d["size"] // d["duration"])
            d["codec_name"] = single_stream["codec_name"]
            d["height"] = single_stream["height"]
            d["width"] = single_stream["width"]
            d["pix_fmt"] = single_stream["pix_fmt"]
    return d


def get_real_duration(filepath: str) -> float:
    d = ffmpeg.probe(filepath)["format"]
    duration = float(d["duration"])
    start_time = float(d.get("start_time", 0))
    return duration if start_time <= 0 else duration - start_time


class FFmpegArgsList(list):
    def __init__(self, *args, **kwargs):
        super(FFmpegArgsList, self).__init__()
        self.add(*args, **kwargs)

    def add_arg(self, arg):
        if isinstance(arg, str):
            if arg:
                self.append(arg)
        elif isinstance(arg, typing.Iterable):
            for a in arg:
                self.add_arg(a)
        else:
            self.append(str(arg))
        return self

    def add_kwarg(self, key: str, value):
        if isinstance(key, str):
            if isinstance(value, str):
                if value:
                    self.append(key)
                    self.append(value)
            elif isinstance(value, typing.Iterable):
                for v in value:
                    self.add_kwarg(key, v)
            elif value is True:
                self.append(key)
            elif value is None or value is False:
                pass
            else:
                self.append(key)
                self.append(str(value))
        return self

    def add(self, *args, **kwargs):
        for a in args:
            self.add_arg(a)
        for k, v in kwargs.items():
            if k in ("x265_params",):
                self.add_kwarg("-" + k.replace("_", "-"), v)
            else:
                self.add_kwarg("-" + k.replace("__", ":"), v)
        return self


class FFmpegRunnerAlpha:
    exe = "ffmpeg"
    head = FFmpegArgsList(exe)
    body = FFmpegArgsList()
    capture_stdout_stderr = False

    class FFmpegError(Exception):
        def __init__(self, exit_code: int, stderr_content: str):
            self.exit_code = exit_code
            self.stderr_content = stderr_content.splitlines()
            self.cause = None, None, None
            for es in self.stderr_content:
                if es.startswith("Unknown encoder"):
                    self.cause = "encoder", "unknown", es[17:-1]
                elif "Error loading plugins" in es:
                    self.cause = "plugin", "load", None

        def __str__(self):
            return f"{self.__class__.__name__}: {self.exit_code}\n" + "\n".join(
                self.stderr_content
            )

    def __init__(
        self,
        banner: bool = True,
        loglevel: str = None,
        overwrite: bool = None,
        capture_out_err: bool = False,
    ):
        self.logger = ez_get_logger(f"{__name__}.{self.__class__.__name__}")
        self.capture_stdout_stderr = capture_out_err
        self.set_head(banner=banner, loglevel=loglevel, overwrite=overwrite)

    @property
    def cmd(self):
        return self.head + self.body

    def set_head(
        self,
        banner: bool = False,
        loglevel: str = None,
        threads: int = None,
        overwrite: bool = None,
    ):
        h = FFmpegArgsList(self.exe)
        if not banner:
            h.add("-hide_banner")
        if loglevel:
            h.add(loglevel=loglevel)
        if overwrite is True:
            h.add("-y")
        elif overwrite is False:
            h.add("-n")
        if threads:
            h.add(threads=threads)
        self.head = h

    def add_args(self, *args, **kwargs):
        self.body.add(*args, **kwargs)

    def reset_args(self):
        self.body = FFmpegArgsList()

    def set_map_preset(self, map_preset: str):
        if not map_preset:
            return
        self.add_args(map=STREAM_MAP_PRESET_TABLE[map_preset])

    def proc_comm(self, input_bytes: bytes) -> bytes:
        cmd = self.cmd
        self.logger.info(ostk.shlex_double_quotes_join(cmd))
        if self.capture_stdout_stderr:
            p = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        else:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        out, err = p.communicate(input_bytes)
        code = p.returncode
        if code:
            raise self.FFmpegError(code, (err or b"<error not captured>").decode())
        else:
            if err:
                self.logger.debug(err.decode())
            return out or b""

    def proc_run(self, dry_run: bool = False, **kwargs) -> bytes:
        cmd = self.cmd
        self.logger.info(
            ostk.shlex_double_quotes_join(cmd)
        )  # command list to string with quotes
        if dry_run:
            # print('dry run')
            return b""
        if self.capture_stdout_stderr:
            p = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs
            )
        else:
            p = subprocess.run(cmd, **kwargs)
        code = p.returncode
        if code:
            raise self.FFmpegError(code, (p.stderr or b"<error not captured>").decode())
        else:
            if p.stderr:
                self.logger.debug(p.stderr.decode())
            return p.stdout or b""

    @decorator_choose_map_preset
    def concat(
        self,
        input_paths: typing.Iterable[str],
        output_path: str,
        output_args: typing.Iterable[str] = (),
        *,
        input_args=(),
        concat_demuxer: bool = False,
        extra_inputs: typing.Iterable = (),
        start: float or int or str = 0,
        end: float or int or str = 0,
        copy_all: bool = True,
        map_preset: str = None,
        metadata_file: str = None,
        **output_kwargs,
    ):
        if isinstance(start, str):
            start = mylib.ext.tricks.seconds_from_colon_time(start)
        if isinstance(end, str):
            end = mylib.ext.tricks.seconds_from_colon_time(end)
        if start < 0:
            start = max([get_real_duration(f) for f in input_paths]) + start
        if end < 0:
            end = max([get_real_duration(f) for f in input_paths]) + end
        self.reset_args()
        self.add_args(*input_args)
        if start:
            self.add_args(ss=start)
        input_count = 0
        if concat_demuxer:
            concat_list = None
            for file in input_paths:
                input_count += 1
                self.add_args(safe=0, protocol_whitelist="file", f="concat", i=file)
        else:
            input_count += 1
            concat_list = "\n".join(
                ["file '{}'".format(e.replace("'", r"'\''")) for e in input_paths]
            )  # ' -> '\''
            self.add_args(f="concat", safe=0, protocol_whitelist="fd,file,pipe", i="-")
        if extra_inputs:
            input_count += len(extra_inputs)
            self.add_args(i=extra_inputs)
        if metadata_file:
            self.add_args(i=metadata_file, map_metadata=input_count)
        if end:
            self.add_args(t=end - start if start else end)
        if copy_all:
            self.add_args(c="copy")
            if not map_preset:
                self.add_args(map=range(input_count))
        self.set_map_preset(map_preset)
        self.add_args(*output_args, **output_kwargs)
        self.add_args(output_path)
        if concat_list:
            # print(concat_list)
            return self.proc_comm(concat_list.encode())
        else:
            return self.proc_run()

    @decorator_choose_map_preset
    def segment(
        self,
        input_path: str,
        output_path: str = None,
        output_args: typing.Iterable[str] = (),
        *,
        copy: bool = True,
        reset_time: bool = True,
        map_preset: str = None,
        **output_kwargs,
    ):
        self.reset_args()
        if not output_path:
            output_path = "%d" + os.path.splitext(input_path)[-1]
        self.add_args(i=input_path, f="segment")
        if copy:
            self.add_args(c="copy")
        if reset_time:
            self.add_args(reset_timestamps=1)
        self.set_map_preset(map_preset)
        self.add_args(*output_args, **output_kwargs)
        self.add_args(output_path)
        return self.proc_run()

    def metadata_file(self, input_path: str, output_path: str):
        self.reset_args()
        self.add_args(i=input_path, f="ffmetadata")
        self.add_args(output_path)
        return self.proc_run()

    @decorator_choose_map_preset
    def convert(
        self,
        input_paths: typing.Iterable[str],
        output_path: str,
        output_args: typing.Iterable[str] = (),
        *,
        input_args: typing.Iterable[str] = (),
        start: float | int | str = 0,
        end: float | int | str = 0,
        copy_all: bool = False,
        map_preset: str = None,
        metadata_file: str = None,
        dry_run=False,
        **output_kwargs,
    ):
        self.reset_args()

        if isinstance(start, str):
            start = mylib.ext.tricks.seconds_from_colon_time(start)
        if isinstance(end, str):
            end = mylib.ext.tricks.seconds_from_colon_time(end)
        if start < 0:
            start = max([get_real_duration(f) for f in input_paths]) + start
        if end < 0:
            end = max([get_real_duration(f) for f in input_paths]) + end
        if start:
            self.add_args(ss=start)

        self.add_args(*input_args)
        self.add_args(i=input_paths)
        if metadata_file:
            self.add_args(i=metadata_file, map_metadata=len(input_paths))
        if end:
            self.add_args(t=end - start if start else end)

        if copy_all:
            self.add_args(c="copy")
            if not map_preset:
                self.add_args(map=len(input_paths) - 1)
        self.set_map_preset(map_preset)
        self.add_args(*output_args, **output_kwargs)
        self.add_args(output_path)
        return self.proc_run(dry_run=dry_run)

    def img2vid(
        self, img_src: str, res_fps: str, vid_path: str, *output_args, **output_kwargs
    ):
        res, fps = res_fps.split("@", maxsplit=1)
        fps = float(fps)
        width, height = map(int, res.split("x", maxsplit=1))
        return self.convert(
            (img_src,),
            vid_path,
            FFmpegArgsList(
                vf=f"scale={width}:{height}:force_original_aspect_ratio=1,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
                *output_args,
                **output_kwargs,
            ),
            input_args=FFmpegArgsList(r=fps),
        )


def get_width_height(filepath) -> (int, int):
    d = ffmpeg.probe(filepath, select_streams="V")["streams"][0]
    return d["width"], d["height"]


@mylib.easy.deco_factory_param_value_choices(
    {
        "res_limit": (
            None,
            "FHD",
            "HD",
            "qHD",
            "QHD",
            "4K",
            "2K",
            "360p",
            "512x",
            "320x",
            "256x",
            "160x",
        )
    }
)
def get_vf_res_scale_down(
    width: int, height: int, res_limit="FHD", vf: str = "", flags=None
) -> str:
    """generate 'scale=<w>:<h>' value for ffmpeg `vf` option, to scale down the given resolution
    return empty str if the given resolution is enough low thus scaling is not needed"""
    d = {
        "FHD": (1920, 1080),
        "HD": (1280, 720),
        "qHD": (960, 540),
        "QHD": (2560, 1440),
        "4K": (3840, 2160),
        "2K": (2560, 1440),
        "360p": (640, 360),
        "512x": (512, 512),
        "320x": (320, 320),
        "256x": (256, 256),
        "160x": (160, 160),
    }
    auto_calc = -2
    if not res_limit:
        return vf
    tgt_long, tgt_short = d[res_limit]
    long = max((width, height))
    short = min((width, height))
    if long <= tgt_long and short <= tgt_short:
        return vf
    ratio = short / long
    tgt_ratio = tgt_short / tgt_long
    thin = False if ratio > tgt_ratio else True
    portrait = True if height > width else False
    baseline = tgt_long if thin else tgt_short
    res_scale = "scale=" + (
        f"{baseline}:{auto_calc}" if thin ^ portrait else f"{auto_calc}:{baseline}"
    )
    if flags:
        res_scale += f":flags={flags}"
    return f"{vf},{res_scale}" if vf else res_scale


def get_filter_list(filters):
    if not filters:
        return []
    elif isinstance(filters, str):
        return [filters]
    elif isinstance(filters, typing.Iterable):
        return list(filters)
    else:
        return []


def get_filter_str(filters):
    return ",".join(get_filter_list(filters))


def kw_video_convert(
    filepath,
    keywords=(),
    vf=None,
    cut_points=(),
    overwrite=False,
    redo=False,
    ffmpeg_opts=(),
    verbose=0,
    dry_run=False,
    force=False,
    **kwargs,
):
    ff = FFmpegRunnerAlpha(overwrite=True, banner=False)
    if verbose > 1:
        lvl = "DEBUG"
    elif verbose > 0:
        lvl = "INFO"
    else:
        lvl = "WARNING"
    ff.logger.setLevel(lvl)
    vf_list = get_filter_list(vf)
    vf_str = get_filter_str(vf_list)
    ffmpeg_input_args = FFmpegArgsList()
    logger = ez_get_logger(f"{__name__}.smartconv", fmt=LOG_FMT_MESSAGE_ONLY)
    codecs_d = {
        "h": "hevc",
        "a": None,
        "hq": "hevc_qsv",
        "aq": "h264_qsv",
        "v": "vp9",
        "hnv": "hevc_nvenc",
        "anv": "h264_nvenc",
    }
    tags = []

    lp = tui.LinePrinter()
    lp.l()

    if not os.path.isfile(filepath):
        logger.info(f"# skip non-file\n {filepath}")
        return
    if not force and ".hevc8b." in filepath:
        logger.info(f"#skip hevc8b file\n {filepath}")
        return
    if not force and filepath[-8:] == ".gif.mp4":
        logger.info(f"#skip gif mp4 file\n {filepath}")
        return
    yaml_sidecar_file = filepath + ".yaml"
    if os.path.isfile(yaml_sidecar_file):
        if not redo:
            logger.info(f"# skip with sidecar yaml file\n {filepath}")
            return
    if filepath[-4:] not in (".swf",):
        if not file_is_video(filepath) and not file_is_audio(filepath):
            logger.info(f"# skip non-video-audio\n {filepath}")
            return

    ft = filetype.guess(filepath)
    if ft and ft.mime == "image/vnd.adobe.photoshop":
        ff.convert([filepath], filepath + ".png")
        return

    if "10bit" in keywords:
        ffmpeg_output_args = FFmpegArgsList(pix_fmt="yuv420p10le")
        bits_tag_l = ["10bit"]
        # 如果有`-hwaccel_output_format cuda`的参数存在的话，可能需要指定其他的、能够被GPU内部cuda所支持的像素格式，`p010le`也许符合要求
    else:
        # ffmpeg_output_args = FFmpegArgsList(pix_fmt='yuv420p')
        ffmpeg_output_args = FFmpegArgsList()
        bits_tag_l = []
    keywords = set(keywords) or set()
    res_limit = None
    codec = "a"
    crf = None

    if "smartblur" in keywords:
        vf_list.append("smartblur")

    output_ext = None
    scale_flags = None
    allow_cuda = True
    for kw in keywords:
        if kw[0] + kw[-1] in ("vk", "vM") and kw[1:-1].isdecimal():
            ffmpeg_output_args.add(b__v=kw[1:])
        elif kw in ("lanczos", "spline", "area"):
            allow_cuda = False
            scale_flags = kw
            # tags.append(kw)
        elif kw == "novid":
            ffmpeg_output_args.add(vn=True)
        elif kw[0] == "." and "." not in kw[1:]:
            output_ext = kw
        elif kw[:3] == "crf" and kw[:4] != "crf+":
            crf = kw[3:]
        elif kw[0] + kw[-1] == "ak" and kw[1:-1].isdecimal():
            ffmpeg_output_args.add(b__a=kw[1:])
        elif kw[:3] == "fps":
            ffmpeg_output_args.add(r=kw[3:])
            tags.append(kw)
        elif kw == "vcopy":
            ffmpeg_output_args.add(c__V="copy")
        elif kw == "acopy":
            ffmpeg_output_args.add(c__a="copy")
        elif kw == "scopy":
            ffmpeg_output_args.add(c__s="copy")
        elif kw == "all":
            ffmpeg_output_args.add(map=0)
        elif kw == "copy":
            ffmpeg_output_args.add(c="copy")
        elif kw in ("FHD", "fhd"):
            res_limit = "FHD"
        elif kw in ("HD", "hd"):
            res_limit = "HD"
        elif kw in ("qHD", "qhd"):
            res_limit = "qHD"
        elif kw.lower() in ("360p", "512x", "320x", "256x", "160x"):
            res_limit = kw.lower()
        elif kw.lower() in ("2k", "4k"):
            res_limit = kw.upper()
        elif re.match(r"\dch$", kw):
            ffmpeg_output_args.add(ac=kw[:1])
            tags.append(kw)
        elif re.match(r"copy\w\d+$", kw):
            ffmpeg_output_args.add_kwarg(f"-c:{kw[4:5]}:{kw[5:]}", "copy")
        elif kw == "hevc":
            codec = "h"
        elif kw in ("vp9", "vpx", "vp90", "webm"):
            codec = "v"
        elif kw == "tv2pc":
            vf_list.append("scale=in_range=limited:out_range=full")
            tags.append(kw)
        elif kw == "opus":
            ffmpeg_output_args.add(c__a="libopus")
            # tags.append(kw)

    word = "nvdec"
    if word in keywords:
        ffmpeg_input_args.add(hwaccel=word)
    word = "cuda"
    if word in keywords and allow_cuda:
        ffmpeg_input_args.add(hwaccel_output_format=word)

    if res_limit:
        try:
            w, h = get_width_height(filepath)
        except IndexError:
            ff.logger.info(f"# no video stream: {filepath}")
            return
        new_vf = get_vf_res_scale_down(w, h, res_limit, vf=vf_str, flags=scale_flags)
        if "cuda" in keywords and allow_cuda:
            new_vf = new_vf.replace("scale=", "scale_cuda=")
        ffmpeg_output_args.add(filter__V__0=new_vf)
        if new_vf != vf_str:
            tags.append(res_limit)
    else:
        ffmpeg_output_args.add(filter__V__0=vf_str)

    if "best" in keywords:
        codec = "h"
        crf = crf or 16
    elif "better" in keywords:
        codec = "h"
        crf = crf or 19
    elif "good" in keywords:
        codec = "h"
        crf = crf or 22
    elif "bad" in keywords:
        codec = "h"
        crf = crf or 25
    elif "worse" in keywords:
        codec = "h"
        crf = crf or 28
    elif "worst" in keywords:
        codec = "h"
        crf = crf or 31
    elif "worster" in keywords:
        codec = "h"
        crf = crf or 34
    elif "worstest" in keywords:
        codec = "h"
        crf = crf or 37
    elif "bester" in keywords:
        codec = "h"
        crf = crf or 13
    elif "bestest" in keywords:
        codec = "h"
        crf = crf or 10


    for kw in keywords:
        if kw[:4] == "crf+":
            crf += type(crf)(kw[4:])

    codec_tag = CODEC_TAGS_DICT[f"{codec}"]
    if "qsv" in keywords and codec in ("a", "h"):
        tags.append("qsv")
        codec += "q"
        crf = None
        ffmpeg_output_args.add(vcodec=codecs_d[codec])
    elif "nvenc" in keywords and codec in ("a", "h"):
        tags.append("nvenc")
        codec += "nv"
        # ffmpeg_output_args.add(c__V=codecs_d[codec], rc='constqp', qp=crf)
        ffmpeg_output_args.add(c__V=codecs_d[codec], cq=int(crf) + 6)
        ffmpeg_output_args.add(preset="p5")
        # ffmpeg_output_args.add_kwarg('-rc-lookahead', 30)
        # ffmpeg_output_args.add_kwarg('-spatial-aq', 1)
        # ffmpeg_output_args.add_kwarg('-temporal-aq', 1)
        # if crf is not None:
        #     ffmpeg_output_args.add(b__v=0)
        for kw in keywords:
            if kw[0] == "p" and kw[1:].isdecimal():
                ffmpeg_output_args.add(preset=kw)

    else:
        ffmpeg_output_args.add(vcodec=codecs_d[codec], crf=crf)
    if codec == "h":
        ffmpeg_output_args.add_kwarg("-x265-params", "aq-mode=3")
    ffmpeg_output_args.add(ffmpeg_opts)

    if keywords & {"copy", "vcopy"}:
        tags.append("copy")
    elif keywords & {"m4a", "aac"}:
        tags.append("audio")
    else:
        tags.append(codec_tag)
        tags.extend(bits_tag_l)

    cut_points = cut_points or []
    start = cut_points[0] if cut_points else 0
    end = cut_points[1] if len(cut_points) >= 2 else 0

    new_ext = ""
    input_ft = EnclosedFilenameTags(filepath, preamble=" +")
    origin_ft = EnclosedFilenameTags(filepath, preamble=" +").tag("origin")
    output_ft = EnclosedFilenameTags(filepath, preamble=" +").untag("crf", "origin")
    if output_ext:
        output_ft.extension = output_ext
    if crf is not None:
        output_ft.tag(crf=crf)
    if not redo and "origin" in input_ft.tags:
        logger.info(f"# skip origin\n  {filepath}")
        return
    input_codec_tags = input_ft.tags & CODEC_TAGS_SET - {"origin"}
    if input_codec_tags and not force:
        logger.info(f"# skip {input_codec_tags}\n  {filepath}")
        return
    if "gif" in keywords:
        new_ext = ".gif"
        # ffmpeg_output_args.add(pix_fmt='rgb24') # not supported
        tags.remove("h264")
    if "mp4" in keywords:
        new_ext = ".mp4"
        ffmpeg_output_args.add(movflags="faststart")
    if "mkv" in keywords:
        new_ext = ".mkv"
        # ffmpeg_output_args.add(c__a='libopus')
        # if choose opus as audio codec, then stream bitrate in mkv will lose
        # need "statistic tags" to specify these bitrate info inside metadata
        # but ffmpeg not support that :(
    if "m4a" in keywords:
        new_ext = ".m4a"
        ffmpeg_output_args.add(map=STREAM_MAP_PRESET_TABLE[S_NO_VIDEO])
    if "aac" in keywords:
        new_ext = ".aac"
    if "webm" in keywords:
        new_ext = ".webm"
    if "mka" in keywords:
        new_ext = ".mka"
        if "h264" in tags:
            tags.remove("h264")
    if new_ext:
        if "append_ext" in keywords:
            output_ft.extension += new_ext
        else:
            output_ft.extension = new_ext
    output_ft = output_ft.tag(*tags)
    if "no_tag" in keywords:
        origin_ft.clear()
        output_ft.clear()

    origin_path = origin_ft.path
    output_path = output_ft.path
    if os.path.isfile(output_path) and not overwrite:
        logger.info(f"# skip existing\n  {output_path}")
        return
    logger.info(f"* {tags}\n  {filepath}")
    lp.l()

    try:
        try:
            ff.convert(
                [filepath],
                output_path,
                ffmpeg_output_args,
                input_args=ffmpeg_input_args,
                start=start,
                end=end,
                dry_run=dry_run,
                **kwargs,
            )
        except ff.FFmpegError as e:
            if (
                e.exit_code == 4294967256
                and "cuda" in keywords
                and "-hwaccel_output_format" in ffmpeg_input_args
                and "cuda" in ffmpeg_input_args
            ):
                ffmpeg_input_args.remove("-hwaccel_output_format")
                ffmpeg_input_args.remove("cuda")
                _i = ffmpeg_output_args.index("-filter:V:0")
                ffmpeg_output_args[_i + 1] = new_vf.replace("scale_cuda=", "scale=")

            ff.convert(
                [filepath],
                output_path,
                ffmpeg_output_args,
                input_args=ffmpeg_input_args,
                start=start,
                end=end,
                dry_run=dry_run,
                **kwargs,
            )
        logger.info(f"+ {output_path}")
        shutil.move(filepath, origin_path)
    except ff.FFmpegError as e:
        logger.error(f"! {output_path}\n {e}")
        os.remove(output_path)
    except KeyboardInterrupt:
        logger.warning(f"- {output_path}")
        os.remove(output_path)
        sys.exit(2)


def parse_kw_opt_str(kw: str):
    if kw[:3] == "crf" and kw[3:].isdecimal():
        return FFmpegArgsList(crf=float(kw[3:]))
    if kw == "hevc":
        return FFmpegArgsList(c__V="hevc")
    if f"{kw[:1]}{kw[-1:]}".lower() in ("vk", "vm") and kw[1:-1].isdecimal():
        return FFmpegArgsList(b__V=0 if kw[1:-1] == "0" else kw[1:])
    if f"{kw[:1]}{kw[-1:]}".lower() in ("ak", "am") and kw[1:-1].isdecimal():
        return FFmpegArgsList(b__a=0 if kw[1:-1] == "0" else kw[1:])
    if kw == "10bit":
        return FFmpegArgsList(pix_fmt="yuv420p10le")


def guess_video_crf(src, codec, *, redo=False, work_dir=None, auto_clean=True):
    tf = EnclosedFilenameTags(src, preamble=" +")
    if not redo and "crf" in tf.keys:
        return float(tf.tags_dict["crf"])
    c = FFmpegSegmentsContainer(src, work_dir=work_dir, log_lvl="WARNING")
    try:
        crf_guess = c.guess_crf(codec)
        tf.tag(crf=round(crf_guess))
        shutil.move(src, tf.path)
        return crf_guess
    finally:
        if auto_clean:
            c.purge()


class FFmpegSegmentsContainer:
    nickname = "ffsegcon"
    tag_file = "FFMPEG_SEGMENTS_CONTAINER.TAG"
    tag_sig = "Signature: " + mylib.ext.tricks.hex_hash(tag_file.encode())
    picture_file = "p.mp4"
    non_visual_file = "nv.mkv"
    test_json = "t.json"
    metadata_file = "metadata.txt"
    concat_list_file = "concat.txt"
    suffix_done = ".DONE"
    suffix_lock = ".LOCK"
    suffix_delete = ".DELETE"
    segment_filename_regex_pattern = r"^\d+\.[^.]+"
    input_filename_prefix = "i="
    input_json = "i.json"
    input_prefix = "i-"
    input_picture = input_prefix + picture_file
    input_non_visual = input_prefix + non_visual_file
    input_filepath = None
    input_data = None
    output_filename_prefix = "o="
    output_prefix = "o-"
    output_json = "o.json"
    output_data = None

    class PathError(Exception):
        pass

    class ContainerError(Exception):
        pass

    class SegmentLockedError(Exception):
        pass

    class SegmentNotDoneError(Exception):
        pass

    class SegmentDeleteRequest(Exception):
        pass

    class SegmentMissing(Exception):
        pass

    def __repr__(self):
        return "{} at '{}' from '{}'".format(
            FFmpegSegmentsContainer.__name__, self.root, self.input_filepath
        )

    def __init__(
        self,
        path: str,
        work_dir: str = None,
        single_video_stream: bool = True,
        log_lvl=None,
    ):
        self.logger = ez_get_logger(f"{__name__}.{self.nickname}")
        self.ff = FFmpegRunnerAlpha(
            banner=False, loglevel="warning", overwrite=True, capture_out_err=True
        )
        if log_lvl:
            self.logger.setLevel(log_lvl)
            self.ff.logger.setLevel(log_lvl)
        _path = os.path.abspath(path)
        select_streams = "V:0" if single_video_stream else "V"
        if not os.path.exists(_path):
            raise self.PathError("path not exist: '{}'".format(_path))

        if os.path.isfile(_path):
            self.input_filepath = _path
            if file_is_video(_path):
                d, b = os.path.split(_path)
                self.input_data = {S_FILENAME: b, S_SEGMENT: {}, S_NON_SEGMENT: {}}
                with mylib.easy.io.SubscriptableFileIO(_path) as f:
                    middle = f.size // 2
                    root_base = ".{}-{}".format(
                        self.nickname,
                        mylib.ext.tricks.hex_hash(
                            f[:4096] + f[middle - 2048 : middle + 2048] + f[-4096:]
                        )[:8],
                    )
                work_dir = work_dir or d
                _path = self.root = os.path.join(
                    work_dir, root_base
                )  # file path -> dir path
            else:
                raise self.PathError("non-video file: '{}'".format(_path))

        try:
            if not os.path.isdir(_path):
                try:
                    os.makedirs(_path, exist_ok=True)
                except FileExistsError:
                    raise self.PathError(
                        "invalid folder path used by file: '{}'".format(_path)
                    )
                self.tag_container_folder()
                self.split(select_streams=select_streams)

            if os.path.isdir(_path):
                try:
                    self.root = _path
                    if not self.container_is_tagged():
                        shutil.rmtree(self.root)
                        raise self.ContainerError(
                            "non-container folder: '{}'".format(_path)
                        )
                    if not self.is_split():
                        self.split(select_streams=select_streams)
                    self.read_input_json()
                    if S_FILENAME not in self.input_data:
                        self.read_filename()
                    self.read_output_json()
                except KeyError:
                    shutil.rmtree(_path)
                    self = FFmpegSegmentsContainer(
                        path=path,
                        work_dir=work_dir,
                        single_video_stream=single_video_stream,
                        log_lvl=log_lvl,
                    )
        except KeyboardInterrupt:
            sleep(0.5)
            shutil.rmtree(_path)
            raise self.ContainerError("aborted")

    def write_filename(self):
        if self.input_filepath:
            fn = os.path.split(self.input_filepath)[-1]
        else:
            fn = self.input_data.get(S_FILENAME)
        if not fn:
            return
        self.input_data[S_FILENAME] = fn
        with oldezpykit.stdlib.os.common.ctx_pushd(self.root):
            prefix = self.input_filename_prefix
            for f in fs_find_iter(
                pattern=prefix + "*", recursive=False, strip_root=True
            ):
                fstk.x_rename(f, prefix + fn, append_src_ext=False)
                break
            else:
                oldezpykit.stdlib.os.common.touch(prefix + fn)
            fstk.write_json_file(self.input_json, self.input_data, indent=4)

    def read_filename(self):
        with oldezpykit.stdlib.os.common.ctx_pushd(self.root):
            prefix = self.input_filename_prefix
            for f in fs_find_iter(
                pattern=prefix + "*", recursive=False, strip_root=True
            ):
                filename = f.lstrip(prefix)
                self.input_data[S_FILENAME] = filename
                return filename
            else:
                raise self.ContainerError("no filename found")

    def split(self, select_streams="V:0"):
        i_file = self.input_filepath
        if not i_file:
            raise self.ContainerError("no input filepath")
        d = self.input_data or {S_SEGMENT: {}, S_NON_SEGMENT: {}}

        with oldezpykit.stdlib.os.common.ctx_pushd(self.root):
            for stream in ffmpeg.probe(i_file, select_streams=select_streams)[
                "streams"
            ]:
                index = stream["index"]
                # codec = stream['codec_name']
                # suitable_filext = CODEC_NAME_TO_FILEXT_TABLE.get(codec)
                # segment_output = '%d' + suitable_filext if suitable_filext else None
                segment_output = "%d.mkv"
                index = str(index)
                d[S_SEGMENT][index] = {}
                seg_folder = self.input_prefix + index
                os.makedirs(seg_folder, exist_ok=True)
                with oldezpykit.stdlib.os.common.ctx_pushd(seg_folder):
                    self.ff.segment(i_file, segment_output, map="0:{}".format(index))
            try:
                self.ff.convert(
                    [i_file],
                    self.input_picture,
                    copy_all=True,
                    map_preset=S_ONLY_PICTURE,
                )
                d[S_NON_SEGMENT][self.picture_file] = {}
            except self.ff.FFmpegError:
                pass
            try:
                self.ff.convert(
                    [i_file],
                    self.input_non_visual,
                    copy_all=True,
                    map_preset=S_ALL,
                    map="-0:v",
                )
                d[S_NON_SEGMENT][self.non_visual_file] = {}
            except self.ff.FFmpegError:
                pass

        self.input_data = d
        self.write_metadata()
        self.write_input_json()

    def write_metadata(self):
        with oldezpykit.stdlib.os.common.ctx_pushd(self.root):
            self.ff.metadata_file(self.input_filepath, self.metadata_file)
            with open(self.metadata_file, encoding="utf8") as f:
                meta_lines = f.readlines()
            meta_lines = [
                line
                for line in meta_lines
                if line.partition("=")[0]
                not in (
                    "encoder",
                    "major_brand",
                    "minor_version",
                    "compatible_brands",
                    "compilation",
                    "media_type",
                )
            ]
            with open(self.metadata_file, "w", encoding="utf8") as f:
                f.writelines(meta_lines)

    def write_input_json(self):
        d = self.input_data or {}
        prefix = self.input_prefix

        with oldezpykit.stdlib.os.common.ctx_pushd(self.root):
            for k in d[S_SEGMENT]:
                seg_folder = prefix + k
                d[S_SEGMENT][k] = {}
                with oldezpykit.stdlib.os.common.ctx_pushd(seg_folder):
                    for file in fs_find_iter(
                        pattern=self.segment_filename_regex_pattern,
                        regex=True,
                        recursive=False,
                        strip_root=True,
                    ):
                        d[S_SEGMENT][k][file] = excerpt_single_video_stream(file)
            for k in d[S_NON_SEGMENT]:
                file = prefix + k
                if os.path.isfile(file):
                    d[S_NON_SEGMENT][k] = ffmpeg.probe(file)
                else:
                    del d[S_NON_SEGMENT][k]
            fstk.write_json_file(self.input_json, d, indent=4)

        self.input_data = d

    def read_input_json(self):
        with oldezpykit.stdlib.os.common.ctx_pushd(self.root):
            self.input_data = fstk.read_json_file(self.input_json)
        self.write_filename()
        return self.input_data

    def read_output_json(self):
        with oldezpykit.stdlib.os.common.ctx_pushd(self.root):
            self.output_data = fstk.read_json_file(self.output_json)
            if not self.output_data:
                self.config()
                self.output_data = fstk.read_json_file(self.output_json)
        return self.output_data

    def write_output_json(self):
        with oldezpykit.stdlib.os.common.ctx_pushd(self.root):
            fstk.write_json_file(self.output_json, self.output_data, indent=4)

    def tag_container_folder(self):
        with oldezpykit.stdlib.os.common.ctx_pushd(self.root):
            with open(self.tag_file, "w") as f:
                f.write(self.tag_sig)

    def container_is_tagged(self) -> bool:
        with oldezpykit.stdlib.os.common.ctx_pushd(self.root):
            try:
                with open(self.tag_file) as f:
                    return f.readline().rstrip("\r\n") == self.tag_sig
            except FileNotFoundError:
                return False

    def is_split(self) -> bool:
        return bool(self.read_input_json())

    def purge(self):
        shutil.rmtree(self.root, ignore_errors=True)
        self.__dict__ = {}

    def config(
        self,
        video_args: FFmpegArgsList = None,
        other_args: FFmpegArgsList = None,
        more_args: FFmpegArgsList = None,
        non_visual_map: typing.Iterable[str] = (),
        filename: str = None,
        **kwargs,
    ):
        video_args = video_args or FFmpegArgsList()
        other_args = other_args or FFmpegArgsList()
        more_args = more_args or FFmpegArgsList()
        videos = self.input_data[S_SEGMENT].keys()
        others = self.input_data[S_NON_SEGMENT].keys()
        need_map = True if len(videos) > 1 or self.picture_file in others else False
        d = self.output_data or {}
        d[S_ORIGINAL] = {
            "video_args": video_args,
            "other_args": other_args,
            "more_args": more_args,
            "non_visual_map": non_visual_map,
            "filename": filename,
            **kwargs,
        }
        input_count = 0

        d[S_VIDEO] = []
        for index in videos:
            args = FFmpegArgsList()
            if need_map:
                args.add(map=input_count)
            i_args = (
                os.path.join(self.output_prefix + index, self.concat_list_file),
                args,
            )
            d[S_VIDEO].append(i_args)
            input_count += 1

        d[S_OTHER] = []
        for o in others:
            args = FFmpegArgsList()
            if o == self.non_visual_file:
                if non_visual_map:
                    for m in non_visual_map:
                        if m.startswith("-"):
                            args.add(map="-{}:{}".format(input_count, m.lstrip("-")))
                        else:
                            args.add(map="{}:{}".format(input_count, m))
                elif need_map:
                    args.add(map=input_count)
                args += other_args
                i_args = self.input_prefix + o, args
                d[S_OTHER].append(i_args)
            else:
                if need_map:
                    args.add(map=input_count)
                i_args = self.input_prefix + o, args
                d[S_OTHER].append(i_args)
            input_count += 1

        d[S_SEGMENT] = video_args
        d[S_MORE] = FFmpegArgsList(vcodec="copy") + more_args
        d[S_FILENAME] = filename or self.input_data[S_FILENAME]
        d["kwargs"] = kwargs

        self.output_data = d
        self.write_output_json()
        self.write_output_concat_list_file()

    def config_other_args(self, other_args: FFmpegArgsList):
        conf = self.read_output_json()
        conf[S_ORIGINAL]["other_args"] = other_args
        self.config(**conf[S_ORIGINAL])

    def config_more_args(self, more_args: FFmpegArgsList):
        conf = self.read_output_json()
        conf[S_ORIGINAL]["more_args"] = more_args
        self.config(**conf[S_ORIGINAL])

    def config_non_visual_map(self, non_visual_map: typing.Iterable[str]):
        conf = self.read_output_json()
        conf[S_ORIGINAL]["non_visual_map"] = non_visual_map
        self.config(**conf[S_ORIGINAL])

    def config_kwargs(self, **kwargs):
        conf = self.read_output_json()
        conf[S_ORIGINAL].update(kwargs)
        self.config(**conf[S_ORIGINAL])

    def config_filename(self, filename):
        conf = self.read_output_json()
        conf[S_ORIGINAL][S_FILENAME] = filename
        self.config(**conf[S_ORIGINAL])

    def config_video(
        self,
        video_args: FFmpegArgsList = None,
        crf=None,
        vf=None,
        res_limit=None,
        **kwargs,
    ):
        conf = self.read_output_json()
        video_args = video_args or FFmpegArgsList()
        vf = self.vf_res_scale_down(res_limit, vf)
        video_args.add(crf=crf, vf=vf, **kwargs)
        conf[S_ORIGINAL]["video_args"] = video_args
        self.config(**conf[S_ORIGINAL])

    def config_hevc(
        self,
        video_args: FFmpegArgsList = None,
        crf=None,
        vf=None,
        res_limit=None,
        x265_log_level: str = "error",
        **x265_params,
    ):
        conf = self.read_output_json()
        video_args = video_args or FFmpegArgsList()
        x265_params_s = f"log-level={x265_log_level}"
        for k in x265_params:
            k_s = k.replace("_", "-")
            x265_params_s += f":{k_s}={x265_params[k]}"
        vf = self.vf_res_scale_down(res_limit, vf)
        video_args.add(vcodec="hevc", x265_params=f"{x265_params_s}", crf=crf, vf=vf)
        conf[S_ORIGINAL]["video_args"] = video_args
        self.config(**conf[S_ORIGINAL])

    def config_vp9(
        self,
        video_args: FFmpegArgsList = None,
        crf=None,
        vf=None,
        res_limit=None,
        constrained_quality=False,
        **kwargs,
    ):
        conf = self.read_output_json()
        video_args = video_args or FFmpegArgsList()
        video_args.add(threads=4, vcodec="libvpx-vp9")
        vf = self.vf_res_scale_down(res_limit, vf)
        if not constrained_quality:
            video_args.add(b__V=0)
        video_args.add(crf=crf, vf=vf, **kwargs)
        conf[S_ORIGINAL]["video_args"] = video_args
        self.config(**conf[S_ORIGINAL])

    def config_qsv_avc(
        self,
        video_args: FFmpegArgsList = None,
        crf=None,
        vf=None,
        res_limit=None,
        **kwargs,
    ):
        conf = self.read_output_json()
        video_args = video_args or FFmpegArgsList()
        vf = self.vf_res_scale_down(res_limit, vf)
        video_args.add(vcodec="h264_qsv", global_quality=crf, vf=vf, **kwargs)
        conf[S_ORIGINAL]["video_args"] = video_args
        self.config(**conf[S_ORIGINAL])

    def merge(self):
        if not self.read_output_json():
            raise self.ContainerError("no output config")
        if self.list_lock_segments() or len(self.list_done_segments()) != len(
            self.list_all_segments()
        ):
            raise self.SegmentMissing
        d = self.output_data
        concat_list = []
        extra_input_list = []
        output_args = []
        for i, args in d[S_VIDEO]:
            concat_list.append(i)
            output_args.extend(args)
        for i, args in d[S_OTHER]:
            extra_input_list.append(i)
            output_args.extend(args)
        output_args.extend(d[S_MORE])
        with oldezpykit.stdlib.os.common.ctx_pushd(self.root):
            self.ff.concat(
                concat_list,
                d[S_FILENAME],
                output_args,
                concat_demuxer=True,
                extra_inputs=extra_input_list,
                copy_all=False,
                metadata_file=self.metadata_file,
                **d["kwargs"],
            )

    def write_output_concat_list_file(self):
        with oldezpykit.stdlib.os.common.ctx_pushd(self.root):
            d = self.input_data[S_SEGMENT]
            for index in d:
                folder = self.output_prefix + index
                os.makedirs(folder, exist_ok=True)
                with oldezpykit.stdlib.os.common.ctx_pushd(folder):
                    lines = [
                        "file '{}'".format(os.path.join(folder, seg))
                        for seg in sorted(
                            d[index].keys(), key=lambda x: int(os.path.splitext(x)[0])
                        )
                    ]
                    with fstk.ensure_open_file(self.concat_list_file, "w") as f:
                        f.write("\n".join(lines))

    def file_has_lock(self, filepath):
        return os.path.isfile(filepath + self.suffix_lock)

    def file_has_done(self, filepath):
        return os.path.isfile(filepath + self.suffix_done)

    def file_has_delete(self, filepath):
        return os.path.isfile(filepath + self.suffix_delete)

    def list_all_segments(self):
        segments = []
        for i, d in self.input_data[S_SEGMENT].items():
            segments.extend((i, f) for f in d)
        return segments

    def list_untouched_segments(self):
        all_segments = self.list_all_segments()
        lock_segments = self.list_lock_segments()
        done_segments = self.list_done_segments()
        return mylib.ext.tricks.remove_from_list(
            mylib.ext.tricks.remove_from_list(all_segments, lock_segments),
            done_segments,
        )

    def list_lock_segments(self):
        segments = []
        prefix = self.output_prefix
        with oldezpykit.stdlib.os.common.ctx_pushd(self.root):
            for index in self.input_data[S_SEGMENT]:
                with oldezpykit.stdlib.os.common.ctx_pushd(prefix + index):
                    segments.extend(
                        [
                            (index, f.rstrip(self.suffix_lock))
                            for f in fs_find_iter("*" + self.suffix_lock)
                        ]
                    )
        return segments

    def list_done_segments(self):
        segments = []
        prefix = self.output_prefix
        with oldezpykit.stdlib.os.common.ctx_pushd(self.root):
            for index in self.input_data[S_SEGMENT]:
                with oldezpykit.stdlib.os.common.ctx_pushd(prefix + index):
                    segments.extend(
                        [
                            (index, f.rstrip(self.suffix_done))
                            for f in fs_find_iter("*" + self.suffix_done)
                        ]
                    )
        return segments

    def convert(self, overwrite: bool = False):
        if overwrite:

            def get_segments():
                return self.list_all_segments()

        else:

            def get_segments():
                return self.list_untouched_segments()

        segments = get_segments()
        while segments:
            # stream_id, segment_file = random.choice(segments)
            stream_id, segment_file = segments.pop(0)
            self.convert_one_segment(stream_id, segment_file, overwrite=overwrite)

    def nap(self):
        t = round(random.uniform(0.2, 0.4), 3)
        self.logger.debug("sleep {}s".format(t))
        sleep(t)

    def file_tag_lock(self, filepath):
        if self.file_has_lock(filepath) or self.file_has_done(filepath):
            return
        else:
            oldezpykit.stdlib.os.common.touch(filepath + self.suffix_lock)

    def file_tag_unlock(self, filepath):
        if self.file_has_lock(filepath):
            os.remove(filepath + self.suffix_lock)

    def file_tag_done(self, filepath):
        if self.file_has_done(filepath):
            return
        if self.file_has_lock(filepath):
            fstk.x_rename(
                filepath + self.suffix_lock,
                filepath + self.suffix_done,
                stay_in_src_dir=False,
                append_src_ext=False,
            )

    def file_tag_delete(self, filepath):
        oldezpykit.stdlib.os.common.touch(filepath + self.suffix_delete)

    def convert_one_segment(self, stream_id, segment_file, overwrite=False) -> dict:
        segment_path_no_prefix = os.path.join(stream_id, segment_file)
        i_seg = self.input_prefix + segment_path_no_prefix
        o_seg = self.output_prefix + segment_path_no_prefix
        args = self.output_data[S_SEGMENT]
        with oldezpykit.stdlib.os.common.ctx_pushd(self.root):
            self.nap()
            if self.file_has_lock(o_seg):
                raise self.SegmentLockedError
            if not overwrite and self.file_has_done(o_seg):
                return self.get_done_segment_info(filepath=o_seg)
            self.file_tag_lock(o_seg)
            try:
                saved_error = None
                self.ff.convert([i_seg], o_seg, args)
                self.nap()
                if self.file_has_delete(o_seg):
                    self.logger.info("delete {}".format(o_seg))
                    os.remove(o_seg)
                    raise self.SegmentDeleteRequest
                else:
                    self.file_tag_done(o_seg)
                    return self.get_done_segment_info(filepath=o_seg)
            except Exception as e:
                saved_error = e
            finally:
                self.file_tag_unlock(o_seg)
                if saved_error:
                    raise saved_error

    def get_done_segment_info(
        self, stream_id=None, segment_filename=None, filepath=None
    ) -> dict:
        if filepath:
            o_seg = filepath
        else:
            o_seg = os.path.join(self.output_prefix + stream_id, segment_filename)
        with oldezpykit.stdlib.os.common.ctx_pushd(self.root):
            if not self.file_has_done(o_seg):
                raise self.SegmentNotDoneError
            return excerpt_single_video_stream(o_seg)

    def estimate(self, overwrite=True) -> dict:
        d = {}
        segments = self.input_data[S_SEGMENT]
        for stream_id in segments:
            d[stream_id] = sd = {}
            segments_sorted_by_rate = sorted(
                [(k, v) for k, v in segments[stream_id].items() if v["duration"] >= 1],
                key=lambda x: x[-1]["bit_rate"],
            )
            min_rate_seg_f, min_rate_seg_d = segments_sorted_by_rate[0]
            max_rate_seg_f, max_rate_seg_d = segments_sorted_by_rate[-1]
            sd["min"] = {
                "file": min_rate_seg_f,
                "input": min_rate_seg_d,
                "output": self.convert_one_segment(
                    stream_id, min_rate_seg_f, overwrite=overwrite
                ),
            }
            sd["max"] = {
                "file": max_rate_seg_f,
                "input": max_rate_seg_d,
                "output": self.convert_one_segment(
                    stream_id, max_rate_seg_f, overwrite=overwrite
                ),
            }
            sd["min"]["ratio"] = round(
                sd["min"]["output"]["bit_rate"] / sd["min"]["input"]["bit_rate"], 3
            )
            sd["max"]["ratio"] = round(
                sd["max"]["output"]["bit_rate"] / sd["max"]["input"]["bit_rate"], 3
            )

            k = (sd["max"]["output"]["bit_rate"] - sd["min"]["output"]["bit_rate"]) / (
                sd["max"]["input"]["bit_rate"] - sd["min"]["input"]["bit_rate"]
            )

            def linear_estimate(input_bit_rate):
                return (
                    k * (input_bit_rate - sd["min"]["input"]["bit_rate"])
                    + sd["min"]["output"]["bit_rate"]
                )

            total_duration = 0
            total_input_size = 0
            estimated_output_size = 0
            for seg_d in segments[stream_id].values():
                estimated_bit_rate = linear_estimate(seg_d["bit_rate"])
                duration = seg_d["duration"]
                total_duration += duration
                total_input_size += seg_d["size"]
                estimated_output_size += duration * estimated_bit_rate // 8
            sd["estimate"] = {
                "type": "linear",
                "size": int(estimated_output_size),
                "duration": total_duration,
                "bit_rate": 8 * estimated_output_size // total_duration,
                "ratio": round(estimated_output_size / total_input_size, 3),
            }

        with oldezpykit.stdlib.os.common.ctx_pushd(self.root):
            fstk.write_json_file(self.test_json, d, indent=4)
        return {k: v["estimate"]["ratio"] for k, v in d.items()}

    def clear(self):
        with oldezpykit.stdlib.os.common.ctx_pushd(self.root):
            segments = self.list_lock_segments() + self.list_done_segments()
            while segments:
                for i, seg in segments:
                    o_seg = os.path.join(self.output_prefix + i, seg)
                    if not os.path.isfile(o_seg):
                        continue
                    elif self.file_has_done(o_seg):
                        self.logger.info("delete done segment {}".format(o_seg))
                        os.remove(o_seg)
                        os.remove(o_seg + self.suffix_done)
                    elif self.file_has_lock(o_seg):
                        self.logger.info(
                            "request delete locked segment {}".format(o_seg)
                        )
                        oldezpykit.stdlib.os.common.touch(o_seg + self.suffix_delete)
                    else:
                        self.logger.info("delete stub segment{}".format(o_seg))
                        os.remove(o_seg)
                        if self.file_has_delete(o_seg):
                            os.remove(o_seg + self.suffix_delete)
                segments = self.list_lock_segments() + self.list_done_segments()

    def vf_res_scale_down(self, res_limit="FHD", vf=None, flags=None):
        width, height = self.width_height
        return get_vf_res_scale_down(
            width, height, res_limit=res_limit, vf=None, flags=flags
        )

    @property
    def width_height(self):
        seg0 = self.list_all_segments()[0]
        i, f = seg0
        seg0_d = self.input_data[S_SEGMENT][i][f]
        width = seg0_d["width"]
        height = seg0_d["height"]
        return width, height

    def excerpt_segments(self):
        try:
            d = {}
            segments = self.input_data[S_SEGMENT]
            for i in segments:
                mkv0_d = segments[i]["0.mkv"]
                d[i] = {}
                for k in ("codec_name", "pix_fmt", "width", "height"):
                    d[i][k] = mkv0_d[k]
            return d
        except KeyError:
            raise self.ContainerError("broken")

    def guess_crf(self, codec=None, res_limit=None):
        d = self.excerpt_segments()
        i, d = list(d.items())[0]
        config_funcs_d = {
            "h264": self.config_video,
            "hevc": self.config_hevc,
            "vp9": self.config_vp9,
        }
        codec = VIDEO_CODECS_A10N.get(codec, codec) or d["codec_name"]
        codec = {"vp8": "vp9"}.get(codec, codec)
        config_func = config_funcs_d[codec]
        crf0 = {"h264": 23, "hevc": 28, "vp9": 31}[codec]
        config_func(crf=crf0, res_limit=res_limit)
        e = self.estimate()
        r = e[i]
        return round(crf0 + 6 * log(r, 2), 1)
