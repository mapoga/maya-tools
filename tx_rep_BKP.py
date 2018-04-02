from PyQt4 import QtCore, QtGui

import maya.cmds as mc
import pymel.core as pm

import maya.OpenMayaUI as omu
import sip
import os, subprocess

OBJECT_ROLE = 'OBJECT_ROLE'

# MQtUtil class exists in Maya 2011 and up
def maya_main_window():
	ptr = omu.MQtUtil.mainWindow()
	return sip.wrapinstance(long(ptr), QtCore.QObject)

class RenamingDialog(QtGui.QDialog):

	def __init__(self, parent=maya_main_window()):
		QtGui.QDialog.__init__(self, parent)

		self.setWindowTitle("Texture Manager")
		w = 900
		h = 500
		self.setSizePolicy(w,h)
		self.resize(w,h)

		self.create_layout()
		self.create_connections()
		#self.execute_refresh()
		self.refresh()

	def create_layout(self):

		self.current_nodes = tx_table_view()
		self.current_nodes.setStyleSheet("""
			.tx_table_view::item{
				padding-left: 5px;
			}
			""")
		self.search_label = QtGui.QLabel('Search  ')
		self.search_line_edit = QtGui.QLineEdit()
		self.replace_label = QtGui.QLabel('Replace')
		self.replace_line_edit = QtGui.QLineEdit()
		self.refresh_button = QtGui.QPushButton('Refresh')
		self.switch_button = QtGui.QPushButton('Switch')
		self.clear_button = QtGui.QPushButton('Clear')
		self.replace_button = QtGui.QPushButton('Replace Selected')
		self.search_line_edit.setDragEnabled(True)
		self.replace_line_edit.setDragEnabled(True)
		self.current_nodes.setDragEnabled(True)
		self.stats_tx = QtGui.QLabel('missing tx: 0')
		self.stats_file = QtGui.QLabel('missing files: 0')

		search_layout = QtGui.QHBoxLayout()
		search_layout.addWidget(self.search_label)
		search_layout.addWidget(self.search_line_edit)

		replace_layout = QtGui.QHBoxLayout()
		replace_layout.addWidget(self.replace_label)
		replace_layout.addWidget(self.replace_line_edit)

		input_layout = QtGui.QVBoxLayout()
		input_layout.addLayout(search_layout)
		input_layout.addLayout(replace_layout)

		switch_layout = QtGui.QVBoxLayout()
		switch_layout.addWidget(self.switch_button)
		switch_layout.addWidget(self.clear_button)

		execute_replace_layout = QtGui.QVBoxLayout()
		execute_replace_layout.addWidget(self.replace_button)

		stats_layout = QtGui.QHBoxLayout()
		stats_layout.addStretch()
		stats_layout.addWidget(self.stats_tx)
		stats_layout.addWidget(self.stats_file)

		refresh_layout = QtGui.QVBoxLayout()
		refresh_layout.addWidget(self.refresh_button)

		main_input_layout = QtGui.QHBoxLayout()
		main_input_layout.addLayout(refresh_layout)		
		main_input_layout.addLayout(switch_layout)
		main_input_layout.addLayout(input_layout)
		main_input_layout.addLayout(execute_replace_layout)
		self.replace_button.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
		self.refresh_button.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)

		main_layout = QtGui.QVBoxLayout()
		main_layout.setSpacing(4)
		main_layout.setMargin(14)

		main_layout.addWidget(self.current_nodes)
		main_layout.addLayout(main_input_layout)
		main_layout.addLayout(stats_layout)
		self.setLayout(main_layout)

		tx = get_textures()
		self.table_model = tx_table_model(tx)
		self.current_nodes.setModel(self.table_model)

	def create_connections(self):
		self.replace_button.clicked.connect(self.execute_replace)
		self.refresh_button.clicked.connect(self.execute_refresh)
		self.switch_button.clicked.connect(self.execute_switch)
		self.clear_button.clicked.connect(self.execute_clear)
		self.search_line_edit.textChanged.connect(self.search_changed)
		self.replace_line_edit.textChanged.connect(self.replace_changed)
		self.current_nodes.selectionModel().selectionChanged.connect(self.selection_changed)


	def refresh(self):
		#self.execute_refresh()
		self.current_nodes.setModel(self.table_model)
		self.current_nodes.resizeColumnsToContents()
		self.current_nodes.resizeRowsToContents()
		self.current_nodes.horizontalHeader().setStretchLastSection(True)
		self.current_nodes.verticalHeader().hide()

	def execute_switch(self):
		s = self.search_line_edit.text()
		self.search_line_edit.setText(self.replace_line_edit.text())
		self.replace_line_edit.setText(s)

	def execute_refresh(self):
		tx = get_textures()
		self.table_model = tx_table_model(tx)
		self.current_nodes.setModel(self.table_model)
		self.current_nodes.resizeColumnsToContents()
		self.current_nodes.resizeRowsToContents()

	def execute_clear(self):
		self.search_line_edit.clear()
		self.replace_line_edit.clear()

	def execute_replace(self):
		textures = self.get_selected_tx()
		for texture in textures:
			texture.set_path(texture.temp_file)
			print(texture)

	def search_changed(self):
		print('searchChanged: ', self.search_line_edit.text())
		sel = self.current_nodes.selectedIndexes()
		tmp = self.get_selected_model_index(sel)
		self.update_temp_files(tmp)

	def replace_changed(self):
		print('replaceChanged: ', self.replace_line_edit.text())
		sel = self.current_nodes.selectedIndexes()
		tmp = self.get_selected_model_index(sel)
		self.update_temp_files(tmp)

	def selection_changed(self, sel=None, unsel=None):
		# clear unselected data
		unselected_textures = [t.model().data[t.row()] for t in unsel.indexes()]
		for tx in unselected_textures:
			tx.temp_file = tx.file
		# updated unselected
		unselect = [s.model().index(s.row(), s.model().mime.index('file')) for s in unsel.indexes()]
		temp = self.get_selected_model_index(unselect)
		for modelIndex in temp:
			a = modelIndex.model().index( modelIndex.row(), 0)
			b = modelIndex.model().index( modelIndex.row(), len(modelIndex.model().mime)-1)
			self.current_nodes.dataChanged(a, b)

		#Updated selected
		sel = self.current_nodes.selectedIndexes()
		tmp = self.get_selected_model_index(sel)
		self.update_temp_files(tmp)
	'''
	def set_missing_style(self, missings=None):
		if missings:
			for item in missings:
				item.setStyleSheet("""
					.tx_table_view::item{
						padding-left: 5px;
						background-color: rgb(100,0,0)
					}
					""")
		pass
	'''



	def update_temp_files(self, textures):
		s = str(self.search_line_edit.text())
		r = str(self.replace_line_edit.text())
		print("ISSPACE: ", s , s.isspace(), ''.isspace())
		if not s:
			print("NOT S")
		if not s or s.isspace():
			s = ''
		if not r or r.isspace():
			r = ''
		for modelIndex in textures:
			tx = modelIndex.model().data[modelIndex.row()]
			if s:
				tx.temp_file = tx.file.replace(s, r)
			else:
				tx.temp_file = tx.file
			a = modelIndex.model().index( modelIndex.row(), 0)
			b = modelIndex.model().index( modelIndex.row(), len(modelIndex.model().mime)-1)
			self.current_nodes.dataChanged(a, b)

	def get_selected_model_index(self, selected):
		already_selected = []
		selected_rows = []
		for item in selected:
			if item.row() not in already_selected:
				selected_rows.append(item)
				already_selected.append(item.row())
		return sorted(selected_rows)

	def get_selected_tx(self):
		sel = self.current_nodes.selectedIndexes()
		selected_rows = self.get_selected_model_index(sel)
		return [t.model().data[t.row()] for t in selected_rows]


class tx_table_view(QtGui.QTableView):
	def __init__(self, parent=None, *args):
		QtGui.QTableView.__init__(self, parent, *args)

	def mouseMoveEvent(self, event):

		item = self.indexAt(event.pos())
		if not item:
			return # nothing was selected

		mimeData = item.model().mimeData([item])

		drag = QtGui.QDrag(self)
		drag.setMimeData(mimeData)
		
		dropAction = drag.exec_(QtCore.Qt.CopyAction)
		print("DAROPACTION: ", dropAction)
		if dropAction == QtCore.Qt.MoveAction:
			item.close()

	def mouseDoubleClickEvent(self, event):
		print("Double click: ")
		item = self.indexAt(event.pos())
		if not item:
			return
		element = getattr(item.model().data[item.row()], item.model().mime[item.column()].lower())
		if item.column() == item.model().mime.index('file'): #File
			folder = os.path.dirname(element)
			subprocess.Popen([r'xdg-open' , folder])
		elif item.column() == item.model().mime.index('name'): #name
			pm.select(element)
		elif item.column() == item.model().headers.index('Tx'): #tx
			tx = item.model().data[item.row()].tx
			if tx:
				folder = os.path.dirname(tx)
				subprocess.Popen([r'xdg-open' , folder])
		pass

class tx_table_model(QtCore.QAbstractTableModel):
	def __init__(self, textures, parent=None, *args):
		QtCore.QAbstractTableModel.__init__(self, parent, *args)

		self.data = textures
		self.headers = ['Type', 'Name', 'Tx', 'File']
		self.mime = ['type', 'name', 'tx_status', 'file']
		self.attributes = ['type', 'name', 'tx_status', 'temp_file']

	def mimeData(self, modelIndexList):
		txt = getattr(self.data[modelIndexList[0].row()], self.mime[modelIndexList[0].column()].lower())
		mime = QtCore.QMimeData()
		mime.setText(txt)
		return mime

	def mimeTypes(self):
		return QtCore.QStringList(QtCore.QString('text/plain'))
		pass

	def rowCount(self, parent):
		return len(self.data)

	def columnCount(self, parent):
		return len(self.headers)

	def data(self, index, role):
		if role == QtCore.Qt.DisplayRole:
			return QtCore.QVariant( getattr(self.data[index.row()], self.attributes[index.column()].lower() ))
		return QtCore.QVariant()

	def headerData(self, section, orientation, role):
		if role == QtCore.Qt.DisplayRole and section < len(self.headers):
			return QtCore.QVariant(self.headers[section])
		return QtCore.QVariant()


class tx(object):
	def __init__(self, node=None):
		object.__init__(self)
		self.__node = node
		self.__type = pm.objectType(self.node)
		self.__name = str((pm.ls(self.node, shortNames=True))[0])
		self.file = self.get_path()
		self.temp_file = self.file

	def __repr__(self):
		return '{0}: {1}'.format(self.type, self.node)

	@property
	def node(self):
		return self.__node
	@property
	def type(self):
		return self.__type
	@property
	def name(self):
		return self.__name
	@property
	def tx(self):
		tx = str(os.path.splitext(self.temp_file)[0])+'.tx'
		if os.path.isfile(tx):
			return tx
		return False
	@property
	def tx_status(self):
		if self.tx:
			return 'yes'
		return 'NO'
	@property
	def file_exists(self):
		return os.path.isfile(self.temp_file)

	def get_path(self):
		if self.type == 'aiImage':
			return self.node.filename.get()
		return self.node.fileTextureName.get()

	def set_path(self, path):
		p = str(path)
		if self.type == 'aiImage':
			self.node.filename.set(p)
		else:
			self.node.fileTextureName.set(p)
		self.file = self.get_path()
		self.temp_file = self.file


def get_textures():
	nodes = sorted(pm.ls(long=True, et="file"))
	textures = []
	for node in nodes:
		t = tx(node)
		textures.append(t)
	return textures

def window():
	print("lol")
	ex = RenamingDialog()
	ex.show()

# Error: nt.Fractal(u'RC_BLD_BERLNSTD_GroundPitLarge_hirez:fractal1') has no attribute or method named 'fileTextureName'
# Traceback (most recent call last):
#   File "<maya console>", line 4, in <module>
#   File "/home/VGMTL/mgaubin/maya/2015-x64/prefs/scripts/tx_rep.py", line 357, in window
#     ex = RenamingDialog()
#   File "/home/VGMTL/mgaubin/maya/2015-x64/prefs/scripts/tx_rep.py", line 28, in __init__
#     self.create_layout()
#   File "/home/VGMTL/mgaubin/maya/2015-x64/prefs/scripts/tx_rep.py", line 99, in create_layout
#     tx = get_textures()
#   File "/home/VGMTL/mgaubin/maya/2015-x64/prefs/scripts/tx_rep.py", line 351, in get_textures
#     t = tx(node)
#   File "/home/VGMTL/mgaubin/maya/2015-x64/prefs/scripts/tx_rep.py", line 302, in __init__
#     self.file = self.get_path()
#   File "/home/VGMTL/mgaubin/maya/2015-x64/prefs/scripts/tx_rep.py", line 335, in get_path
#     return self.node.fileTextureName.get()
#   File "/vg/apps/Autodesk/maya2015-x64/lib/python2.7/site-packages/pymel/core/nodetypes.py", line 349, in __getattr__
#     raise AttributeError,"%r has no attribute or method named '%s'" % (self, attr)
# AttributeError: nt.Fractal(u'RC_BLD_BERLNSTD_GroundPitLarge_hirez:fractal1') has no attribute or method named 'fileTextureName' # 