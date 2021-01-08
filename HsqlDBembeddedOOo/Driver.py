#!
# -*- coding: utf_8 -*-

"""
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020 https://prrvchr.github.io                                     ║
║                                                                                    ║
║   Permission is hereby granted, free of charge, to any person obtaining            ║
║   a copy of this software and associated documentation files (the "Software"),     ║
║   to deal in the Software without restriction, including without limitation        ║
║   the rights to use, copy, modify, merge, publish, distribute, sublicense,         ║
║   and/or sell copies of the Software, and to permit persons to whom the Software   ║
║   is furnished to do so, subject to the following conditions:                      ║
║                                                                                    ║
║   The above copyright notice and this permission notice shall be included in       ║
║   all copies or substantial portions of the Software.                              ║
║                                                                                    ║
║   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,                  ║
║   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES                  ║
║   OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.        ║
║   IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY             ║
║   CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,             ║
║   TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE       ║
║   OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.                                    ║
║                                                                                    ║
╚════════════════════════════════════════════════════════════════════════════════════╝
"""

import uno
import unohelper

from com.sun.star.lang import XServiceInfo
from com.sun.star.sdbc import XDriver
from com.sun.star.sdbcx import XDataDefinitionSupplier
from com.sun.star.sdbcx import XCreateCatalog
from com.sun.star.sdbcx import XDropCatalog

from com.sun.star.sdbc import SQLException

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.uno import Exception as UnoException

from unolib import getResourceLocation
from unolib import createService
from unolib import getSimpleFile
from unolib import getUrl

from hsqldbembedded import Connection
from hsqldbembedded import getDataBaseInfo
from hsqldbembedded import g_identifier
from hsqldbembedded import g_protocol
from hsqldbembedded import g_path
from hsqldbembedded import g_jar
from hsqldbembedded import g_class
from hsqldbembedded import g_options
from hsqldbembedded import g_shutdown

from hsqldbembedded import logMessage
from hsqldbembedded import getMessage
g_message = 'Driver'

import traceback

# pythonloader looks for a static g_ImplementationHelper variable
g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationName = '%s.Driver' % g_identifier


class Driver(unohelper.Base,
             XServiceInfo,
             XDataDefinitionSupplier,
             XCreateCatalog,
             XDropCatalog,
             XDriver):

    def __init__(self, ctx):
        self.ctx = ctx
        self._supportedProtocol = 'sdbc:embedded:hsqldb'
        self._dbdir = 'database/'
        self._dbfiles = ('script', 'properties', 'data', 'backup', 'log')
        self._user = 'SA'
        self._password = ''
        msg = getMessage(self.ctx, g_message, 101)
        logMessage(self.ctx, INFO, msg, 'Driver', '__init__()')

    # XDriver
    def connect(self, url, infos):
        try:
            location = self._getUrl(infos)
            if location is None:
                code = getMessage(self.ctx, g_message, 111)
                msg = getMessage(self.ctx, g_message, 112, (url, self._getInfo(infos)))
                raise self._getException(code, 1001, msg, self)
            msg = getMessage(self.ctx, g_message, 113, location.Main)
            logMessage(self.ctx, INFO, msg, 'Driver', 'connect()')
            name = self._getDataSourceName(location)
            sf = getSimpleFile(self.ctx)
            split = '%s%s' % (location.Path, name)
            if not sf.isFolder(split):
                if sf.exists(split):
                    code = getMessage(self.ctx, g_message, 114)
                    msg = getMessage(self.ctx, g_message, 115, (name, location.Path))
                    raise self._getException(code, 1002, msg, self)
                self._splitDataBase(sf, location, name)
            datasource = self._getDataSource(location, name)
            connection = Connection(self.ctx, datasource, url, self._user, self._password)
            version = connection.getMetaData().getDriverVersion()
            msg = getMessage(self.ctx, g_message, 116, (version, self._user))
            logMessage(self.ctx, INFO, msg, 'Driver', 'connect()')
            return connection
        except SQLException as e:
            raise e
        except Exception as e:
            msg = getMessage(self.ctx, g_message, 117, (e, traceback.print_exc()))
            logMessage(self.ctx, SEVERE, msg, 'Driver', 'connect()')

    def acceptsURL(self, url):
        accept = url.startswith(self._supportedProtocol)
        msg = getMessage(self.ctx, g_message, 121, (url, accept))
        logMessage(self.ctx, INFO, msg, 'Driver', 'acceptsURL()')
        return accept

    def getPropertyInfo(self, url, infos):
        try:
            msg = getMessage(self.ctx, g_message, 131, url)
            logMessage(self.ctx, INFO, msg, 'Driver', 'getPropertyInfo()')
            for info in infos:
                msg = getMessage(self.ctx, g_message, 132, (info.Name, info.Value))
                logMessage(self.ctx, INFO, msg, 'Driver', 'getPropertyInfo()')
            drvinfo = []
            dbinfo = getDataBaseInfo()
            for info in dbinfo:
                drvinfo.append(self._getDriverPropertyInfo(info, dbinfo[info]))
            for info in infos:
                if info.Name not in dbinfo:
                    drvinfo.append(self._getDriverPropertyInfo(info.Name, info.Value))
            for info in drvinfo:
                msg = getMessage(self.ctx, g_message, 133, (info.Name, info.Value))
                logMessage(self.ctx, INFO, msg, 'Driver', 'getPropertyInfo()')
            return tuple(drvinfo)
        except Exception as e:
            msg = getMessage(self.ctx, g_message, 134, (e, traceback.print_exc()))
            logMessage(self.ctx, SEVERE, msg, 'Driver', 'getPropertyInfo()')

    def getMajorVersion(self):
        return 1
    def getMinorVersion(self):
        return 0

    # XDataDefinitionSupplier
    def getDataDefinitionByConnection(self, connection):
        msg = getMessage(self.ctx, g_message, 141)
        logMessage(self.ctx, INFO, msg, 'Driver', 'getDataDefinitionByConnection()')
        return connection
    def getDataDefinitionByURL(self, url, infos):
        msg = getMessage(self.ctx, g_message, 151, url)
        logMessage(self.ctx, INFO, msg, 'Driver', 'getDataDefinitionByURL()')
        connection = self.connect(url, infos)
        return self.getDataDefinitionByConnection(connection)

    # XCreateCatalog
    def createCatalog(self, info):
        msg = getMessage(self.ctx, g_message, 161)
        logMessage(self.ctx, INFO, msg, 'Driver', 'createCatalog()')

    # XDropCatalog
    def dropCatalog(self, name, info):
        msg = getMessage(self.ctx, g_message, 171, name)
        logMessage(self.ctx, INFO, msg, 'Driver', 'dropCatalog()')

    def _splitDataBase(self, sf, location, dbname):
        service = 'com.sun.star.packages.zip.ZipFileAccess'
        args = (location.Main, )
        zip = createService(self.ctx, service, *args)
        for name in self._dbfiles:
            path = '%s%s' % (self._dbdir, name)
            if zip.hasByName(path):
                url = self._getDataBaseUrl(location, dbname, name)
                if not sf.exists(url):
                    input = zip.getStreamByPattern(path)
                    sf.writeFile(url, input)
                    input.closeInput()

    def _getDataBaseUrl(self, location, dbname, name):
        return '%s%s/%s.%s' % (location.Path, dbname, dbname, name)

    def _getInfo(self, infos):
        url = ''
        for info in infos:
            if info.Name == 'URL':
                url = info.Value.strip()
                break
        return url

    def _getUrl(self, infos):
        url = self._getInfo(infos)
        return getUrl(self.ctx, url)

    def _getException(self, state, code, message, context=None, exception=None):
        error = SQLException()
        error.SQLState = state
        error.ErrorCode = code
        error.NextException = exception
        error.Message = message
        error.Context = context
        return error

    def _getDriverPropertyInfo(self, name, value):
        info = uno.createUnoStruct('com.sun.star.sdbc.DriverPropertyInfo')
        info.Name = name
        required = value is not None and not isinstance(value, tuple)
        info.IsRequired = required
        if required:
            info.Value = value
        info.Choices = ()
        return info

    def _getDataSource(self, url, name):
        service = 'com.sun.star.sdb.DatabaseContext'
        datasource = createService(self.ctx, service).createInstance()
        self._setDataSource(datasource, url, name)
        return datasource

    def _setDataSource(self, datasource, url, name):
        datasource.URL = self._getDataSourceUrl(url, name)
        datasource.Settings.JavaDriverClass = g_class
        datasource.Settings.JavaDriverClassPath = self._getDataSourceClassPath()

    def _getDataSourceName(self, url):
        name, sep, extension = url.Name.rpartition('.')
        return name

    def _getDataSourceUrl(self, url, name):
        format = (g_protocol, url.Protocol, url.Path, name, name, g_options, g_shutdown)
        location = '%s%s%s%s/%s%s%s' % format
        return location

    def _getDataSourceClassPath(self):
        path = getResourceLocation(self.ctx, g_identifier, g_path)
        return '%s/%s' % (path, g_jar)

    # XServiceInfo
    def supportsService(self, service):
        return g_ImplementationHelper.supportsService(g_ImplementationName, service)
    def getImplementationName(self):
        return g_ImplementationName
    def getSupportedServiceNames(self):
        return g_ImplementationHelper.getSupportedServiceNames(g_ImplementationName)


g_ImplementationHelper.addImplementation(Driver,
                                         g_ImplementationName,
                                        (g_ImplementationName,
                                        'com.sun.star.sdbc.Driver',
                                        'com.sun.star.sdbcx.Driver'))
