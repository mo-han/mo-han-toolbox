#!/usr/bin/env python3
from mylib.easy import *
from tempfile import NamedTemporaryFile
from mylib.ex.PIL import *
import json
from filetype.filetype import guess_mime

PROP_EDIT_BASENAME = 'mkv' 'prop' 'edit'
MERGE_BASENAME = 'mkv' 'merge'
ACCEPTED_MIME_FOR_COVER_ART = ('image/jpeg', 'image/png')


def make_bad_mime_type(mime_type: str):
    return f'  {mime_type}  '


def recover_bad_mime_type(bad_mime_type: str):
    return bad_mime_type.strip()


def make_attachment_selector(uid=None, name=None, mime_type=None):
    if uid:
        return f':{uid}'
    if name:
        return f'name:{name}'
    if mime_type:
        return f'mime-type:{mime_type}'


class CLIArgs(CLIArgumentsList):
    merge_option_nargs = False


def run_cmd(cmd_l):
    p = subprocess.run(cmd_l, stdout=subprocess.PIPE)
    if p.returncode:
        raise ChildProcessError(cmd_l)
    return p.stdout.decode()


def get_info(filepath) -> dict:
    cmd = CLIArgs(MERGE_BASENAME, filepath, i=True, F='json')
    return json.loads(run_cmd(cmd))


def get_attachment_info(filepath) -> list:
    return get_info(filepath)['attachments']


def set_attachment(mkv_filepath, selector=None, attachment_filepath=None, *, name=None, mime_type=None, desc=None,
                   uid=None):
    cmd = CLIArgs(PROP_EDIT_BASENAME, mkv_filepath, attachment_name=name, attachment_mime_type=mime_type,
                  attachment_description=desc, attachment_uid=uid)
    if selector and attachment_filepath:
        cmd.add(replace_attachment=f'{selector}:{attachment_filepath}')
    elif selector:
        cmd.add(update_attachment=selector)
    elif attachment_filepath:
        cmd.add(add_attachment=attachment_filepath)
    else:
        raise ValueError('neither selector nor filepath given, nothing to do.')
    r = run_cmd(cmd)
    return r


def del_attachment(mkv_filepath, selector):
    cmd = CLIArgs(PROP_EDIT_BASENAME, mkv_filepath, delete_attachment=selector)
    return run_cmd(cmd)


def set_cover_art_image(mkv_filepath, image_source, *, name=None, desc=None):
    for mt in ACCEPTED_MIME_FOR_COVER_ART:
        try:
            set_attachment(mkv_filepath, make_attachment_selector(mime_type=mt), mime_type=make_bad_mime_type(mt))
        except ChildProcessError:
            pass
    if isinstance(image_source, Image.Image):
        with NamedTemporaryFile() as temp_file:
            image_source.save(temp_file.name, format=None if image_source.format in ('JPEG', 'PNG') else 'PNG')
            set_attachment(mkv_filepath, attachment_filepath=temp_file.name, name=name or 'cover', desc=desc)
    else:
        set_attachment(mkv_filepath, attachment_filepath=image_source, name=name, desc=desc,
                       mime_type=None if guess_mime(image_source) in ACCEPTED_MIME_FOR_COVER_ART else 'image/png')
