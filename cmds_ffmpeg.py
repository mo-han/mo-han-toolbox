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
        # c__v='hevc', crf=16,
        # x265_params='log-level=error:aq-mode=3',
        # x265_params='aq-mode=3',
        c__v='libx264', crf=16,
        x264opts='aq-mode=2',
# x264 有多种 aq-mode：
#
#     0: 禁用 AQ。
#     1: 方差自适应量化 (Variance AQ)。这是默认模式。它基于块的方差来分配码率，给低方差（更平坦）的块分配更多的码率，以减少条带效应 (banding)。
#     2: 自动方差自适应量化 (Auto-variance AQ)。在 aq-mode=1 的基础上，试图进一步防止在非常高细节的区域出现明显的质量下降。
#     3: 带偏置的自动方差自适应量化 (Auto-variance AQ with bias)。
#         这是 aq-mode=2 的一个增强版本。
#         它仍然会优先处理平坦区域以减少条带效应。
#         关键的“偏置”作用是： 它会略微增加对非常复杂、高纹理或高噪声区域的量化（即稍微降低这些区域的质量），因为人眼对这些区域的细节丢失不那么敏感。
#         这种模式旨在更好地处理那些本身就比较“脏”或“嘈杂”的视频源（例如电影胶片颗粒感很强），通过牺牲这些不易察觉的复杂区域的少量质量，来为更重要的平坦区域节省码率，从而实现更高效的整体压缩。
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
