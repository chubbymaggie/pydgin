

def signed( value, nbits ):
  mask = 0x1 << (nbits - 1)
  value = trim( value, nbits )
  if value & mask:
    twos_complement = ~value + 1
    return -trim( twos_complement, nbits )
  return value

def trim( value, nbits ):
  mask = 0xffffffffffffffff >> (64 - nbits)
  return value & mask

def trim_64( value ):
  return value & 0xffffffffffffffff

def sext_32( value ):
  value = 0x00000000ffffffff & value
  if value & 0x80000000:
    return 0xffffffff00000000 | value
  return value

def sext( value, nbits ):
  value = trim( value, nbits )
  sign_mask = 0x1 << (nbits - 1)
  mask = trim_64( 0xffffffffffffff << nbits )
  if value & sign_mask:
    return mask | value
  return value
