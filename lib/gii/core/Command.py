import logging

class EditorCommandMeta( type ):
	def __init__( cls, name, bases, dict ):
		super( EditorCommandMeta, cls ).__init__( name, bases, dict )
		fullname = dict.get( 'name', None )
		if not fullname: return
		EditorCommandRegistry.get().registerCommand( fullname, cls )

##----------------------------------------------------------------##
class EditorCommand( object ):
	__metaclass__ = EditorCommandMeta

	def init( self, **kwargs ):
		pass
	
	def redo( self ):
		return

	def undo( self ):
		return

	def canMerge( self, prevCommand ):
		return False


##----------------------------------------------------------------##
class EditorCommandStack( object ):
	def __init__( self, stackLimit = 100 ):
		self.undoStack = []
		self.redoStack    = []
		self.stackLimit = stackLimit

	def clear():
		self.undoStack = []
		self.redoStack    = []

	def canUndo( self ):
		return len( self.undoStack ) > 0

	def canRedo( self ):
		return len( self.redoStack ) > 0

	def pushCommand( self, cmd, redo = False ):
		assert not hasattr( cmd, 'inStack' )
		count = len( self.undoStack )
		cmd.inStack = True
		cmd.merged = False
		if count>0:
			lastCommand = self.undoStack[ count - 1 ]
			if cmd.canMerge( lastCommand ):
				cmd.merged = True
			if count >= self.stackLimit:
				self.undoStack.pop( 0 )
		self.undoStack.append( cmd )

		if cmd.redo() == False: #failed
			self.undoStack.pop()
			return False

		if not redo:
			self.redoStack = []

		return True

	def undoCommand( self ):
		count = len( self.undoStack )
		if count>0:
			cmd = self.undoStack[ count-1 ]
			if cmd.undo() == False:
				return False
			self.undoStack.pop()
			self.redoStack.append( cmd )
			if cmd.merged:
				return self.undoCommand()
			else:
				return True
		return False

	def redoCommand( self ):
		if not self.canRedo(): return False
		cmd = self.redoStack.pop()
		return self.pushCommand( cmd, True )
		#TODO: redo merged commands

##----------------------------------------------------------------##
class EditorCommandRegistry(object):
	_singleton = None

	@staticmethod
	def get():
		return EditorCommandRegistry._singleton

	def __init__( self ):
		assert not EditorCommandRegistry._singleton
		EditorCommandRegistry._singleton = self
		self.stacks   = {}
		self.commands = {}

	def createCommandStack( self, name ):
		stack = EditorCommandStack()
		self.stacks[ name ] = stack
		return stack

	def getCommandStack( self, name ):
		return self.stacks.get( name , None )

	def registerCommand( self, fullname, cmdClass ):
		cmdBlobs = fullname.split('/')
		assert len(cmdBlobs) == 2, 'command name must be <group>/<name>'
		stackName, cmdName = cmdBlobs[0], cmdBlobs[1]
		self.commands[ fullname ] = ( stackName, cmdName, cmdClass )
		logging.info( 'register command: %s / %s' % ( stackName, cmdName ) )

	def doCommand( self, fullname, **kwargs ):
		entry = self.commands.get( fullname, None )
		if not entry:
			logging.warn( 'command not found %s ' % fullname )
			return None
		( stackName, cmdName, cmdClass ) = entry
		stack = self.getCommandStack( stackName )
		if not stack:
			logging.warn( 'command stack not found %s ' % stackName )
			return None
		cmd = cmdClass()
		if cmd.init( **kwargs ) ==  False: return None
		return stack.pushCommand( cmd )
