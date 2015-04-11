from PyQt4 import QtGui, QtCore, QtOpenGL, uic
from PyQt4.QtCore import Qt, QObject, QEvent, pyqtSignal
from PyQt4.QtCore import QPoint, QRect, QSize
from PyQt4.QtCore import QPointF, QRectF, QSizeF
from PyQt4.QtGui import QColor, QTransform
from OpenGL.GL import *



def makeBrush( **option ):
	brush = QtGui.QBrush()
	brush.setStyle( option.get( 'style', Qt.SolidPattern ) )
	color = QColor( option.get( 'color', '#ffffff' ) )
	color.setAlphaF( option.get( 'alpha', 1 ) )
	brush.setColor( color )
	return brush

def makePen( **option ):
	pen = QtGui.QPen()
	pen.setStyle( option.get( 'style', Qt.SolidLine ) )
	color = QColor( option.get( 'color', '#ffffff' ) )
	color.setAlphaF( option.get( 'alpha', 1 ) )
	pen.setColor( color )
	pen.setWidth( option.get( 'width', 1 ) )
	return pen

_ItemStyleRegistry = {}

def registerStyle( id, pen, brush, penText = None ):
	_ItemStyleRegistry[ id ] = ( pen, brush, penText or pen )

def applyStyle( id, painter ):
	if _ItemStyleRegistry.has_key( id ):
		pen, brush, penText = _ItemStyleRegistry[ id ]
		painter.setPen( pen )
		painter.setBrush( brush )
		def drawStyledText( rect, flags, text ):
			painter.setPen( penText )
			painter.drawText( rect, flags, text )
			painter.setPen( pen )
		painter.drawStyledText = drawStyledText
	else:
		print 'no style found', id

def makeStyle( id, penOption, brushOption, textOption = None ):
	pen = None
	brush = None
	penText = None
	if isinstance( penOption, dict ):
		pen = makePen( **penOption )
	elif isinstance( penOption, str ):
		pen = makePen( color = penOption )

	if isinstance( brushOption, dict ):
		brush = makeBrush( **brushOption )
	elif isinstance( brushOption, str ):
		brush = makeBrush( color = brushOption )

	if isinstance( textOption, dict ):
		penText = makePen( **textOption )
	elif isinstance( textOption, str ):
		penText = makePen( color = textOption )

	return registerStyle( id, pen, brush, penText )


##----------------------------------------------------------------##

class StyledItemMixin:
	def setItemType( self, t ):
		self.itemType = t

	def setItemState( self, state ):
		self.itemState = state

	def getItemType( self ):
		return getattr( self, 'itemType', 'unknown' )

	def getItemState( self ):
		return getattr( self, 'itemState', 'normal' )

	def findItemStyleName( self ):
		n = '%s:%s' % ( self.getItemType(), self.getItemState() )
		if _ItemStyleRegistry.has_key( n ):
			return n
		if _ItemStyleRegistry.has_key( self.itemType ):
			return self.itemType
		return 'default'

	def updateItemState( self ):
		self.activeStyleId = self.findItemStyleName()

	def paint( self, painter, option, widget ):
		self.updateItemState()
		applyStyle( self.findItemStyleName(), painter )
		self.onPaint( painter, option, widget )

	def onPaint( self, paint, option, widget ):
		pass



##----------------------------------------------------------------##
class GLGraphicsView( QtGui.QGraphicsView ):
	def __init__( self, *args, **kwargs ):
		super( GLGraphicsView, self ).__init__( *args, **kwargs )
		self.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
		self.setVerticalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
		self.setViewportUpdateMode( QtGui.QGraphicsView.SmartViewportUpdate )
		# self.setViewportUpdateMode( QtGui.QGraphicsView.FullViewportUpdate )
		fmt = QtOpenGL.QGLFormat()
		fmt.setRgba(True)
		fmt.setAlpha(True)
		fmt.setDepth(False)
		fmt.setDoubleBuffer(True)
		fmt.setSwapInterval(0)
		fmt.setSampleBuffers( True )
		viewport = QtOpenGL.QGLWidget( QtOpenGL.QGLContext(fmt, None) )
		viewport.makeCurrent()
		self.setViewport( viewport )
		self.setRenderHint( QtGui.QPainter.Antialiasing, False )
		self.setTransformationAnchor( self.NoAnchor )
		# self.setRenderHint( QtGui.QPainter.HighQualityAntialiasing, True )
		# self.setCacheMode( self.CacheBackground )


##----------------------------------------------------------------##
class GridBackground( QtGui.QGraphicsRectItem ):
	_gridPenV  = makePen( color = '#333', width = 1 )
	_gridPenH  = makePen( color = '#444', width = 1 )
	def __init__( self ):
		super( GridBackground, self ).__init__()
		self.setZValue( -100 )
		self.gridWidth = 50
		self.gridHeight = 50 
		self.offsetX = 0
		self.offsetY = 0

	def setOffset( self, x, y ):
		self.offsetX = x
		self.offsetY = y

	def setGridSize( self, width, height = None ):
		if not height:
			height = width
		self.gridWidth = width
		self.gridHeight = height
		self.update()

	def setGridWidth( self, width ):
		self.setGridSize( width, self.gridHeight )

	def setGridHeight( self, height ):
		self.setGridSize( self.gridWidth, height )

	def paint( self, painter, option, widget ):
		painter.setRenderHint( QtGui.QPainter.Antialiasing, False )
		rect = painter.viewport()
		transform = painter.transform()
		dx = transform.dx() 
		dy = transform.dy()
		tw = self.gridWidth
		th = self.gridHeight
		w = rect.width()
		h = rect.height()
		rows = int( h/self.gridHeight ) + 1
		cols = int( w/self.gridWidth ) + 1
		x0 = -dx
		y0 = -dy
		x1 = x0 + w
		y1 = y0 + h
		ox = (dx) % tw
		oy = (dy) % th

		offx = self.offsetX
		painter.setPen( GridBackground._gridPenV )
		for col in range( cols ): #V lines
			x = col * tw + ox + x0 + offx
			painter.drawLine( x, y0, x, y1 )
		
		# x0 = max( x0, _HEAD_OFFSET )
		offy = self.offsetY
		painter.setPen( GridBackground._gridPenH )
		for row in range( rows ): #H lines
			y = row * th + oy + y0 + offy
			painter.drawLine( x0, y, x1, y )
