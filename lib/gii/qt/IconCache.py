import os.path

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QEventLoop, QEvent, QObject

import logging
from gii.core import app

_iconCache = {}

def getIcon(name, fallback=None):
	global _iconCache
	if not name: return QtGui.QIcon()

	icon = _iconCache.get(name,None)
	if icon: return icon
	iconFile = None
	path = app.findDataFile( 'icons/%s.png' % name )
	if not path:
		if fallback:
			return getIcon(fallback)
		logging.error('icon not found: %s' % name)
		return QtGui.QIcon()

	icon = QtGui.QIcon(QtGui.QPixmap(path))
	_iconCache[name]=icon
	return icon
