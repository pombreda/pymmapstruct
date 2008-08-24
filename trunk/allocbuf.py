'''
0 nil
4 max
8 record
12 root
16... open
'''

'''
used     used
size     size
left     .
right    .
parent   .
balance  .
.        .
.        .
.        .
self     self
'''

'''
'add_at' and 'remove_at' adapted from GNU PAVL library.
'''

word= 4
class Buffer(object):
	def setI( self, offt, val ): raise NotImplemented
	def getI( self, offt ): raise NotImplemented
	def seti( self, offt, val ): raise NotImplemented
	def geti( self, offt ): raise NotImplemented
	def print_( self ): raise NotImplemented

class Node(object):
	lookup= { 'key': 0* word, 'left': 1* word, 'right': 2* word, 'parent': 3* word, 'balance': 4* word }
	class Link( object ):
		__slots__= 'where', '_tree'
		def __init__( self, where, tree ):
			self.where, self._tree= where, tree
		def __getitem__( self, key ):
			if key:
				return self._tree[ self.where ].right
			else:
				return self._tree[ self.where ].left
		def __setitem__( self, key, val ):
			if key:
				self._tree[ self.where ].right= val
			else:
				self._tree[ self.where ].left= val
	class PLink( object ):
		__slots__= 'where', '_tree'
		def __init__( self, where, tree ):
			self.where, self._tree= where, tree
		def __getitem__( self, key ):
			if key:
				return self._tree[ self._tree[ self.where ].right ]
			else:
				return self._tree[ self._tree[ self.where ].left ]
		def __setitem__( self, key, val ):
			if key:
				self._tree[ self.where ].right= val.where
			else:
				self._tree[ self.where ].left= val.where

	__slots__= 'where', '_tree'
	def __init__( self, where, tree ):
		self.where, self._tree= where, tree

	class Null:
		where= 0

	def __nonzero__( self ):
		return self.where!= 0
	
	def __eq__( self, other ):
		return self.where== other.where
	
	def __ne__( self, other ):
		return self.where!= other.where
	
	def _getkey( self ): #limited to one-word key.  override to access.
		return self._tree.getI(
			self.where+ self.lookup[ 'key' ] )
	def _setkey( self, val ):
		self._tree.setI(
			self.where+ self.lookup[ 'key' ], val )
	key= property( _getkey, _setkey )

	def _getleft( self ):
		return self._tree.getI(
			self.where+ self.lookup[ 'left' ] )
	def _setleft( self, val ):
		self._tree.setI(
			self.where+ self.lookup[ 'left' ], val )
	left= property( _getleft, _setleft )

	def _getright( self ):
		return self._tree.getI(
			self.where+ self.lookup[ 'right' ] )
	def _setright( self, val ):
		self._tree.setI(
			self.where+ self.lookup[ 'right' ], val )
	right= property( _getright, _setright )

	def _getlink( self ):
		return self.link( self.where, self._tree )
	link= property( _getlink )

	def _getplink( self ):
		return self.PLink( self.where, self._tree )
	plink= property( _getplink )

	def _getparent( self ):
		return self._tree.getI(
			self.where+ self.lookup[ 'parent' ] )
	def _setparent( self, val ):
		self._tree.setI(
			self.where+ self.lookup[ 'parent' ], val )
	parent= property( _getparent, _setparent )

	def _getpparent( self ):
		return self._tree[ self.parent ]
	def _setpparent( self, val ):
		self.parent= val.where
	pparent= property( _getpparent, _setpparent )

	def _getbalance( self ):
		return self._tree.geti(
			self.where+ self.lookup[ 'balance' ] )
	def _setbalance( self, val ):
		self._tree.seti(
			self.where+ self.lookup[ 'balance' ], val )
	balance= property( _getbalance, _setbalance )


class AdjNode( Node ):
	lookup= { 'prevkey': -1* word, 'used': 0, 'key': 1* word,
					'left': 2* word, 'right': 3* word, 'parent': 4* word, 'balance': 5* word }
	__slots__= 'where', '_tree'

	def _getprevkey( self ):
		return self._tree.getI( self.prevwhere )
	prevkey= property( _getprevkey )

	def _getprevwhere( self ):
		return self.where+ self.lookup[ 'prevkey' ]
	prevwhere= property( _getprevwhere )
	
	def _getused( self ):
		return self._tree.getI(
			self.where+ self.lookup[ 'used' ] )
	def _setused( self, val ):
		self._tree.setI(
			self.where+ self.lookup[ 'used' ], val )
	used= property( _getused, _setused )

	def _getfoot( self ):
		return self.where+ self.key+ 2* word
	def _setfoot( self, val ):
		self._tree.setI( self.foot, val )
	foot= property( _getfoot, _setfoot )
	
	def _getnext( self ):
		return self.__class__( self.foot+ 1* word, self._tree )
	next= property( _getnext )

	def _getprev( self ):
		return self.__class__( self.prevkey, self._tree )
	prev= property( _getprev )

class BufferTree( Buffer ):
	class RootProxy:
		__slots__= '_tree'
		class RootLink:
			__slots__= '_tree'
			def __init__( self, tree ):
				self._tree= tree
			def __getitem__( self, key ):
				assert key== 0
				return self._tree.root
			def __setitem__( self, key, val ):
				assert key== 0
				self._tree.root= val
		class RootPLink:
			__slots__= '_tree'
			def __init__( self, tree ):
				self._tree= tree
			def __getitem__( self, key ):
				assert key== 0
				return self._tree.proot
			def __setitem__( self, key, val ):
				assert key== 0
				self._tree.proot= val
		def __init__( self, tree ):
			self._tree= tree
		#delegate 'left' to 'self._tree'
		def _getleft( self ):
			return self._tree.root
		def _setleft( self, val ):
			self._tree.proot= val
		left= property( _getleft, _setleft )
		def _getlink( self ):
			return self.RootLink( self._tree )
		link= property( _getlink )
		def _getplink( self ):
			return self.RootPLink( self._tree )
		plink= property( _getplink )

	def __init__( self, rootaddr ):
		self._rootaddr= rootaddr

	def __getitem__( self, where ):
		return Node( where, self )

	def _getsize( self ):
		return self.getI( self.sizeaddr )
	size= property( _getsize )
	
	def _getroot( self ):
		return self.getI( self._rootaddr )
	def _setroot( self, val ):
		self.setI( self._rootaddr, val )
	root= property( _getroot, _setroot )

	def _getproot( self ):
		return self[ self.root ]
	def _setproot( self, val ):
		self.root= val.where
	proot= property( _getproot, _setproot )

	def _getrecord( self ):
		return self.getI( self.recordaddr )
	def _setrecord( self, record ):
		self.setI( self.recordaddr, record )
	record= property( _getrecord, _setrecord )

	def _getproxy( self ):
		return self.RootProxy( self )
	proxy= property( _getproxy )
	
	def compare( self, key1, key2 ):
		if key1< key2:
			return -1
		if key1== key2:
			return 0
		return 1

	def add_at( self, where, key ):
		''' add a free node at address where, size key '''
		#print 'add_at', where, key
		y= p= q= n= w= Node.Null
		dir= 0
		
		y= self.proot
		q, p= Node.Null, self.proot
		while p!= Node.Null:
			cmp= self.compare( key, p.key )

			dir= cmp>= 0

			if p.balance!= 0:
				y= p

			q, p= p, p.plink[ dir ]
		
		n= self[ where ]

		n.plink[ 0 ]= n.plink[ 1 ]= Node.Null
		n.pparent= q
		n.key= key
		if q!= Node.Null:
			q.plink[ dir ]= n
		else:
			self.proot= n
		n.balance= 0
		if self.proot== n:
			return
		
		p= n
		while p!= y:
			q= p.pparent
			dir= q.plink[ 0 ]!= p
			if dir== 0:
				q.balance-= 1
			else:
				q.balance+= 1
			p= q
		
		if y.balance== -2:
			x= y.plink[ 0 ]
			if x.balance== -1:
				w= x
				y.plink[ 0 ]= x.plink[ 1 ]
				x.plink[ 1 ]= y
				x.balance= y.balance= 0
				x.pparent= y.pparent
				y.pparent= x
				if y.plink[ 0 ]!= Node.Null:
					y.plink[ 0 ].pparent= y
			else:
				assert x.balance== 1
				w= x.plink[ 1 ]
				x.plink[ 1 ]= w.plink[ 0 ]
				w.plink[ 0 ]= x
				y.plink[ 0 ]= w.plink[ 1 ]
				w.plink[ 1 ]= y
				if w.balance== -1:
					x.balance, y.balance= 0, 1
				elif w.balance== 0:
					x.balance= y.balance= 0
				else:
					x.balance, y.balance= -1, 0
				w.balance= 0
				w.pparent= y.pparent
				x.pparent= y.pparent= w
				if x.plink[ 1 ]!= Node.Null:
					x.plink[ 1 ].pparent= x
				if y.plink[ 0 ]!= Node.Null:
					y.plink[ 0 ].pparent= y
		elif y.balance== 2:
			x= y.plink[ 1 ]
			if x.balance== 1:
				w= x
				y.plink[ 1 ]= x.plink[ 0 ]
				x.plink[ 0 ]= y
				x.balance= y.balance= 0
				x.pparent= y.pparent
				y.pparent= x
				if y.plink[ 1 ]!= Node.Null:
					y.plink[ 1 ].pparent= y
			else:
				assert x.balance== -1
				w= x.plink[ 0 ]
				x.plink[ 0 ]= w.plink[ 1 ]
				w.plink[ 1 ]= x
				y.plink[ 1 ]= w.plink[ 0 ]
				w.plink[ 0 ]= y
				if w.balance== 1:
					x.balance, y.balance= 0, -1
				elif w.balance== 0:
					x.balance= y.balance= 0
				else:
					x.balance, y.balance= 1, 0
				w.balance= 0
				w.pparent= y.pparent
				x.pparent= y.pparent= w
				if x.plink[ 0 ]!= Node.Null:
					x.plink[ 0 ].pparent= x
				if y.plink[ 1 ]!= Node.Null:
					y.plink[ 1 ].pparent= y
		else:
			return
		if w.pparent!= Node.Null:
			w.pparent.plink[ y!= w.pparent.plink[ 0 ] ]= w
		else:
			self.proot= w

	def remove_at( self, where ):
		''' consume the free node at address where '''
		#print 'remove at', where

		p= self[ where ]
		dir= 0

		if self.proot== Node.Null:
			raise KeyError
		
		if p.pparent!= Node.Null and p.pparent.plink[ 1 ]== p:
			dir= 1

		q= p.pparent
		if q== Node.Null:
			q= self.proxy
			dir= 0
		
		if p.plink[ 1 ]== Node.Null:
			q.plink[ dir ]= p.plink[ 0 ]
			if q.plink[ dir ]!= Node.Null:
				q.plink[ dir ].pparent= p.pparent
		else:
			r= p.plink[ 1 ]
			if r.plink[ 0 ]== Node.Null:
				r.plink[ 0 ]= p.plink[ 0 ]
				q.plink[ dir ]= r
				r.pparent= p.pparent
				if r.plink[ 0 ]!= Node.Null:
					r.plink[ 0 ].pparent= r
				r.balance= p.balance
				q= r
				dir= 1
			else:
				s= r.plink[ 0 ]
				while s.plink[ 0 ]!= Node.Null:
					s= s.plink[ 0 ]
				r= s.pparent
				r.plink[ 0 ]= s.plink[ 1 ]
				s.plink[ 0 ]= p.plink[ 0 ]
				s.plink[ 1 ]= p.plink[ 1 ]
				q.plink[ dir ]= s
				if s.plink[ 0 ]!= Node.Null:
					s.plink[ 0 ].pparent= s
				s.plink[ 1 ].pparent= s
				s.pparent= p.pparent
				if r.plink[ 0 ]!= Node.Null:
					r.plink[ 0 ].pparent= r
				s.balance= p.balance
				q= r
				dir= 0

		breakflag= isinstance( q, self.RootProxy )
		while not breakflag:
			y= q

			if y.pparent!= Node.Null:
				q= y.pparent
			else:
				breakflag= True
				q= self.proxy
			
			if dir== 0:
				dir= q.plink[ 0 ]!= y
				y.balance+= 1
				if y.balance== 1:
					break
				elif y.balance== 2:
					x= y.plink[ 1 ]
					if x.balance== -1:
						assert x.balance== -1
						w= x.plink[ 0 ]
						x.plink[ 0 ]= w.plink[ 1 ]
						w.plink[ 1 ]= x
						y.plink[ 1 ]= w.plink[ 0 ]
						w.plink[ 0 ]= y
						if w.balance== 1:
							x.balance, y.balance= 0, -1
						elif w.balance== 0:
							x.balance= y.balance= 0
						else:
							x.balance, y.balance= 1, 0
						w.balance= 0
						w.pparent= y.pparent
						x.pparent= y.pparent= w
						if x.plink[ 0 ]!= Node.Null:
							x.plink[ 0 ].pparent= x
						if y.plink[ 1 ]!= Node.Null:
							y.plink[ 1 ].pparent= y
						q.plink[ dir ]= w
					else:
						y.plink[ 1 ]= x.plink[ 0 ]
						x.plink[ 0 ]= y
						x.pparent= y.pparent
						y.pparent= x
						if y.plink[ 1 ]!= Node.Null:
							y.plink[ 1 ].pparent= y
						q.plink[ dir ]= x
						if x.balance== 0:
							x.balance= -1
							y.balance= 1
							break
						else:
							x.balance= y.balance= 0
							y= x
			else:
				dir= q.plink[ 0 ]!= y
				y.balance-= 1
				if y.balance== -1:
					break
				elif y.balance== -2:
					x= y.plink[ 0 ]
					if x.balance== 1:
						assert x.balance== 1
						w= x.plink[ 1 ]
						x.plink[ 1 ]= w.plink[ 0 ]
						w.plink[ 0 ]= x
						y.plink[ 0 ]= w.plink[ 1 ]
						w.plink[ 1 ]= y
						if w.balance== -1:
							x.balance, y.balance= 0, 1
						elif w.balance== 0:
							x.balance= y.balance= 0
						else:
							x.balance, y.balance= -1, 0
						w.balance= 0
						w.pparent= y.pparent
						x.pparent= y.pparent= w
						if x.plink[ 1 ]!= Node.Null:
							x.plink[ 1 ].pparent= x
						if y.plink[ 0 ]!= Node.Null:
							y.plink[ 0 ].pparent= y
						q.plink[ dir ]= w
					else:
						y.plink[ 0 ]= x.plink[ 1 ]
						x.plink[ 1 ]= y
						x.pparent= y.pparent
						y.pparent= x
						if y.plink[ 0 ]!= Node.Null:
							y.plink[ 0 ].pparent= y
						q.plink[ dir ]= x
						if x.balance== 0:
							x.balance= 1
							y.balance= -1
							break
						else:
							x.balance= y.balance= 0
							y= x

	def has_key( self, key ):
		pass

class AllocTree( BufferTree ):
	nil= 0
	sizeaddr= 1* word
	recordaddr= 2* word
	rootaddr= 3* word
	mapheadsize= 4* word

	class AllocException( Exception ): pass

	def __getitem__( self, where ):
		return AdjNode( where, self )

	def __init__( self ):
		super( AllocTree, self ).__init__( AllocTree.rootaddr )

	def _where_smallest_gte( self, size ):
		cur= self.root
		best, bestsize= None, None
		while cur:
			cursize= self[ cur ].key
			if size== cursize:
				best, bestsize= cur, cursize
				break
			elif cursize> size:
				if best is None or cursize< bestsize:
					best, bestsize= cur, cursize
				cur= self[ cur ].left
			else:
				cur= self[ cur ].right
		return best
		
	def alloc( self, size ):
		#print 'alloc', size
		size= max( size, 4* word )
		where= self._where_smallest_gte( size )
		if where is None:
			raise AllocTree.AllocException()

		self.remove_at( where )

		oldsize= self[ where ].key
		if oldsize>= size+ 7* word:
			self[ where ].key= size
			self[ where ].foot= where
			self.add_at( self[ where ].next.where, oldsize- size- 3* word )

		return where+ 2* word

	def realloc( self, where, size ):
		raise

	def free( self, where ):
		#print 'free', where
		_joinprev, _joinnext= True, True
		where-= 2* word
		if self[ where ].prevwhere< self.mapheadsize or self[ where ].prev.used:
			_joinprev= False
		if self[ where ].next.where>= self.map.size() or self[ where ].next.used:
			_joinnext= False

		newkey= self[ where ].key
		newwhere= where
		if _joinprev:
			self.remove_at( self[ where ].prev.where )
			newkey+= self[ where ].prev.key+ 3* word
			newwhere= self[ where ].prev.where
		if _joinnext:
			self.remove_at( self[ where ].next.where )
			newkey+= self[ where ].next.key+ 3* word
		self.add_at( newwhere, newkey )

	def add_at( self, where, key ):
		super( AllocTree, self ).add_at( where, key )
		assert key>= 4* word
		self[ where ].used= 0
		self[ where ].foot= where

	def remove_at( self, where ):
		super( AllocTree, self ).remove_at( where )
		self[ where ].used= 1

class CheckingTree( AllocTree ):
	def print_( self ):
		i= 0
		for x in self._data:
			print '%4i:%3i   '% (i,x),
			i+= 1
			if i% 4== 0:
				print
	def print_list( self ):
		def print_rec( where, spaces ):
			if not where:
				print ' '* spaces, '-'
				return
			print ' '* spaces, self[ where ].key, '@', where, '%+i'% self[ where ].balance
			print_rec( self[ where ].left, spaces+ 2 )
			print_rec( self[ where ].right, spaces+ 2 )
		print_rec( self.root, 0 )
	def list_io( self ):
		def list_io_rec( where ):
			ret= []
			if not where: return ret
			ret.extend( list_io_rec( self[ where ].left ) )
			ret.append( self[ where ].key )
			ret.extend( list_io_rec( self[ where ].right ) )
			return ret
		return list_io_rec( self.root )
	def print_used( self ):
		n= self.root
		while n.where< self.size():
			assert self.getI( n.foot )== n.where
			if not n.used:
				if n.right: assert self[ n.right ].parent== n.where
				if n.left: assert self[ n.left ].parent== n.where
				if n.parent: assert n.where in [ self[ n.parent ].right, self[ n.parent ].left ]
			n= n.next
		io= self.list_io()
		assert io== sorted( io )
	def check_used( self, n= None ):
		if n is None:
			n= self.root
		if n== 0:
			return
		def height_rec( where ):
			if not where: return 0
			lheight= height_rec( self[ where ].left )
			rheight= height_rec( self[ where ].right )
			return 1 + max(lheight, rheight)
		lheight= height_rec( self[ n ].left )
		rheight= height_rec( self[ n ].right )
		#print n, self[ n ].balance, rheight, lheight
		assert self[ n ].balance== rheight- lheight
		if self[ n ].left:
			assert self[ self[ n ].left ].parent== n
		if self[ n ].right:
			assert self[ self[ n ].right ].parent== n
		self.check_used( self[ n ].left )
		self.check_used( self[ n ].right )

import mmap
import struct
packI= struct.Struct( 'I' )
packi= struct.Struct( 'i' )

class MmapAllocTree( CheckingTree ):
	def __init__( self, map ):
		self.map= map
		super( MmapAllocTree, self ).__init__( )
	def setI( self, offt, val ):
		#print self.map.size(), offt, val
		assert type( val )== int
		packI.pack_into( self.map, offt, val )
	def getI( self, offt ):
		#print self.map.size(), offt
		return packI.unpack_from( self.map, offt )[ 0 ]
	def seti( self, offt, val ):
		#print self.map.size(), offt, val
		assert type( val )== int
		packi.pack_into( self.map, offt, val )
	def geti( self, offt ):
		#print self.map.size(), offt
		return packi.unpack_from( self.map, offt )[ 0 ]
	@classmethod
	def open( cls, file, access= mmap.ACCESS_WRITE ):
		f= open( file, 'r+b' )
		m= mmap.mmap( f.fileno( ), 0, access= access )
		mm= cls( m )
		mm.f= f
		return mm
	@classmethod
	def createNB( cls, file, size, access= mmap.ACCESS_WRITE ):
		open( file, 'w+b' )
		f= open( file, 'r+b' )
		m= mmap.mmap( f.fileno( ), size, access= access )
		mm= cls( m )
		mm.f= f
		return mm
	@classmethod
	def create( cls, file, size, access= mmap.ACCESS_WRITE ):
		mm= cls.createNB( file, size, access= access )
		mm.setI( mm.sizeaddr, mm.map.size( ) ) 
		mm.add_at( mm.mapheadsize, mm.map.size( )- mm.mapheadsize- 3* word )
		return mm
	def flush( self ):
		self.map.flush( )
	def close( self ):
		self.map.close( )
		self.map= None
		self.f.close( )
		del self.f

if 0:
	#shared write
	import time

	def th_w( ):
		mt= MmapAllocTree.createNB( 'mappedtree.dat', 3000 )
		j= 0
		base= mt.mapheadsize 
		while 1:
			for i in range( 0, 1000, word ):
				mt.setI( i+ base, j )
			time.sleep( .1 )
			j+= 1
			mt.flush( )
		
	def th_r( ):
		mt= MmapAllocTree.open( 'mappedtree.dat', mmap.ACCESS_READ )
		j= 0
		base= mt.mapheadsize 
		while 1:
			for i in range( 0, 1000, 100 ):
				print mt.getI( i+ base ),
			print
			time.sleep( .1 )
	
	import thread
	thread.start_new_thread( th_w, () )
	time.sleep( .1 )
	th_r( )
			

if 0:
	def insert_stress():
		while 1:
			print '======================='
			mt= MmapAllocTree.createNB( 'mappedtree.dat', 3000 )
			i= 100
			seq= [ 10, 11, 13, 17, 33, 43, 65, 72, 85, 93, 107, 113, 120 ]
			import random as ran
			ran.shuffle( seq )

			while i< 2800:
				x= ran.randint( 16, 100 )
				mt.add_at( i, x )
				mt.print_list()
				mt.check_used()
				i+= 30
			mt.close()
	insert_stress()

def stress():
	import random as ran
	mems= set( )
	_recordlimit= 100
	if 1:
		mt= MmapAllocTree.create( 'mappedtree.dat', 3000 )
		mt.record= mt.alloc( _recordlimit* word )
	else:
		mt= MmapAllocTree.open( 'mappedtree.dat' )
		print 'cache',
		for i in range( mt.getI( mt.record ) ):
			print i, mt.getI( mt.record+ word* i+ word ),
			mems.add( mt.getI( mt.record+ word* i+ word ) )
		print

	log= open( 'mappedtree.txt', 'w' )
	for count in range( 10000 ):#while 1:
		print len( mems ),

		mt.check_used()
		#mt.print_list()
		#print mt.list_io()
		if ran.choice( ( 0, 1 ) ) and mems or len( mems )+ 2> _recordlimit:
			where= ran.choice( list( mems ) )
			#print 'free',where, mt[where-2* word].key
			#log.write( 'mt.free( %i )\n'% where )
			log.flush()
			mt.free( where )
			mems.remove( where )
		else:
			size= ran.randint( 5, 100 )
			#print 'alloc', size
			try:
				#log.write( 'mt.alloc( %i )\n'% size )
				log.flush()
				where= mt.alloc( size )
				mems.add( where )
			except AllocTree.AllocException:
				print 'insufficient',
				#log.write( 'insufficient\n' )
				log.flush()
				pass

	mt.setI( mt.record, len( mems ) )
	print
	print 'cache',
	for i, x in enumerate( mems ):
		print i, x,
		mt.setI( word* i+ mt.record+ word, x )
	print
	mt.flush()
	mt.close()

if 1 and __name__== '__main__':
	import profile
	#profile.run( 'stress()' )
	stress( )

