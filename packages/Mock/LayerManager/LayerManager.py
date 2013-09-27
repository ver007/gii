import random
##----------------------------------------------------------------##
from gii.core        import app, signals
from gii.qt          import QtEditorModule

from gii.qt.IconCache                  import getIcon
from gii.qt.controls.GenericTreeWidget import GenericTreeWidget
from gii.moai.MOAIRuntime import MOAILuaDelegate
from gii.SceneEditor      import SceneEditorModule, getSceneSelectionManager
from gii.qt.helpers   import addWidgetWithLayout, QColorF, unpackQColor

##----------------------------------------------------------------##
from PyQt4           import QtCore, QtGui, uic
from PyQt4.QtCore    import Qt

##----------------------------------------------------------------##
from mock import _MOCK, isMockInstance
##----------------------------------------------------------------##

def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

def _fixDuplicatedName( names, name, id = None ):
	if id:
		testName = name + '_%d' % id
	else:
		id = 0
		testName = name
	#find duplicated name
	if testName in names:
		return _fixDuplicatedName( names, name, id + 1)
	else:
		return testName

##----------------------------------------------------------------##
class LayerManager( SceneEditorModule ):
	def __init__(self):
		super( LayerManager, self ).__init__()

	def getName( self ):
		return 'layer_manager'

	def getDependency( self ):
		return [ 'scene_editor' ]

	def onLoad( self ):
		#UI
		self.windowTitle = 'Layers'
		self.window = self.requestDockWindow( 'LayerManager',
			title     = 'Layers',
			size      = (120,120),
			minSize   = (120,120),
			dock      = 'left'
			)

		#Components
		self.tree = self.window.addWidget( 
			LayerTreeWidget(
				self.window,
				multiple_selection = False,
				sorting            = False,
				editable           = True,
				drag_mode          = 'internal'
				)
			)

		self.tool = self.addToolBar( 'layer_manager', self.window.addToolBar() )
		self.delegate = MOAILuaDelegate( self )
		self.delegate.load( _getModulePath( 'LayerManager.lua' ) )

		self.addTool( 'layer_manager/add',    label = '+')
		self.addTool( 'layer_manager/remove', label = '-')
		self.addTool( 'layer_manager/up',     label = 'up')
		self.addTool( 'layer_manager/down',   label = 'down')

		
		#SIGNALS
		signals.connect( 'moai.clean', self.onMoaiClean )

	def onStart( self ):
		self.tree.rebuild()

	def onMoaiClean( self ):
		self.tree.clear()

	def onTool( self, tool ):
		name = tool.name
		if name == 'add':
			layer = self.delegate.safeCall( 'addLayer' )
			self.tree.addNode( layer )
			self.tree.editNode( layer )
			self.tree.selectNode( layer )
			
		elif name == 'remove':
			for l in self.tree.getSelection():
				self.delegate.safeCall( 'removeLayer', l )
				self.tree.removeNode( l )
		elif name == 'up':
			for l in self.tree.getSelection():
				self.delegate.safeCall( 'moveLayerUp', l )
				self.tree.rebuild()
				self.tree.selectNode( l )
				break
		elif name == 'down':
			for l in self.tree.getSelection():
				self.delegate.safeCall( 'moveLayerDown', l )		
				self.tree.rebuild()
				self.tree.selectNode( l )
				break

	def changeLayerName( self, layer, name ):
		layer.setName( layer, name )

	def toggleHidden( self, layer ):
		layer.setVisible( layer, not layer.isVisible( layer ) )
		self.tree.refreshNodeContent( layer )
		signals.emit( 'scene.update' )

	def toggleLock( self, layer ):
		layer.locked = not layer.locked
		self.tree.refreshNodeContent( layer )
		signals.emit( 'scene.update' )
	
##----------------------------------------------------------------##
class LayerTreeWidget( GenericTreeWidget ):
	def getHeaderInfo( self ):
		return [ ('Name',150), ('Show', 30), ('Edit',30), ('',-1) ]

	def getRootNode( self ):
		return _MOCK.game

	def saveTreeStates( self ):
		pass

	def loadTreeStates( self ):
		pass

	def getNodeParent( self, node ): # reimplemnt for target node	
		if isMockInstance( node, 'Game' ):
			return None
		return _MOCK.game

	def getNodeChildren( self, node ):
		if isMockInstance( node, 'Game' ):
			result = []
			for item in node.layers.values():
				if item.name == '_GII_EDITOR_LAYER': continue
				result.append( item )
			return reversed( result )
		return []

	def updateItemContent( self, item, node, **option ):
		name = None
		if isMockInstance( node, 'Layer' ):
			item.setText( 0, node.name )
			if node.default :
				item.setIcon( 0, getIcon('obj_blue') )
			else:
				item.setIcon( 0, getIcon('obj') )

			if node.visible:
				item.setIcon( 1, getIcon(None) )
			else:
				item.setIcon( 1, getIcon('state_no') )

			if node.locked:
				item.setIcon( 2, getIcon('state_no'))
			else:
				item.setIcon( 2, getIcon(None) )

		else:
			item.setText( 0, '' )
			item.setIcon( 0, getIcon('normal') )
		
	def onItemSelectionChanged(self):
		selections = self.getSelection()
		getSceneSelectionManager().changeSelection( selections )

	def onItemChanged( self, item, col ):
		layer = self.getNodeByItem( item )
		app.getModule('layer_manager').changeLayerName( layer, item.text(0) )

	def onDClicked(self, item, col):
		if col == 1: #hide toggle
			app.getModule('layer_manager').toggleHidden( self.getNodeByItem(item) )
		elif col == 2: #lock toggle
			app.getModule('layer_manager').toggleLock( self.getNodeByItem(item) )

##----------------------------------------------------------------##
LayerManager().register()
