"In-place" memory manager that uses a disk-backed memory-mapped buffer.  Among its possibilities are: storing variable-length strings and structures for persistence and interprocess communication with mmap.

It allocates segments of a generic buffer by length and returns an offset to the reserved block, which can then be used with struct or ctypes to pack values to store.  The data structure is adapted from the GNU PAVL binary tree.

Module is in proof-of-concept stage.