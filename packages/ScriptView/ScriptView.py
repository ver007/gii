from PyQt4 import QtGui, QtCore, Qsci
from PyQt4.QtCore import Qt
##----------------------------------------------------------------##

from gii.core               import *
from gii.qt                 import QtEditorModule
from gii.qt.controls.Window import MainWindow


##----------------------------------------------------------------##
from ScriptNoteBook  import ScriptNoteBook
from DebuggerHandler import DebuggerHandler
from ListStackView   import ListStackView
from TreeScopeView   import TreeScopeView
##----------------------------------------------------------------##

class ScriptView( QtEditorModule ):
	"""docstring for ObjectEditor"""
	def __init__(self):
		super(ScriptView,self).__init__()
	
	def getName(self):
		return 'script_view'

	def getDependency(self):
		return []

	def getMainWindow( self ):
		return self.window

	def onLoad(self):	
		#init gui	
		self.window = window = ScriptViewWindow(None)
		window.resize(600,400)
		window.setWindowTitle('Script Viewer')
		window.module = self
		
		self.menu = self.addMenuBar( 'script', self.window.menuBar() )
		
		# self.menu.addChild('&File').addChild(['Open','E&xit'])

		editMenu=self.menu.addChild( '&Goto' ).addChild([
				{'name':'goto_line', 'label':'Goto Line', 'shortcut':'Meta+G'},
				{'name':'goto_file', 'label':'Goto File', 'shortcut':'Ctrl+P'}
			])

		self.menu.addChild( '&Debug' ).addChild([
				{ 'name':'step_over', 'label':'Step Over', 'shortcut':'F6' },
				{ 'name':'step_in',   'label':'Step In',   'shortcut':'F7' },
				{ 'name':'step_out',  'label':'Step Out',  'shortcut':'F8' },
				{ 'name':'continue',  'label':'Continue',  'shortcut':'F5' },
				{ 'name':'terminate', 'label':'Terminate', 'shortcut':'Meta+F5' }
			])

		self.book = ScriptNoteBook(window)
		window.addChildWidget(self.book, 'ScriptView.NoteBook', 
			title   = 'main',
			dock    = 'main',
			minSize = (200,200)
		)
		self.book.getPageByFile('picking.lua')
		
		self.panelDebug=PanelDebug()
		self.panelDebug.module=self
		window.addChildWidget(self.panelDebug, 'ScriptView.Debugger', 
			title   = 'Debugger', 
			dock    = 'bottom',
			minSize = (200,200)
		)
		self.toggleDebug(False)

		#init function component
		self.debuggerHandler = DebuggerHandler(self)
		self.book.getPageByFile('picking.lua')
		
		signals.connect('app.command', self.onAppCommand)

	def onStart( self ):
		# self.show()
		pass

	def show(self):
		self.window.show()
		self.window.raise_()

	def hide(self):
		self.window.hide()

	def onUnload(self):
		if self.debuggerHandler.busy:
				self.debuggerHandler.doStop()	#stop debug
		signals.dispatchAll()
		self.window.close()
		self.window = None

	def onUpdate(self):
		pass

	def locateFile(self, filename, lineNumber=1, highLight = False):
		if not self.window.isVisible():
			self.window.show()
		if not self.window.hasFocus():
			if highLight:
				# self.window.requestUserAttention()
				pass
			self.window.raise_()
		page=self.book.getPageByFile(filename, True)
		if not page:
			return False
		self.book.selectPage(page)
		page.locateLine(lineNumber, highLight)

	def toggleDebug(self, toggle):
		# if toggle:
		# 	self.window.setWindowModality(Qt.ApplicationModal)
		# else: 
		# 	self.window.setWindowModality(Qt.NonModal)
		# self.panelDebug.toggleDebug(toggle)
		self.enableMenu('script/debug/step_in',toggle)
		self.enableMenu('script/debug/step_over',toggle)
		self.enableMenu('script/debug/step_out',toggle)
		self.enableMenu('script/debug/terminate',toggle)
		self.enableMenu('script/debug/continue',toggle)

	def onMenu(self, node):

		name=node.name
		if name=='step_in':
			self.debuggerHandler.doStepIn()
		elif name=='step_over':
			self.debuggerHandler.doStepOver()
		elif name=='step_out':
			self.debuggerHandler.doStepOut()
		elif name=='terminate':
			self.debuggerHandler.doStop()
		elif name=='continue':
			self.debuggerHandler.doContinue()

	def onAppCommand(self, cmd, src=None):
		if cmd=='exec':
			if self.debuggerHandler.busy:
				self.debuggerHandler.doStop()	#stop debug

	def onSetFocus(self):
		self.window.raise_()
		self.window.setFocus()
		App.get().setActiveWindow(self.window)

##----------------------------------------------------------------##
class ScriptViewWindow( MainWindow ):
	"""docstring for ScriptViewWindow"""
	def __init__(self, arg):
		super(ScriptViewWindow, self).__init__(arg)		

	def closeEvent(self,event):
		if self.module.alive:
			self.hide()
			event.ignore()

##----------------------------------------------------------------##
class PanelDebug(QtGui.QWidget):
	def __init__(self,*args):
		super(PanelDebug,self).__init__(*args)
		layout=QtGui.QVBoxLayout(self)
		layout.setSpacing(0)
		layout.setMargin(0)
		self.toolbar=QtGui.QToolBar(self)
		self.toolbar.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
		layout.addWidget(self.toolbar)

		splitter=QtGui.QSplitter(QtCore.Qt.Horizontal)
		splitter.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
		layout.addWidget(splitter)
		
		font=QtGui.QFont()
		font.setFamily('Consolas')
		font.setPointSize(12)

		listStack=ListStackView()
		treeScope=TreeScopeView()

		listStack.setFont(font)
		treeScope.setFont(font)

		self.listStack=listStack
		self.treeScope=treeScope

		listStack.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
		treeScope.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)

		splitter.addWidget(listStack)
		splitter.addWidget(treeScope)

		# self.toolbar.addAction('hello').triggered.connect(self.onStepIn)

	def toggleDebug(self, toggle):
		pass
		# self.toolbarStack.EnableTool(forms.TOOLID_CONTINUE,toggle)
		# self.toolbarStack.EnableTool(forms.TOOLID_STEPIN, toggle)
		# self.toolbarStack.EnableTool(forms.TOOLID_STEPOUT, toggle)
		# self.toolbarStack.EnableTool(forms.TOOLID_STEPOVER, toggle)
		# self.toolbarStack.EnableTool(forms.TOOLID_STOP, toggle)
		# self.toolbarStack.Enable(toggle)

	def loadVarData(self,data,parentName):
		self.treeScope.loadVarData(data, parentName)

	def loadStackData(self, data ):
		self.listStack.loadStackData(data or [])		

	def onStepIn( self, event ):
		self.module.debuggerHandler.doStepIn()
	
	def onStepOver( self, event ):
		self.module.debuggerHandler.doStepOver()
	
	def onStepOut( self, event ):
		self.module.debuggerHandler.doStepOut()
	
	def onStop( self, event ):
		self.module.debuggerHandler.doStop()
	
	def onContinue( self, event ):
		self.module.debuggerHandler.doContinue()
##----------------------------------------------------------------##

ScriptView().register()

