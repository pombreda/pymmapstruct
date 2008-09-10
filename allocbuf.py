'''
In-buffer dynamic-allocation module, providing 'alloc' and 'free' service to
generic buffers with an implementation on memory-mapped files.

If you are unfamiliar with dynamic memory allocation, read an article from:
	http://www.google.com/search?q=dynamic+memory+allocation
'alloc' and 'free' are established terms and concepts with established applications
and needs.  'allocbuf' merely provides them to a buffer "in-place", so that its
allocation (metadata) state is carried along in the buffer, and allocations can be
made and freed on non-initial uses.

Distinguish from maintaining metadata in memory, and allocating from a buffer based
on that.  Then, while the buffer correctly does not overlap blocks, its structure
is meaningless after freeing the metadata.

Further distinguish from recording the metadata in a separate block in the file,
which would require loading the entire structure into memory before making any
changes or useful queries to it.  Instead, store it in place, in the vicinity
of the free and used nodes.  Then, merely search the tree for a new node or to
replace it; its structure is already active, live, and valid.
'''

'''
File head:
word 0 nil
word 1 max
word 2 record
word 3 root
word 4... rest
'''

'''
Node structure:
Unused | Used:
used     used
size     size
left     .    ]
right    .    ]
parent   .    ]
balance  .    ] <---- size/key # of bytes
.        .    ]
.        .    ]
.        .    ]
self     self   <---- contains address of top of node
'''

'''
'add_at' and 'remove_at' adapted from GNU PAVL library.  freenode
size is the key used to sort on.  size is expected size in bytes
after allocation, not size of whole node.
'''

import struct
packI= struct.Struct( 'I' )
packi= struct.Struct( 'i' )
word= 4
packI= struct.Struct( 'H' )
packi= struct.Struct( 'h' )
word= 2

class Buffer(object):
	'''Abstract base class, probably not necessary.

	'mmap' is one known specialization, others may implement set/geti/I in other ways
	
	'''
	def setI( self, offt, val ): raise NotImplemented
	def getI( self, offt ): raise NotImplemented
	def seti( self, offt, val ): raise NotImplemented
	def geti( self, offt ): raise NotImplemented
	def print_( self ): raise NotImplemented

class Node(object):
	'''ctypes substitute for accessing bytes.'''
	lookup= { 'key': 0* word, 'left': 1* word, 'right': 2* word, 'parent': 3* word, 'balance': 4* word }
	class Link( object ):
		'''adapter to substitute 'link[0]' and 'link[1]' for 'left' and 'right' '''
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
		''' object adapter for Link class, returns Node instances instead of offsets '''
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
	
	def _getkey( self ): #limited to one-word integral key.  override to access.
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
		''' substitute index access for 'left' and 'right' attributes '''
		return self.Link( self.where, self._tree )
	link= property( _getlink )

	def _getplink( self ):
		''' object adapter, returns Node instances instead of offsets '''
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
		''' object adapter, returns Node instances instead of offsets '''
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
	''' additional properties to access 'top' footer of buffer-prior node,
	'used' field, buffer-next node '''
	lookup= { 'prevkey': -1* word, 'used': 0, 'key': 1* word,
					'left': 2* word, 'right': 3* word, 'parent': 4* word, 'balance': 5* word }
	__slots__= 'where', '_tree'

	def _getprevkey( self ):
		''' get previous footer value, which is its top / address of node it's the foot of '''
		return self._tree.getI( self.prevwhere )
	prevkey= property( _getprevkey )

	def _getprevwhere( self ):
		''' previous footer address '''
		return self.where+ self.lookup[ 'prevkey' ]
	prevwhere= property( _getprevwhere )
	
	def _getused( self ):
		''' zero for unused (has left, right, parent, balance; non-zero for used '''
		return self._tree.getI(
			self.where+ self.lookup[ 'used' ] )
	def _setused( self, val ):
		self._tree.setI(
			self.where+ self.lookup[ 'used' ], val )
	used= property( _getused, _setused )

	def _getfoot( self ):
		''' slight asymmetry; get returns address of foot; set sets value *at* foot '''
		return self.where+ self.key+ 2* word
	def _setfoot( self, val ):
		self._tree.setI( self.foot, val )
	foot= property( _getfoot, _setfoot )
	
	def _getnext( self ):
		''' next node is located at self.foot + 1* word == self.where + self.key+ 2* word+ 1* word'''
		return self.__class__( self.foot+ 1* word, self._tree )
	next= property( _getnext )

	def _getprev( self ):
		''' previous object, located at self.prevkey, or value at location self.prevwhere '''
		return self.__class__( self.prevkey, self._tree )
	prev= property( _getprev )

class BufferTree( Buffer ):
	''' tree class with 'add_at' and 'remove_at' methods, and buffer header information.  see:
			http://www.stanford.edu/~blp/avl/libavl.html/index.html#toc_AVL-Trees-with-Parent-Pointers
		(excellent algorithm with docs, lots of hard work)
	'''
	class RootProxy:
		''' for uniform access to root node / parent of root, and when tree is empty.
		only child pointer accessed is 'left', as specified in GNU algorithm.  conforms to
		Node interface only for 'left', 'link[0]', and 'plink[0]' properties. '''
		__slots__= '_tree'
		class RootLink:
			''' proxy root with root.parent.left, returns location '''
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
			''' same, returns node '''
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
		def _getleft( self ):
			''' delegate 'left' to 'self._tree' '''
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
		''' magic property: create a non-buffer / heap / external Node about a particular offset into buffer '''
		return Node( where, self )

	def _getsize( self ):
		''' size of buffer (or node size) '''
		return self.getI( self.sizeaddr )
	size= property( _getsize )
	
	def _getroot( self ):
		''' freetree node root '''
		return self.getI( self._rootaddr )
	def _setroot( self, val ):
		self.setI( self._rootaddr, val )
	root= property( _getroot, _setroot )

	def _getproot( self ):
		''' Node object at root '''
		return self[ self.root ]
	def _setproot( self, val ):
		self.root= val.where
	proot= property( _getproot, _setproot )

	def _getrecord( self ):
		''' dogear one location between accesses '''
		return self.getI( self.recordaddr )
	def _setrecord( self, record ):
		self.setI( self.recordaddr, record )
	record= property( _getrecord, _setrecord )

	def _getproxy( self ):
		''' proxy of parent of root, slight misnomer '''
		return self.RootProxy( self )
	proxy= property( _getproxy )
	
	def compare( self, key1, key2 ):
		if key1< key2:
			return -1
		if key1== key2:
			return 0
		return 1

	def add_at( self, where, key ):
		''' add a free node at address: where, size: key and rebalance tree.  comments see:
				http://www.stanford.edu/~blp/avl/libavl.html/Inserting-into-a-PAVL-Tree.html
		'''
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
		''' consume the free node at address where.  comments see:
				http://www.stanford.edu/~blp/avl/libavl.html/Deleting-from-a-PAVL-Tree.html
			note: 'remove_at' omits 'find' step.
		'''
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

		breakflag= isinstance( q, self.RootProxy ) #slight deviation, avoids 'isinstance' test
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

class AllocTree( BufferTree ):
	'''
	'nil' is reserved and must be at address 0 with value 0.
	'root' is location of root of freenode tree.
	'max' is size'
	'record' is user-defined field for storing one address between sessions.  set and query
	this field for an initial known location.  (you only get to remember one location.)
	
	open memory starts after the header, excluding the node head there.  first 'alloc' from
	a brand new buffer will be at 'tree size' + 'used node head size'

	tree analogue to a 'free list': a 'freetree'.

	'''
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
		''' custom find step prior to 'remove_at' '''
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
		''' remove the node, add remainder if big enough '''
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
		''' add the node, joining prior and/or next if also free '''
		#print 'free', where
		_joinprev, _joinnext= True, True
		where-= 2* word
		if self[ where ].prevwhere< self.mapheadsize or self[ where ].prev.used:
			_joinprev= False
		if self[ where ].next.where>= self.map.size() or self[ where ].next.used:
			_joinnext= False

		newkey= self[ where ].key
		newwhere= where
		if _joinprev: # join prior
			self.remove_at( self[ where ].prev.where )
			newkey+= self[ where ].prev.key+ 3* word
			newwhere= self[ where ].prev.where
		if _joinnext: # join next
			self.remove_at( self[ where ].next.where )
			newkey+= self[ where ].next.key+ 3* word
		self.add_at( newwhere, newkey )

	def add_at( self, where, key ):
		''' small specialization of add_at '''
		super( AllocTree, self ).add_at( where, key )
		assert key>= 4* word
		self[ where ].used= 0
		self[ where ].foot= where

	def remove_at( self, where ):
		''' small specialization of remove_at '''
		super( AllocTree, self ).remove_at( where )
		self[ where ].used= 1

class CheckingTree( AllocTree ):
	''' debugging, integrity, and print routines '''
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
		''' rather strong and lengthy integrity check '''
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
import os
class MmapAllocTree( CheckingTree ):
	''' specialization of AllocTree into mmap '''
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
	@staticmethod
	def lenS( val ):
		''' calculate space needed for length-preceded strings '''
		return len( val )+ word
	def setS( self, offt, val ):
		''' additional for packing length-preceded strings '''
		assert type( val )== str
		self.setI( offt, len( val ) )
		self.map[ offt+ word: offt+ word+ len( val ) ]= val
	def getS( self, offt ):
		len_= self.getI( offt )
		return self.map[ offt+ word: offt+ word+ len_ ]
	@classmethod
	def open( cls, file, access= mmap.ACCESS_WRITE ):
		f= os.open( file, os.O_RDWR ) #O_BINARY? O_RANDOM?
		m= mmap.mmap( f, 0, access= access )
		mm= cls( m )
		mm.f= f
		return mm
	@classmethod
	def createNB( cls, file, size, access= mmap.ACCESS_WRITE ):
		''' create without default whole-file block, poss. for testing '''
		f= os.open( file, os.O_RDWR| os.O_CREAT| os.O_TRUNC ) #O_BINARY? O_RANDOM?
		m= mmap.mmap( f, size, access= access )
		mm= cls( m )
		mm.f= f
		return mm
	@classmethod
	def create( cls, file, size, access= mmap.ACCESS_WRITE ):
		''' create and add default whole-file block to freetree '''
		mm= cls.createNB( file, size, access= access )
		mm.setI( mm.sizeaddr, mm.map.size( ) ) 
		mm.add_at( mm.mapheadsize, mm.map.size( )- mm.mapheadsize- 3* word )
		return mm
	def flush( self ):
		self.map.flush( )
	def close( self ):
		self.map.close( )
		self.map= None
		#self.f.close( )
		os.close( self.f )
		del self.f

'''test suite of 4 functions.  recommend useful_test.'''

def concurrency_test( ):
	''' test concurrency integrity of mmap, multiple unsynchronized writers '''
	import time

	def th_w( ix= 0 ):
		if ix== 0:
			mt= MmapAllocTree.createNB( 'mappedtree.dat', 3000 )
		else:
			mt= MmapAllocTree.open( 'mappedtree.dat' )
		j= 0
		base= mt.mapheadsize
		while 1:
			for i in range( ix* word, 1000, 3* word ):
				mt.setI( i+ base, j )
			time.sleep( .05 )
			j+= 1
			mt.flush( )
		
	def th_r( ):
		mt= MmapAllocTree.open( 'mappedtree.dat' )
		j= 0
		base= mt.mapheadsize 
		while 1:
			for i in range( 0, 1000, 100 ):
				print mt.getI( i+ base ),
			print
			time.sleep( .1 )
	
	import thread
	thread.start_new_thread( th_w, ( 0, ) )
	time.sleep( .1 )
	thread.start_new_thread( th_w, ( 1, ) )
	time.sleep( .1 )
	thread.start_new_thread( th_w, ( 2, ) )
	time.sleep( .1 )
	th_r( )
#concurrency_test( )			

def insert_stress():
	''' test of add_at.  insert nodes, assuming size 30, until file is full.'''
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
#insert_stress()

def stress():
	''' stress-test alloc/free.  randomly choose either alloc of random size (if
	below record limit) or free (if any are allocated).  loop 10000 times (ten seconds).
	store up to 100 offsets that have been allocated + count.
	optionally reopen file on second run, read count + list of offsets, and run
	10000 more.
	'''
	import random as ran
	mems= set( ) #external store of what offsets are currently allocated
	_recordlimit= 100
	import time
	print time.clock( )
	if 1: #change to if '0' to set to 'reopen', not 'create'
		#create a file, plus allocate space to store 100 offsets between runs
		mt= MmapAllocTree.create( 'mappedtree.dat', 3000 )
		mt.record= mt.alloc( _recordlimit* word )
	else:
		#open and print existing 'cache' of offsets that were stored previously
		mt= MmapAllocTree.open( 'mappedtree.dat' )
		print 'cache',
		for i in range( mt.getI( mt.record ) ):
			print i, mt.getI( mt.record+ word* i+ word ),
			mems.add( mt.getI( mt.record+ word* i+ word ) )
		print

	#log= open( 'mappedtree.txt', 'w' )
	for count in range( 10000 ):#while 1:
		print len( mems ), #print current count of allocation

		mt.check_used()
		#mt.print_list()
		#print mt.list_io()
		if ran.choice( ( 0, 1 ) ) and mems or len( mems )+ 2> _recordlimit:
			where= ran.choice( list( mems ) )
			#print 'free',where, mt[where-2* word].key
			#log.write( 'mt.free( %i )\n'% where )
			#log.flush()
			mt.free( where )
			mems.remove( where )
		else:
			size= ran.randint( 5, 100 )
			#print 'alloc', size
			try:
				#log.write( 'mt.alloc( %i )\n'% size )
				#log.flush()
				where= mt.alloc( size )
				mems.add( where )
			except AllocTree.AllocException:
				print 'insufficient',
				#log.write( 'insufficient\n' )
				#log.flush()
				pass

	#record cache for valid persistivity
	mt.setI( mt.record, len( mems ) )
	print
	print 'cache',
	for i, x in enumerate( mems ):
		print i, x,
		mt.setI( word* i+ mt.record+ word, x )
	print
	mt.flush()
	mt.close()
	print time.clock( ) #10 seconds on author's run
#stress( )

def useful_test( ):
	import random as ran
	mt= MmapAllocTree.create( 'mappedtree.dat', 3000 )
	aL= 4* word
	a= mt.alloc( aL ) #array of 4 words
	mt.record= a #pointer to our structure in the file
	for i in range( 4 ):
		mt.setI( a+ i* word, i ) #calculate position by hand
	mt.close( )

	mt= MmapAllocTree.open( 'mappedtree.dat' ) #reopen
	a= mt.record
	bL= 8* word
	b= mt.alloc( bL ) #allocate more (realloc service by hand)
	mt.record= b
	mt.map[ b: b+ aL ]= mt.map[ a: a+ aL ] #copy old
	for i in range( 4, 8 ):
		mt.setI( b+ i* word, i** 2 )
	mt.close( )
	''' at this point, the former records (0,1,2,3) should still be
	at the original offset as well as at the new one.  (16,25,36,49)
	should come after them at the second offset. '''
	
	mt= MmapAllocTree.open( 'mappedtree.dat' ) #reopen
	b= mt.record
	for i in range( 8 ):
		print 'read', mt.getI( b+ i* word )
	mt.close( )
useful_test( )
