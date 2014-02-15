from distutils.core import setup
import py2exe
import warnings
warnings.simplefilter('ignore')

setup(
    windows=['Main.py'],
    options={"py2exe": {
    "includes": ["sip", "PyQt4.QtGui", "PyQt4.QtCore", "bs4.builder._html5lib", "bs4.builder._htmlparser", "bs4.*", 'sqlite3.*', 'codecs', 'cStringIO']}},
    name='Saraiva',
    version='1.0',
    packages=['spiders', 'logs', 'utils', 'works', 'views', 'db'],
    url='',
    license='',
    author='Rabbi',
    author_email='',
    description=''
)
