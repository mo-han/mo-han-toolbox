#!/usr/bin/env python3
from mylib.ffmpeg_alpha import FFmpegArgsList
from oldezpykitext.appkit import *
from mylib import ffmpeg_alpha

__logger__ = logging.get_logger(__name__)
ap = argparse.ArgumentParserWrapper()


@ap.sub()
@ap.map()
def test():
    print(ap.extra)


@ap.sub()
def concat_seg_in_folder():
    for dp in os.clpb.get_path():
        if not os.path_isdir(dp):
            return
        seg_l = [os.join_path(dp, f) for f in sorted(os.listdir(dp))]
        if not seg_l:
            return
        seg_ext = '.mkv'
        dst = f'{dp} +{{seg}}{seg_ext}'
        ff = ffmpeg_alpha.FFmpegRunnerAlpha()
        ff.concat(seg_l, dst, output_args=ap.extra)


@ap.sub()
@ap.arg('frame_size_and_rate', help='{width}x{height}@{fps}')
@ap.map('frame_size_and_rate')
def concat_frame_in_folder(frame_size_and_rate):
    w, h, r = re.search(r'(\d+)x(\d+)@(\d+)', frame_size_and_rate).groups()
    a = FFmpegArgsList(
        vf=f'scale={w}:{h}:force_original_aspect_ratio=1,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2',
        c__v='hevc', crf=22, pix_fmt='yuv420p',
        # x265_params='log-level=error:aq-mode=3',
        x265_params='aq-mode=3',
        x264opts='aq-mode=3',
    )
    for dp in os.clpb.get_path():
        if not os.path_isdir(dp):
            return
        seg_l = [os.join_path(dp, f) for f in sorted(os.listdir(dp))]
        if not seg_l:
            return
        seg_ext = '.mkv'
        dst = f'{dp}{seg_ext}'
        ff = ffmpeg_alpha.FFmpegRunnerAlpha()
        ff.concat(
            seg_l, dst,
            input_args=['-r', str(r)],
            output_args=a + ap.extra,
        )


def main():
    logging.init_root(fmt=logging.FMT_MESSAGE_ONLY)
    logging.set_root_level('INFO')
    # logging.set_root_level('DEBUG')
    ap.parse(catch_unknown_args=True)
    ap.run()


if __name__ == '__main__':
    main()
