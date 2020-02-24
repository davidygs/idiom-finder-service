import pkgutil

from sanic.log import logger

IDIOM_PACKAGE = 'idiomfinder.idiomchecker'
IDIOM_FILE = 'data/idioms.3w.txt'


class IdiomChecker:
    """
    IdiomChecker checks a given string to see if it is a Chinese idiom. It does so by searching
    against a list of known idioms.
    """

    def __init__(self):
        a = pkgutil.get_data(IDIOM_PACKAGE, IDIOM_FILE)
        self.all_idioms = set(a.decode('utf-8').strip().splitlines())
        logger.debug('Idioms loaded from {}/{}'.format(IDIOM_PACKAGE, IDIOM_FILE))

    def is_idiom(self, s):
        return s in self.all_idioms
