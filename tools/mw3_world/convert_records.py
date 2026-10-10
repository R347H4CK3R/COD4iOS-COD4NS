"""Pointer-free IW5 -> IW3 record conversion. Asset fixups are separate."""
import math
import struct

class ConversionError(ValueError): pass

def minmax(row, offset=0):
    values=struct.unpack_from('<6f',row,offset)
    if any(not math.isfinite(x) or abs(x)>1e7 for x in values) or any(x<0 for x in values[3:]):
        raise ConversionError('Invalid original bounds')
    return [values[i]-values[i+3] for i in range(3)]+[values[i]+values[i+3] for i in range(3)]

def surface(row, bound):
    if len(row)!=24 or len(bound)!=24: raise ConversionError('Invalid surface stride')
    return row[:16]+bytes(4)+row[20:24]+struct.pack('<6f',*minmax(bound))

def brush(row, surface_count):
    if len(row)!=60: raise ConversionError('Invalid brush stride')
    count,start,no_decal=struct.unpack_from('<3H',row,52)
    if (count and start+count>surface_count) or no_decal>count:
        raise ConversionError('Brush surface range outside world')
    return struct.pack('<12f3H2x',*(minmax(row)+minmax(row,24)),count,start,no_decal)

def static_model(draw, instance):
    if len(draw)!=76 or len(instance)!=36: raise ConversionError('Invalid model stride')
    placement=struct.unpack_from('<13f',draw)
    if any(not math.isfinite(x) or abs(x)>1e7 for x in placement) or placement[12]<=0:
        raise ConversionError('Invalid static-model placement')
    cull,lighting=struct.unpack_from('<2H',draw,56)
    converted=struct.pack('<f',cull)+draw[:52]+bytes(4)+draw[68:76]+draw[60:62]+struct.pack('<H',lighting)+draw[62:63]+bytes(3)
    return converted,struct.pack('<6f',*minmax(instance))+draw[64:68]
