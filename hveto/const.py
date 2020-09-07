import os
from gwpy.time import from_gps


def get_hvetopath(gpstime):

    """ Returns the path of hveto output files

    Given a gpstime, the path of the folder
    containing hveto trigger files is returned

    Parameters
    ----------
    gpstime : `str` or `float`
    start time of the day for this analysis

    Returns
    _______
    path : `str`

    Example
    _______

    >>> from hveto.const import get_hvetopath
    >>> get_hvetopath(1257811218)
    '/home/detchar/public_html/hveto/day/20191115/latest'
    """

    date = from_gps(gpstime).strftime('%Y%m%d')
    hveto_dir = '/home/detchar/public_html/hveto/day/'
    path = os.path.join(hveto_dir, date, 'latest')

    return path
