import os
# Maya 2017 switched to PySide2
try:
    from PySide import QtGui, QtCore
    QtWidgets = QtGui
except:
    from PySide2 import QtGui, QtCore, QtWidgets

