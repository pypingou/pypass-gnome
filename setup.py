#!/usr/bin/python

# test via:
# python setup.py install --root /tmp/pypass && tree /tmp/pypass/
# rm -rf build/ PyPass.egg-info /tmp/pypass/ && python setup.py \
# install --root /tmp/pypass && tree /tmp/pypass/


from distutils.core import setup
from setuptools import find_packages
import os, sys
from src import __version__, __author__, __url__, __license__
from src import __description__, __mail__

name = 'PyPass'

locales = []
if os.path.exists('pypass/locale'):
    for lang in os.listdir('pypass/locale'):
        locales.append(os.path.join(lang, 'LC_MESSAGES'))

if sys.platform == 'win32':
    # Something might come here one day.
    pass
else:
    print find_packages('.')
    setup(
        name = name,
        version = __version__,
        license = __license__,
        description = __description__,
        long_description = 'PyPass helps you to manage all your ' \
        'accounts in an easy and secure with GPG.',
        platforms = ['Linux'],
        author = __author__,
        author_email = __mail__,
        url = __url__,
        packages = ['pypass.gtk'],
        package_dir={'pypass.gtk': 'src'},
        #package_data = {'pypass' : ['data/pypass.ini', 
                                #'gtk/ui/*'] },
        scripts = ["pypass-gnome"],
        data_files = [("/usr/share/applications/",["PyPass.desktop"]), 
                      ('/usr/share/icons/',["src/data/PyPass.png"]),
                      #TODO: fix language stuff
                    ]# + [(os.path.join(LOCALE_DIR, locale),
                       #     [os.path.join('pypass', 'locale', locale,
                       #      'pypass.mo')])
                       #     for locale in locales]
        )
