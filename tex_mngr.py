"""
ToDo:
Right click for actions as a context view.

1. Open in os.                                  Done: Tested on Windows only
2. Select in outliner.                          Done: Auto behaviour
3. Search and replace
    - Default search is common denominator
    - Offer a filesystem search
4. Rename node
    - From text input
    - Auto from filename
5. Copy textures
6. Move textures
7. Create .tx if possible
8. Convert from a texture nodeType to another.
"""

import sys
import os
# Maya 2017 switched to PySide2
try:
    from PySide import QtGui, QtCore
    QtWidgets = QtGui
except:
    from PySide2 import QtGui, QtCore, QtWidgets
from maya import OpenMayaUI as omui
try:
    from shiboken import wrapInstance
except:
    from shiboken2 import wrapInstance
import pymel.core as pm


TEXTURE_NODES = {
    'file': 'fileTextureName',
    'aiImage': 'filename',
}


def maya_main_window():
    maya_main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(maya_main_window_ptr), QtWidgets.QWidget)


def list_texture_nodes():
    tex = pm.ls(long=True, textures=True)
    filtered_tex = [f for f in tex if pm.nodeType(f) in
                    TEXTURE_NODES.keys()]
    return filtered_tex


def select_texture_nodes(nodes):
    return pm.select(nodes)


def has_tx(file_path):
    root, ext = os.path.splitext(file_path)
    tx = '.'.join([root, 'tx'])
    return os.path.exists(tx)


def node_from_index(model_index):
    return pm.PyNode(model_index.data(QtCore.Qt.ItemDataRole.UserRole))


def file_path_from_node(node):
    return node.getAttr(TEXTURE_NODES[node.nodeType()])


def open_in_os(file_path):
    if file_path and os.path.exists(file_path):
        # Dir
        norm_file_path = os.path.abspath(file_path)
        file_dir, name = os.path.split(norm_file_path)
        # URI
        file_dir_URI = 'file:///{0}'.format(file_dir)
        open_succes = QtGui.QDesktopServices.openUrl(file_dir_URI)

        if not open_succes:
            print('Open in OS: Could not open:       {0}'.format(file_dir_URI))
        else:
            print('Open in OS: Directory opened:     {0}'.format(file_dir))
    else:
        print('Open in OS: File does not exists: {0}'.format(file_path))
        return False


def QHVBox(parent):
    h = QtWidgets.QHBoxLayout()
    v = QtWidgets.QVBoxLayout()
    parent.addLayout(h)
    h.addLayout(v)
    return v


class TexManager(QtWidgets.QDialog):
    def __init__(self, parent=maya_main_window()):
        super(self.__class__, self).__init__(parent)

        # Window
        self.setWindowTitle('Texture Manager')
        self.setMinimumSize(800, 400)
        self.resize(1000, 600)
        self.setWindowFlags(QtCore.Qt.Window)
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)

        # Table
        lay_table = QtWidgets.QHBoxLayout()
        self.table = QtWidgets.QTableWidget()
        self.table.clicked.connect(self.select_texture_nodes)
        self.table.doubleClicked.connect(self.open_in_os)
        self.table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        lay_table.addWidget(self.table)
        layout.addLayout(lay_table)

        # Search and Replace
        lay_snr_combo = QtWidgets.QHBoxLayout()
        layout.addLayout(lay_snr_combo)
        lay_replace_lines = QHVBox(lay_snr_combo)
        # Search
        lay_search_line = QtWidgets.QHBoxLayout()
        label_search = QtWidgets.QLabel('Search:')
        label_search.setFixedWidth(46)
        lay_search_line.addWidget(label_search)
        self.line_search = QtWidgets.QLineEdit()
        lay_search_line.addWidget(self.line_search)
        lay_replace_lines.addLayout(lay_search_line)
        # Replace
        lay_replace_line = QtWidgets.QHBoxLayout()
        label_replace = QtWidgets.QLabel('Replace:')
        label_replace.setFixedWidth(46)
        lay_replace_line.addWidget(label_replace)
        self.line_replace = QtWidgets.QLineEdit()
        lay_replace_line.addWidget(self.line_replace)
        lay_replace_lines.addLayout(lay_replace_line)

        btn_replace = QtWidgets.QPushButton('Replace')
        btn_replace.setFixedWidth(100)
        btn_replace.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                  QtWidgets.QSizePolicy.Minimum)
        self.table.itemSelectionChanged.connect(self.select_texture_nodes)
        lay_snr_combo.addWidget(btn_replace)

        self.setLayout(layout)

        self.init_table()
        self.fill_table()

    def init_table(self):
        # Header
        header_titles = ['Type', 'Name', 'Tx', 'Exists', 'File Path']
        self.table.setColumnCount(len(header_titles))
        self.table.setHorizontalHeaderLabels(header_titles)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSortIndicatorShown(True)

        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)

        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setStyleSheet('QTableView::item{padding-right: 16px}')

    def open_in_os(self, model_index):
        node = node_from_index(model_index)
        file_path = file_path_from_node(node)
        open_in_os(file_path)

    def select_texture_nodes(self):
        model_indexes = self.table.selectedIndexes()
        selected_nodes = []
        if model_indexes:
            file_path_idx = 4
            for i in model_indexes:
                if i.column() == file_path_idx:
                    selected_nodes.append(node_from_index(i))
        select_texture_nodes(selected_nodes)

    def fill_table(self):
        texture_nodes = list_texture_nodes()
        if texture_nodes:
            self.table.setSortingEnabled(False)

            row_count = len(texture_nodes)
            column_count = self.table.columnCount()
            self.table.setRowCount(row_count)

            for row, node in enumerate(texture_nodes):
                file_path = node.getAttr(TEXTURE_NODES[node.nodeType()])

                # type
                item_type = QtWidgets.QTableWidgetItem()
                item_type.setData(QtCore.Qt.ItemDataRole.UserRole, node.name())
                item_type.setData(QtCore.Qt.ItemDataRole.DisplayRole,
                                  node.nodeType())
                self.table.setItem(row, 0, item_type)

                # name
                item_name = QtWidgets.QTableWidgetItem()
                item_name.setData(QtCore.Qt.ItemDataRole.UserRole, node.name())
                item_name.setData(QtCore.Qt.ItemDataRole.DisplayRole,
                                  node.name())
                self.table.setItem(row, 1, item_name)

                # tx
                item_tx = QtWidgets.QTableWidgetItem()
                tx = 'TX' if has_tx(file_path) else ''
                item_tx.setData(QtCore.Qt.ItemDataRole.UserRole, node.name())
                item_tx.setData(QtCore.Qt.ItemDataRole.DisplayRole,
                                tx)
                self.table.setItem(row, 2, item_tx)

                # exists
                item_exist = QtWidgets.QTableWidgetItem()
                exists = 'exists' if os.path.exists(file_path) else ''
                item_exist.setData(QtCore.Qt.ItemDataRole.UserRole,
                                   node.name())
                item_exist.setData(QtCore.Qt.ItemDataRole.DisplayRole,
                                   exists)
                self.table.setItem(row, 3, item_exist)

                # file_path
                item_filename = QtWidgets.QTableWidgetItem()

                item_filename.setData(QtCore.Qt.ItemDataRole.UserRole,
                                      node.name())
                item_filename.setData(QtCore.Qt.ItemDataRole.DisplayRole,
                                      file_path)
                self.table.setItem(row, 4, item_filename)

            self.table.setSortingEnabled(True)
            self.table.sortByColumn(
                self.table.horizontalHeader().sortIndicatorSection())
            self.table.horizontalHeader().setStretchLastSection(False)
            self.table.resizeColumnsToContents()
            self.table.horizontalHeader().setStretchLastSection(True)
            self.table.resizeRowsToContents()


def panel():
    print('Texture Manager Dialog')
    p = TexManager()
    p.show()
