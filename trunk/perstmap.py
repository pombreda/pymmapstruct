import mmap
builtinopen= open

from ctypes import *

prototype= PYFUNCTYPE( c_int, py_object, POINTER(c_void_p), POINTER(c_uint) )
PyObject_AsWriteBuffer= prototype( ( "PyObject_AsWriteBuffer", pythonapi ) )
class perstmap:
	def __init__( self, map ):
		_b= c_void_p(0)
		_s= c_uint(0)
		PyObject_AsWriteBuffer( map, byref(_b), byref(_s) )

		self._map= map
		self._b= _b.value
	def refas( self, offset, tp ):
		c= cast( self._b+ offset, POINTER( tp ) )
		return c.contents

from ctypes import *
prototype= PYFUNCTYPE( c_int, py_object, POINTER(c_void_p), POINTER(c_uint) )
PyObject_AsWriteBuffer= prototype( ( "PyObject_AsWriteBuffer", pythonapi ) )
def refas( buf, offset, tp ):
	''' return an instance of |tp| that refers to |offset| bytes into buffer |buf| '''
	_b, _s= c_void_p(0), c_uint(0)
	PyObject_AsWriteBuffer( buf, byref(_b), byref(_s) )
	c= cast( _b.value+ offset, POINTER( tp ) )
	return c.contents

def create( file, size, access= mmap.ACCESS_WRITE ):
	builtinopen( file, 'w+b' )
	f= builtinopen( file, 'r+b' )
	m= mmap.mmap( f.fileno( ), size, access= access )
	pm= perstmap( m )
	return pm

def open( file, access= mmap.ACCESS_WRITE ):
	f=  builtinopen( file, 'r+b' )
	m= mmap.mmap( f.fileno( ), 0, access= access )
	pm= perstmap( m )
	return pm

'''
PyObject_AsWriteBuffer = ctypes.pythonapi.PyObject_AsWriteBuffer
PyObject_AsWriteBuffer.restype = ctypes.c_int
PyObject_AsWriteBuffer.argtypes = [ctypes.py_object,
                                   ctypes.POINTER(ctypes.c_void_p),
                                   ctypes.POINTER(Py_ssize_t)]
'''