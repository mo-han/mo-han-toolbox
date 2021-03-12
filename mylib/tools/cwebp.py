#!/usr/bin/env python3
import dpath
from ..ez import *
from ..ez.argparse import ArgumentParserRigger, UnknownArguments

__dependencies__ = [i.__name__ for i in [dpath]]

apr = ArgumentParserRigger()
rename_ = apr.rename_factory_replace_underscore()
unknown_args = UnknownArguments()

an = AttrName()
an.update = an.user = ''


@apr.sub(rename_)
@apr.true(long_name=an.update)
@apr.true(long_name=an.user, default=True)
def install_dep():
    pip_install_dependencies(__dependencies__, update=apr.find(an.update), user=apr.find(an.user), options=apr.unknown)


if __name__ == '__main__':
    print(dpath.__name__)
    apr.prepare(skip_unknown=True)
    apr.run()
