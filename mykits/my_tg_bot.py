#!/usr/bin/env python3
from pprint import pformat

from telegram.ext import MessageHandler

from mylib.cli import new_argument_parser
from mylib.easy.logging import ez_get_logger
from mylib.easy.text import decode_fallback_locale
from mylib.ext.fstk import read_json_file, write_json_file
from mylib.ext.tricks import monitor_sub_process_tty_frozen, ProcessTTYFrozen
from mylib.tg_bot import *

mt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(os.path.realpath(__file__))))


@deco_factory_retry(exceptions=ProcessTTYFrozen, max_retries=-1)
def bldl_retry_frozen(*args: str):
    p = subprocess.Popen(['bldl.sh.cmd', *args], stdout=subprocess.PIPE)
    return monitor_sub_process_tty_frozen(p, encoding='u8', timeout=60)


@deco_factory_retry(exceptions=ProcessTTYFrozen, max_retries=-1)
def ytdl_retry_frozen(*args: str):
    p = subprocess.Popen(['ytdl.sh.cmd', *args], stdout=subprocess.PIPE)
    return monitor_sub_process_tty_frozen(p, encoding='u8', timeout=60)


@deco_factory_retry(exceptions=ProcessTTYFrozen, max_retries=-1)
def yt_dlp_retry_frozen(*args: str):
    p = subprocess.Popen(['yt-dlp.sh.cmd', *args], stdout=subprocess.PIPE)
    return monitor_sub_process_tty_frozen(p, encoding='u8', timeout=60)


@deco_factory_retry(exceptions=ProcessTTYFrozen, max_retries=-1)
def phgif_retry_frozen(*args: str):
    p = subprocess.Popen(['you-get.pornhub.gif.py', *args], stdout=subprocess.PIPE)
    return monitor_sub_process_tty_frozen(p, encoding='u8', timeout=60)


def line2args(line: str) -> T.List[str]:
    args = shlex.split(line.strip())
    if args[0] in '+-*!':
        args.pop(0)
    return args


ytdl_regex_pattern = re.compile(r'youtube|youtu\.be|iwara|pornhub.com/view_video|ph[\da-f]{13}|kissjav|xvideos|spankbang|redgifs|xhamster')
bldl_regex_pattern = re.compile(r'(/|^)BV[\da-zA-Z]{10}|(/|^)av\d+|(/|^)ep\d+|(/|^)ss\d+|^https://b23.tv/.+')
phgif_regex_pattern = re.compile(r'pornhub.com/gif')


class MyAssistantBot(EasyBot):
    def __init__(self, config_file: str, **kwargs):
        self._config_file = config_file
        config = read_json_file(config_file)
        persistence_file = os.path.splitext(config_file)[0] + '.dat'
        super().__init__(token=config['token'], whitelist=config.get('user_whitelist'),
                         dat_fp=persistence_file, **kwargs)

    def __get_config__(self):
        return read_json_file(self._config_file)

    def __set_config__(self, **kwargs):
        conf = self.__get_config__()
        conf.update(kwargs)
        write_json_file(self._config_file, conf, indent=4)

    def __str_contain_abandon_errors__(self, s):
        abandon_errors = self.__get_config__().get('abandon_errors') or []
        return any(map(lambda x: x in s, abandon_errors))

    @deco_factory_bot_handler_method(CommandHandler, on_menu=True, command='freevmessuuid')
    def free_ss_site_vmess_uuid(self, update: Update, *args):
        import mylib.sites.misc
        self.__send_typing__(update)
        for uuid in mylib.sites.misc.free_ss_site_vmess_uuid():
            self.__send_text__(update, uuid)

    @deco_factory_bot_handler_method(MessageHandler, filters=Filters.regex(ytdl_regex_pattern))
    def _ytdl(self, update: Update, *args):
        with self.__ctx_save__():
            if not self.__check_update__(update):
                echo = f'# {update.message.text}'
                print(echo)
                self.__send_code_block__(update, echo)
                return
            chat_id = update.message.chat_id
            msg_lines = update.message.text.splitlines()
            args_ll = [line2args(line) for line in msg_lines]
            line0 = msg_lines[0].strip()
            if line0 in (f'@{h}p' for h in (360, 480, 720, 1080)):
                new_args_ll = []
                for args_l in args_ll[1:]:
                    new_args_ll.append(args_l + ['-S', f'res:{line0[1:-1]}'])
                    # if 'pornhub.com' in args_l[0]:
                    #     new_args_ll.append(
                    #         args_l + ['-f', f'[format_id!*=hls][height<=?{line0[1:-1]}]/[height<=?{line0[1:-1]}]'])
                    # else:
                    #     new_args_ll.append(args_l + ['-f', f'[height<=?{line0[1:-1]}]'])
                args_ll = new_args_ll
            tasks = [EasyBotTaskData(target=self._ytdl_internal.__name__, args=args_l, chat_to=chat_id)
                     for args_l in args_ll]
            self.__save_tasks__(tasks, chat_id)

    def _ytdl_internal(self, call_data: EasyBotTaskData):
        args = call_data.args
        chat_to = call_data.chat_to
        args = [re.sub(r'(^ph[\da-f]{13})', r'https://www.pornhub.com/view_video.php?viewkey=\1', a) for a in args]
        args_s = ' '.join([shlex.quote(a) for a in args])
        retry_frozen = yt_dlp_retry_frozen
        # retry_frozen = ytdl_retry_frozen
        # if any(map(lambda s: s in args[0], ('youtu.be', 'youtube.com', 'redgifs.com', 'xvideos.com', 'pornhub.com'))):
        #     retry_frozen = yt_dlp_retry_frozen
        try:
            p, out, err = retry_frozen(*args)
            echo = ''.join(
                [re.sub(r'.*\[download\]', '[download]', decode_fallback_locale(b).rsplit('\r', maxsplit=1)[-1]) for
                 b in
                 out.readlines()[-16:]])
            if p.returncode:
                if self.__str_contain_abandon_errors__(echo):
                    self.__send_code_block__(chat_to, f'- {args_s}\n{echo}')
                    return EasyBotTaskResult(ok=True)
                self.__send_code_block__(chat_to, f'! {args_s}\n{p.returncode}\n{echo}')
                return EasyBotTaskResult(ok=False)
            else:
                self.__send_code_block__(chat_to, f'* {args_s}\n{echo}')
            return EasyBotTaskResult(ok=True)
        except Exception as e:
            print('ERROR')
            self.__send_code_block__(chat_to, f'! {args_s}\n{str(e)}\n{repr(e)}')
            self.__send_traceback__(chat_to)
            return EasyBotTaskResult(ok=False)

    @deco_factory_bot_handler_method(MessageHandler, filters=Filters.regex(bldl_regex_pattern))
    def _bldl(self, update, *args):
        with self.__ctx_save__():
            chat_id = update.message.chat_id
            args_ll = [line2args(line) for line in update.message.text.splitlines()]
            tasks = [EasyBotTaskData(target=self._bldl_internal.__name__, args=args_l, chat_to=chat_id)
                     for args_l in args_ll]
            self.__save_tasks__(tasks, chat_id)

    def _bldl_internal(self, call_data: EasyBotTaskData):
        args = call_data.args
        arg0 = args[0].strip()
        if not (arg0.startswith('https://') or arg0.startswith('-')):
            args[0] = f'https://b23.tv/{arg0}'
        chat_id = call_data.chat_to
        args_s = ' '.join([shlex.quote(a) for a in args])
        try:
            p, out, err = bldl_retry_frozen(*args)
            if p.returncode:
                echo = ''.join(
                    [decode_fallback_locale(b).rsplit('\r', maxsplit=1)[-1] for b in out.readlines()[-5:]])
                if self.__str_contain_abandon_errors__(echo):
                    print(f' EXIT CODE: {p.returncode}')
                    self.__send_code_block__(chat_id, f'- {args_s}\n{echo}')
                    return EasyBotTaskResult(ok=True)
                print(f' EXIT CODE: {p.returncode}')
                self.__send_code_block__(chat_id, f'! {args_s}\n{echo}')
                if 'urllib.error.HTTPError: HTTP Error 412: Precondition Failed' in echo:
                    ts = 60
                    self.__send_code_block__(chat_id, f'# sleep {ts}s.')
                    print(f'# sleep {ts}s.')
                    sleep(ts)
                return EasyBotTaskResult(ok=False)
            else:
                echo = ''.join([s for s in [decode_fallback_locale(b) for b in out.readlines()] if '─┤' not in s])
                self.__send_code_block__(chat_id, f'* {args_s}\n{echo}')
            return EasyBotTaskResult(ok=True)
        except Exception as e:
            self.__send_code_block__(chat_id, f'! {args_s}\n{str(e)}\n{repr(e)}')
            return EasyBotTaskResult(ok=False)

    @deco_factory_bot_handler_method(MessageHandler, filters=Filters.regex(phgif_regex_pattern))
    def _phgif(self, update, *args):
        with self.__ctx_save__():
            chat_id = update.message.chat_id
            args_ll = [line2args(line) for line in update.message.text.splitlines()]
            tasks = [EasyBotTaskData(target=self._phgif_internal.__name__, args=args_l, chat_to=chat_id)
                     for args_l in args_ll]
            self.__save_tasks__(tasks, chat_id)

    def _phgif_internal(self, call_data: EasyBotTaskData):
        args = call_data.args
        chat_id = call_data.chat_to
        args_s = ' '.join([shlex.quote(a) for a in args])
        try:
            p, out, err = phgif_retry_frozen(*args)
            if p.returncode:
                echo = ''.join(
                    [decode_fallback_locale(b).rsplit('\r', maxsplit=1)[-1] for b in out.readlines()[-5:]])
                if self.__str_contain_abandon_errors__(echo):
                    print(f' EXIT CODE: {p.returncode}')
                    self.__send_code_block__(chat_id, f'- {args_s}\n{echo}')
                    return EasyBotTaskResult(ok=True)
                print(f' EXIT CODE: {p.returncode}')
                self.__send_code_block__(chat_id, f'! {args_s}\n{echo}')
                return EasyBotTaskResult(ok=False)
            else:
                echo = ''.join([s for s in [decode_fallback_locale(b) for b in out.readlines()] if '─┤' not in s])
                self.__send_code_block__(chat_id, f'* {args_s}\n{echo}')
            return EasyBotTaskResult(ok=True)
        except Exception as e:
            self.__send_code_block__(chat_id, f'! {args_s}\n{str(e)}\n{repr(e)}')
            return EasyBotTaskResult(ok=False)

    @deco_factory_bot_handler_method(CommandHandler)
    def _secret(self, update: Update, *args):
        self.__send_typing__(update)
        for name in ('effective_message', 'effective_user'):
            self.__send_code_block__(update, f'{name}\n{pformat(getattr(update, name).to_dict())}')
        self.__send_code_block__(update, f'bot.get_me()\n{pformat(self.__bot__.get_me().to_dict())}')

    @deco_factory_bot_handler_method(CommandHandler, on_menu=True, pass_args=True)
    def sleep(self, u: Update, c: CallbackContext):
        """sleep some time (unit: sec)"""
        args = c.args or [0]
        t = float(args[0])
        self.__send_text__(u, f'sleep {t} seconds')
        time.sleep(t)
        self.__send_text__(u, 'awake...')

    @deco_factory_bot_handler_method(CommandHandler, on_menu=True, pass_args=True)
    def errors(self, u: Update, c: CallbackContext):
        """manage subprocess errors"""
        args = c.args
        if not args:
            usage_s = '/errors {+,-,:} [T]'
            self.__send_code_block__(u, usage_s)
            return
        arg0, arg1 = args[0], ' '.join(args[1:])
        errors = self.__get_config__().get('abandon_errors', [])
        if arg0 == ':':
            self.__send_code_block__(u, pformat(errors))
        elif arg0 == '+':
            errors = sorted(set(errors) | {arg1})
            self.__set_config__(abandon_errors=errors)
            self.__send_code_block__(u, pformat(errors))
        elif arg0 == '-':
            errors = sorted(set(errors) - {arg1})
            self.__set_config__(abandon_errors=errors)
            self.__send_code_block__(u, pformat(errors))
        else:
            self.__send_code_block__(u, pformat(errors))

    def __check_update__(self, u: Update, c: CallbackContext = None):
        anti_updates = set(self.__get_config__().get('anti_updates', []))
        for x in anti_updates:
            if x in u.message.text:
                anti_updates.remove(x)
                self.__set_config__(anti_updates=list(anti_updates))
                return False
        else:
            return True


def main():
    ap = new_argument_parser()
    ap.add_argument('-c', '--config-file', metavar='path', required=True)
    ap.add_argument('-v', '--verbose', action='store_true')
    ap.add_argument('-T', '--timeout', type=float)
    parsed_args = ap.parse_args()
    config_file = parsed_args.config_file
    timeout = parsed_args.timeout

    if parsed_args.verbose:
        log_lvl = 'DEBUG'
        print(parsed_args)
    else:
        log_lvl = 'INFO'
    ez_get_logger('telegram').setLevel(log_lvl)
    bot = MyAssistantBot(config_file, timeout=timeout, auto_run=False, debug_mode=parsed_args.verbose)
    bot.__run__()


if __name__ == '__main__':
    # ensure_sigint_signal()
    main()
