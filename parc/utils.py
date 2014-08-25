# trace elidable for instruction reads
from rpython.rlib.jit import elidable, unroll_safe

#-----------------------------------------------------------------------
# sext
#-----------------------------------------------------------------------
# Sign extend 16-bit immediate fields.
def sext( value ):
  if value & 0x8000:
    return 0xFFFF0000 | value
  return value

#-----------------------------------------------------------------------
# sext_byte
#-----------------------------------------------------------------------
# Sign extend 8-bit immediate fields.
def sext_byte( value ):
  if value & 0x80:
    return 0xFFFFFF00 | value
  return value

#-----------------------------------------------------------------------
# signed
#-----------------------------------------------------------------------
def signed( value ):
  if value & 0x80000000:
    twos_complement = ~value + 1
    return -trim( twos_complement )
  return value

#-----------------------------------------------------------------------
# trim
#-----------------------------------------------------------------------
# Trim arithmetic to 16-bit values.
def trim( value ):
  return value & 0xFFFFFFFF

#-----------------------------------------------------------------------
# trim_5
#-----------------------------------------------------------------------
# Trim arithmetic to 5-bit values.
def trim_5( value ):
  return value & 0b11111

#-----------------------------------------------------------------------
# register_inst
#-----------------------------------------------------------------------
# Utility decorator for building decode table.
def register_inst( func ):
  prefix, suffix = func.func_name.split('_')
  assert prefix == 'execute'
  decode_table[ suffix ] = func
  return func

#-----------------------------------------------------------------------
# RegisterFile
#-----------------------------------------------------------------------
class RegisterFile( object ):
  def __init__( self ):
    self.regs = [0] * 32
  def __getitem__( self, idx ):
    return self.regs[idx]
  def __setitem__( self, idx, value ):
    if idx != 0:
      self.regs[idx] = value

#-----------------------------------------------------------------------
# Memory
#-----------------------------------------------------------------------
class Memory( object ):
  def __init__( self, data=None ):
    if not data:
      self.data = [' ']*2**10
    else:
      self.data = data

  @unroll_safe
  def read( self, start_addr, num_bytes ):
    value = 0
    for i in range( num_bytes-1, -1, -1 ):
      value = value << 8
      value = value | ord( self.data[ start_addr + i ] )
    return value

  # this is instruction read, which is otherwise identical to read. The
  # only difference is the elidable annotation, which we assume the
  # instructions are not modified (no side effects, assumes the addresses
  # correspond to the same instructions)
  @elidable
  @unroll_safe
  def iread( self, start_addr, num_bytes ):
    value = 0
    for i in range( num_bytes-1, -1, -1 ):
      value = value << 8
      value = value | ord( self.data[ start_addr + i ] )
    return value

  @unroll_safe
  def write( self, start_addr, num_bytes, value ):
    for i in range( num_bytes ):
      self.data[ start_addr + i ] = chr(value & 0xFF)
      value = value >> 8

#-----------------------------------------------------------------------
# State
#-----------------------------------------------------------------------
class State( object ):
  _virtualizable_ = [ 'rf.regs[*]' ]
  def __init__( self, memory, symtable, reset_addr=0x400 ):
    self.pc       = reset_addr
    self.rf       = RegisterFile()
    self.mem      = memory

    # coprocessor registers
    self.status   = 0
    self.stats_en = 0
    self.ncycles  = 0

    # parc special
    self.src_ptr  = 0
    self.sink_ptr = 0

    # syscall stuff... TODO: should this be here?
    self.break_point = 0

#-----------------------------------------------------------------------
# Instruction Fields
#-----------------------------------------------------------------------
def rd( inst ):
  return (inst >> 11) & 0x1F

def rt( inst ):
  return (inst >> 16) & 0x1F

def rs( inst ):
  return (inst >> 21) & 0x1F

def imm( inst ):
  return inst & 0xFFFF

def jtarg( inst ):
  return inst & 0x3FFFFFF

def shamt( inst ):
  return (inst >> 6) & 0x1F
