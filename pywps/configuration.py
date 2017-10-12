##################################################################
# Copyright 2016 OSGeo Foundation,                               #
# represented by PyWPS Project Steering Committee,               #
# licensed under MIT, Please consult LICENSE.txt for details     #
##################################################################

"""
Reads the PyWPS configuration file
"""

import logging
import sys
import os
import tempfile
import pywps

from pywps._compat import PY2
if PY2:
    import ConfigParser
else:
    import configparser

__author__ = "Calin Ciociu"


CONFIG = None
LOGGER = logging.getLogger("PYWPS")


def get_config_value(section, option):
    """Get desired value from  configuration files

    :param section: section in configuration files
    :type section: string
    :param option: option in the section
    :type option: string
    :returns: value found in the configuration file
    """

    if not CONFIG:
        load_configuration()

    value = ''

    if CONFIG.has_section(section):
        if CONFIG.has_option(section, option):
            value = CONFIG.get(section, option)

            # Convert Boolean string to real Boolean values
            if value.lower() == "false":
                value = False
            elif value.lower() == "true":
                value = True

    return value


def load_configuration(cfgfiles=None):
    """Load PyWPS configuration from configuration files.
    The later configuration file in the array overwrites configuration
    from the first.

    :param cfgfiles: list of configuration files
    """

    global CONFIG

    LOGGER.info('loading configuration')
    if PY2:
        CONFIG = ConfigParser.SafeConfigParser()
    else:
        CONFIG = configparser.ConfigParser()

    LOGGER.debug('setting default values')
    CONFIG.add_section('server')
    CONFIG.set('server', 'encoding', 'utf-8')
    CONFIG.set('server', 'language', 'en-US')
    CONFIG.set('server', 'url', 'http://localhost/wps')
    CONFIG.set('server', 'maxprocesses', '30')
    CONFIG.set('server', 'maxsingleinputsize', '1mb')
    CONFIG.set('server', 'maxrequestsize', '3mb')
    CONFIG.set('server', 'temp_path', tempfile.gettempdir())
    CONFIG.set('server', 'processes_path', '')
    outputpath = tempfile.gettempdir()
    CONFIG.set('server', 'outputurl', 'file:///%s' % outputpath)
    CONFIG.set('server', 'outputpath', outputpath)
    CONFIG.set('server', 'workdir', tempfile.gettempdir())
    CONFIG.set('server', 'parallelprocesses', '2')

    CONFIG.add_section('logging')
    CONFIG.set('logging', 'file', '')
    CONFIG.set('logging', 'level', 'DEBUG')
    CONFIG.set('logging', 'database', 'sqlite:///:memory:')
    CONFIG.set('logging', 'prefix', 'pywps_')

    CONFIG.add_section('metadata:main')
    CONFIG.set('metadata:main', 'identification_title', 'PyWPS Processing Service')
    CONFIG.set('metadata:main', 'identification_abstract', 'PyWPS is an implementation of the Web Processing Service standard from the Open Geospatial Consortium. PyWPS is written in Python.')  # noqa
    CONFIG.set('metadata:main', 'identification_keywords', 'PyWPS,WPS,OGC,processing')
    CONFIG.set('metadata:main', 'identification_keywords_type', 'theme')
    CONFIG.set('metadata:main', 'identification_fees', 'NONE')
    CONFIG.set('metadata:main', 'identification_accessconstraints', 'NONE')
    CONFIG.set('metadata:main', 'provider_name', 'Organization Name')
    CONFIG.set('metadata:main', 'provider_url', 'http://pywps.org/')
    CONFIG.set('metadata:main', 'contact_name', 'Lastname, Firstname')
    CONFIG.set('metadata:main', 'contact_position', 'Position Title')
    CONFIG.set('metadata:main', 'contact_address', 'Mailing Address')
    CONFIG.set('metadata:main', 'contact_city', 'City')
    CONFIG.set('metadata:main', 'contact_stateorprovince', 'Administrative Area')
    CONFIG.set('metadata:main', 'contact_postalcode', 'Zip or Postal Code')
    CONFIG.set('metadata:main', 'contact_country', 'Country')
    CONFIG.set('metadata:main', 'contact_phone', '+xx-xxx-xxx-xxxx')
    CONFIG.set('metadata:main', 'contact_fax', '+xx-xxx-xxx-xxxx')
    CONFIG.set('metadata:main', 'contact_email', 'Email Address')
    CONFIG.set('metadata:main', 'contact_url', 'Contact URL')
    CONFIG.set('metadata:main', 'contact_hours', 'Hours of Service')
    CONFIG.set('metadata:main', 'contact_instructions', 'During hours of service.  Off on weekends.')
    CONFIG.set('metadata:main', 'contact_role', 'pointOfContact')

    CONFIG.add_section('grass')
    CONFIG.set('grass', 'gisbase', '')

    if not cfgfiles:
        cfgfiles = _get_default_config_files_location()

    if isinstance(cfgfiles, str):
        cfgfiles = [cfgfiles]

    loaded_files = CONFIG.read(cfgfiles)
    if loaded_files:
        LOGGER.info('Configuration file(s) %s loaded', loaded_files)
    else:
        LOGGER.info('No configuration files loaded. Using default values')

    cfgfile_folder_fullpath = os.path.dirname(os.path.realpath(cfgfiles[0]))
    outputs_folder_fullpath = os.path.join(cfgfile_folder_fullpath, "outputs")
    workdir_folder_fullpath = os.path.join(cfgfile_folder_fullpath, "workdir")
    log_file_fullpath = os.path.join(cfgfile_folder_fullpath, "pywps.log")
    CONFIG.set('server', 'outputpath', outputs_folder_fullpath)
    CONFIG.set('server', 'workdir', workdir_folder_fullpath)
    CONFIG.set('logging', 'file', log_file_fullpath)
    # _check_config()


def _check_config():
    """Check some configuration values
    """
    global CONFIG

    def checkdir(confid):

        confvalue = get_config_value('server', confid)

        if not os.path.isdir(confvalue):
            LOGGER.warning('server->%s configuration value %s is not directory'
                           % (confid, confvalue))

        if not os.path.isabs(confvalue):
            LOGGER.warning('server->%s configuration value %s is not absolute path, making it absolute to %s' %
                           (confid, confvalue, os.path.abspath(confvalue)))
            CONFIG.set('server', confid, os.path.abspath(confvalue))

    [checkdir(n) for n in ['workdir', 'outputpath']]


def _get_default_config_files_location():
    """Get the locations of the standard configuration files. These are
    Unix/Linux:
        1. `/etc/pywps.cfg`
        2. `$HOME/.pywps.cfg`
    Windows:
        1. `pywps\\etc\\default.cfg`

    Both:
        1. `$PYWPS_CFG environment variable`
    :returns: configuration files
    :rtype: list of strings
    """

    is_win32 = sys.platform == 'win32'
    if is_win32:
        LOGGER.debug('Windows based environment')
    else:
        LOGGER.debug('UNIX based environment')

    if os.getenv("PYWPS_CFG"):
        LOGGER.debug('using PYWPS_CFG environment variable')
        # Windows or Unix
        if is_win32:
            PYWPS_INSTALL_DIR = os.path.abspath(os.path.join(os.getcwd(), os.path.dirname(sys.argv[0])))
            cfgfiles = (os.getenv("PYWPS_CFG"))
        else:
            cfgfiles = (os.getenv("PYWPS_CFG"))

    else:
        LOGGER.debug('trying to estimate the default location')
        # Windows or Unix
        if is_win32:
            PYWPS_INSTALL_DIR = os.path.abspath(os.path.join(os.getcwd(), os.path.dirname(sys.argv[0])))
            cfgfiles = (os.path.join(PYWPS_INSTALL_DIR, "pywps", "etc", "pywps.cfg"))
        else:
            homePath = os.getenv("HOME")
            if homePath:
                cfgfiles = (os.path.join(pywps.__path__[0], "etc", "pywps.cfg"), "/etc/pywps.cfg",
                            os.path.join(os.getenv("HOME"), ".pywps.cfg"))
            else:
                cfgfiles = (os.path.join(pywps.__path__[0], "etc",
                            "pywps.cfg"), "/etc/pywps.cfg")

    return cfgfiles


def get_size_mb(mbsize):
    """Get real size of given obeject

    """

    size = mbsize.lower()

    import re

    units = re.compile("[gmkb].*")
    newsize = float(re.sub(units, '', size))

    if size.find("g") > -1:
        newsize *= 1024
    elif size.find("m") > -1:
        newsize *= 1
    elif size.find("k") > -1:
        newsize /= 1024
    else:
        newsize *= 1
    LOGGER.debug('Calculated real size of %s is %s', mbsize, newsize)
    return newsize
