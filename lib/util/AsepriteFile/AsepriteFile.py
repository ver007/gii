import sys
import struct
import cStringIO
import zlib
from PIL import Image

def read_fmt(fmt, fp):
	"""
	Reads data from ``fp`` according to ``fmt``.
	"""
	fmt = str("<" + fmt)
	fmt_size = struct.calcsize(fmt)
	data = fp.read(fmt_size)
	assert len(data) == fmt_size, (len(data), fmt_size)
	x = struct.unpack(fmt, data)
	if len( x ) == 1: return x[0]
	return x

def read_string( fp ):
	s = read_fmt( 'H', fp )
	string = fp.read( s )
	return string

##----------------------------------------------------------------##
class ASEFrame(object):
	def __init__( self ):
		self.cels = []

	def getCels( self ):
		return self.cels


##----------------------------------------------------------------##
class ASECel(object):
	def __init__( self ):
		self.x, self.y = 0, 0
		self.w, self.h = 0, 0
		self.type       = 0
		self.layerIndex = None
		self.layer      = None
		self.linked     = None
		self.image      = None
		self.bbox       = None

	def getImage( self ):
		if self.linked:
			return self.linkedCel.getImage()


##----------------------------------------------------------------##
class ASELayer(object):
	def __init__( self ):
		self.flags = 0
		self.type = 0
		self.childLevel = 0
		self.blend = 0
		self.opacity = 255
		self.name = ''

##----------------------------------------------------------------##					
class ASEFrameTag(object):
	def __init__( self ):
		self.name = ''
		self.color = ( 1,1,1,1 )
		

##----------------------------------------------------------------##
class ASEDocument(object):
	def __init__( self ):
		self.frames = []
		self.layers = []
		self.tags   = []
		self.flags  = 0
		self.width  = 0
		self.height = 0
		self.speed  = 1
		self.depth  = 0

	def load( self, path ):
		#read header
		self.frames = []
		fp = file( path, 'rb' )
		filesize, mnumber = read_fmt( 'LH', fp )
		frameNum          = read_fmt( 'H', fp )
		w, h              = read_fmt( 'HH', fp )
		depth             = read_fmt( 'H', fp )
		flags             = read_fmt( 'L', fp )
		speed             = read_fmt( 'H', fp )
		read_fmt( 'LL', fp) #skip
		transparentIdx = read_fmt( 'c', fp )
		fp.read( 3 )
		colorNum = read_fmt( 'H', fp )
		fp.read( 94 )
		self.flags = flags
		self.width, self.height = w, h
		self.speed = speed
		self.colorNum = colorNum
		self.depth = depth 
		if depth != 32:
			raise Exception( 'only RGBA mode is supported' )
			
		#frames
		for fid in range( frameNum ):
			frame = ASEFrame()
			frameSize, mnumber = read_fmt( 'LH', fp )
			chunkNum = read_fmt( 'H', fp )
			duration = read_fmt( 'H', fp )
			fp.read( 6 )
			frame.duration = duration
			self.frames.append( frame )
			
			contextObject = None

			for ci in range( chunkNum ):
				chunkSize, chunkType = read_fmt( 'LH', fp )
				chunkData = fp.read( chunkSize - 6 )
				dp = cStringIO.StringIO( chunkData )
				
				if chunkType == 0x0004: #old palette SKIP
					pass

				elif chunkType == 0x0011: #old palette SKIP
					pass

				elif chunkType == 0x2004: #layer
					layer = ASELayer()
					layer.flags = read_fmt( 'H', dp )
					layer.type, layer.childLevel = read_fmt( 'HH', dp )
					defaultw, defaulth = read_fmt( 'HH', dp )
					layer.blend   = read_fmt( 'H', dp )
					layer.opacity = read_fmt( 'c', dp )
					dp.read( 3 )
					layer.name = read_string( dp )
					self.layers.append( layer )
					contextObject = layer

				elif chunkType == 0x2005: #cel
					cel = ASECel()
					cel.layerIndex = read_fmt( 'H', dp )
					cel.x, cel.y   = read_fmt( 'HH', dp )
					cel.opacity    = read_fmt( 'c', dp )
					cel.type       = read_fmt( 'H', dp )
					dp.read( 7 )
					ctype = cel.type
					if ctype == 1: #linked cel
						cel.linked = read_fmt( 'H', dp )

					else:
						cel.w, cel.h = read_fmt( 'HH', dp )
						data = dp.read()
						if ctype == 2: #raw cel
							data = zlib.decompress( data )
						img = Image.frombuffer( 'RGBA', (cel.w, cel.h), data, 'raw', 'RGBA', 0, 1 )
						bbox = img.getbbox()
						cropped = img.crop( bbox )
						cel.image = img
						cel.bbox  = bbox

					frame.cels.append( cel )
					contextObject = cel

				elif chunkType == 0x2016: #mask SKIP
					pass

				elif chunkType == 0x2017: #path SKIP
					pass

				elif chunkType == 0x2018: #frame tags
					tagNum = read_fmt( 'H', dp )
					dp.read( 8 )
					for tid in range( tagNum ):
						tag = ASEFrameTag()
						tag.id = tid
						tag.frameFrom, tag.frameTo = read_fmt( 'HH', dp )
						tag.direction = read_fmt( 'c', dp )
						dp.read( 8 )
						dp.read( 3 )
						dp.read( 1 )
						tag.name = read_string( dp )
						self.tags.append( tag )

				elif chunkType == 0x2019: #new palette SKIP
					pass

				elif chunkType == 0x2020: #userdata
					flags = read_fmt( 'L', dp )
					userText = None
					userColor = None
					if flags & 0x1:
						userText = read_string( dp )
					if flags & 0x2:
						userColor = read_fmt( 'cccc', dp )
					contextObject.userText  = userText
					contextObject.userColor = userColor

if __name__ == '__main__':
	doc = ASEDocument()
	doc.load( 'test.ase' )
	# print 'layer count:', len( doc.layers )
	# for i, frame in enumerate( doc.frames ):
	# 	print 'frame #',i
	# 	for j, cel in enumerate( frame.cels ):
	# 		print cel.type, cel.layerIndex, cel.x, cel.y, cel.w, cel.h

