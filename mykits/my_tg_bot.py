#!/usr/bin/env python3
from pprint import pformat

from telegram.ext import MessageHandler

from mylib.cli import new_argument_parser
from mylib.easy.logging import ez_get_logger
from mylib.easy.text import decode_fallback_locale
from mylib.ex.fstk import read_json_file, write_json_file
from mylib.ex.tricks import monitor_sub_process_tty_frozen, ProcessTTYFrozen
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


def line2args(line: str):
    args = shlex.split(line.strip())
    if args[0] in '+-*!':
        args.pop(0)
    return args


ytdl_regex_pattern = re.compile(r'youtube|youtu\.be|iwara|pornhub|\[ph[\da-f]{13}]|kissjav|xvideos')
bldl_regex_pattern = re.compile(r'(/|^)BV[\da-zA-Z]{10}|(/|^)av\d+\W|(/|^)ep\d+|(/|^)ss\d+')


class MyAssistantBot(EasyBot):
    def __init__(self, config_file: str, **kwargs):
        self._config_file = config_file
        config = read_json_file(config_file)
        persistence_file = os.path.splitext(config_file)[0] + '.dat'
        super().__init__(token=config['token'], whitelist=config.get('user_whitelist'),
                         persistence_filename=persistence_file, **kwargs)

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
        self.__typing__(update)
        uuid = mylib.sites.misc.free_ss_site_vmess_uuid()
        self.__send_text__(update, uuid)

    @deco_factory_bot_handler_method(MessageHandler, filters=Filters.regex(ytdl_regex_pattern))
    def _ytdl(self, update: Update, *args):
        with self.__ctx_save__(update):
            if not self.__predicate_update__(update):
                echo = f'# {update.message.text}'
                print(echo)
                self.__send_code_block__(update, echo)
                return
            chat_id = update.message.chat_id
            args_ll = [line2args(line) for line in update.message.text.splitlines()]
            for args_l in args_ll:
                call_tuple = (self._ytdl_succeed, chat_id, *args_l)
                if not self.__successful_internal_call__(*call_tuple):
                    self.__add_internal_call__(*call_tuple)

    def _ytdl_succeed(self, chat_id, *args):
        print('ytdl', args)
        args = [re.sub(r'\[(ph[\da-f]{13})]', r'https://www.pornhub.com/view_video.php?viewkey=\1', a) for a in args]
        print('ytdl', args)
        args_s = ' '.join([shlex.quote(a) for a in args])
        try:
            self.__send_code_block__(chat_id, f'+ {args_s}')
            p, out, err = ytdl_retry_frozen(*args)
            echo = ''.join(
                [re.sub(r'.*\[download\]', '[download]', decode_fallback_locale(b).rsplit('\r', maxsplit=1)[-1]) for
                 b in
                 out.readlines()[-10:]])
            if p.returncode:
                if self.__str_contain_abandon_errors__(echo):
                    self.__send_code_block__(chat_id, f'- {args_s}\n{echo}')
                    return BotInternalCallResult(ok=True)
                self.__send_code_block__(chat_id, f'! {args_s}\n{echo}')
                return BotInternalCallResult(ok=False)
            else:
                self.__send_code_block__(chat_id, f'* {args_s}\n{echo}')
            return BotInternalCallResult(ok=True)
        except Exception as e:
            print('ERROR')
            self.__send_code_block__(chat_id, f'! {args_s}\n{str(e)}\n{repr(e)}')
            self.__send_traceback__(chat_id)
            return BotInternalCallResult(ok=False)

    @deco_factory_bot_handler_method(MessageHandler, filters=Filters.regex(bldl_regex_pattern))
    def _bldl(self, update, *args):
        with self.__ctx_save__(update):
            chat_id = update.message.chat_id
            args_ll = [line2args(line) for line in update.message.text.splitlines()]
            for args_l in args_ll:
                call_tuple = (self._bldl_succeed, chat_id, *args_l)
                if not self.__successful_internal_call__(*call_tuple):
                    self.__add_internal_call__(*call_tuple)

    def _bldl_succeed(self, chat_id, *args):
        print('bldl', args)
        args_s = ' '.join([shlex.quote(a) for a in args])
        try:
            self.__send_code_block__(chat_id, f'+ {args_s}')
            p, out, err = bldl_retry_frozen(*args)
            if p.returncode:
                echo = ''.join(
                    [decode_fallback_locale(b).rsplit('\r', maxsplit=1)[-1] for b in out.readlines()[-5:]])
                if self.__str_contain_abandon_errors__(echo):
                    print(f' EXIT CODE: {p.returncode}')
                    self.__send_code_block__(chat_id, f'- {args_s}\n{echo}')
                    return BotInternalCallResult(ok=True)
                print(f' EXIT CODE: {p.returncode}')
                self.__send_code_block__(chat_id, f'! {args_s}\n{echo}')
                return BotInternalCallResult(ok=False)
            else:
                echo = ''.join([s for s in [decode_fallback_locale(b) for b in out.readlines()] if '─┤' not in s])
                self.__send_code_block__(chat_id, f'* {args_s}\n{echo}')
            return BotInternalCallResult(ok=True)
        except Exception as e:
            self.__send_code_block__(chat_id, f'! {args_s}\n{str(e)}\n{repr(e)}')
            return BotInternalCallResult(ok=False)

    @deco_factory_bot_handler_method(CommandHandler)
    def _secret(self, update: Update, *args):
        self.__typing__(update)
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

    def __predicate_update__(self, u: Update, c: CallbackContext = None):
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
