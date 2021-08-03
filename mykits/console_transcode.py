#!/usr/bin/env python3
import codecs

from mylib.ex.console_app import *

apr = ArgumentParserRigger()


@apr.root()
@apr.arg('inner_encoding')
@apr.arg('outer_encoding')
@apr.map(inner_encoding='inner_encoding', outer_encoding='outer_encoding', args=apr.unknown_placeholder)
def stdout_stderr_transcode(inner_encoding, outer_encoding, args):
    def read_1byte_from_pipe(pipe):
        def read_1byte():
            return pipe.read(1)

        return read_1byte

    def transcode_pipe(from_pipe, from_encoding, to_pipe, to_encoding):
        from_decoder = codecs.getincrementaldecoder(from_encoding)(errors='surrogateescape')
        to_encoder = codecs.getincrementaldecoder(to_encoding)(errors='surrogateescape')
        for data in iter(read_1byte_from_pipe(from_pipe), b''):
            if not data:
                break
            s = from_decoder.decode(data)
            if s:
                from_decoder.reset()
                to_pipe.write(s.encode(to_encoding, errors='surrogateescape'))
                to_pipe.flush()

    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    thread_factory(name='out')(transcode_pipe, p.stdout, inner_encoding, sys.stdout.buffer, outer_encoding).start()
    thread_factory(name='err')(transcode_pipe, p.stderr, inner_encoding, sys.stderr.buffer, outer_encoding).start()
    thread_factory(name='in')(transcode_pipe, sys.stdin.buffer, outer_encoding, p.stdin, inner_encoding).start()
    p.wait()


def main():
    apr.parse(catch_unknown_args=True)
    apr.run()


if __name__ == '__main__':
    main()
