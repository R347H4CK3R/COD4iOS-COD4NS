#!/usr/bin/env python3
"""Synthetic x86 overlay assets; no game files needed."""
import struct,unittest
from export_oat_navigation import path_graph,addon_entities,overlay_data,ExportError

BASE=0x10000
def fixture():
    data=bytearray(4096)
    name=b'maps/mp/mp_test.d3dbsp\0';data[100:100+len(name)]=name
    struct.pack_into('<III',data,0,BASE+100,2,BASE+200)
    for i in range(2):
        at=200+i*136
        struct.pack_into('<IH',data,at,1,4)
        struct.pack_into('<3f',data,at+20,i*10,2,3)
    struct.pack_into('<H',data,256,1);struct.pack_into('<I',data,260,BASE+500)
    struct.pack_into('<fHBBB',data,500,10,1,0,1,4)
    addon_name=b'maps/so_survival_mp_test.mapents\0';data[700:700+len(addon_name)]=addon_name
    text=b'{\n1668 "actor"\n}\n\0';data[800:800+len(text)]=text
    struct.pack_into('<IIi',data,600,BASE+700,BASE+800,len(text))
    struct.pack_into('<II',data,636,BASE+1000,2)
    return data

class OverlayTests(unittest.TestCase):
    def regions(self,data):return [(BASE,bytes(data))]
    def test_valid_overlay(self):
        graph,text,metadata=overlay_data(self.regions(fixture()),'mp_test')
        self.assertEqual(len(graph['nodes']),2)
        self.assertEqual(graph['nodes'][1]['position'],[10,2,3])
        self.assertEqual(graph['nodes'][0]['links'][0]['target'],1)
        self.assertEqual(graph['nodes'][0]['links'][0]['distance'],10)
        self.assertEqual(text,b'{\n1668 "actor"\n}\n')
        self.assertTrue(metadata['hasAdditionalClipInfo']);self.assertEqual(metadata['submodels'],2)
    def test_outside_target(self):
        data=fixture();struct.pack_into('<H',data,504,2)
        with self.assertRaises(ExportError):path_graph(self.regions(data),BASE,'mp_test')
    def test_invalid_distance(self):
        for value in (-1,float('nan'),float('inf')):
            data=fixture();struct.pack_into('<f',data,500,value)
            with self.assertRaises(ExportError):path_graph(self.regions(data),BASE,'mp_test')
    def test_invalid_node_type(self):
        data=fixture();struct.pack_into('<I',data,200,21)
        with self.assertRaises(ExportError):path_graph(self.regions(data),BASE,'mp_test')
    def test_invalid_node_position(self):
        data=fixture();struct.pack_into('<f',data,220,float('nan'))
        with self.assertRaises(ExportError):path_graph(self.regions(data),BASE,'mp_test')
    def test_outside_link_pointer(self):
        data=fixture();struct.pack_into('<I',data,260,0xfffffff0)
        with self.assertRaises(ExportError):path_graph(self.regions(data),BASE,'mp_test')
    def test_entity_size_and_nul(self):
        for count in (-1,5<<20):
            data=fixture();struct.pack_into('<i',data,608,count)
            with self.assertRaises(ExportError):addon_entities(self.regions(data),BASE+600,'mp_test')
        data=fixture();data[803]=0
        with self.assertRaises(ExportError):addon_entities(self.regions(data),BASE+600,'mp_test')
    def test_wrong_map_identity(self):
        with self.assertRaises(ExportError):overlay_data(self.regions(fixture()),'mp_other')
    def test_ambiguous_graph(self):
        data=fixture();data[1500:1544]=data[:44]
        with self.assertRaises(ExportError):overlay_data(self.regions(data),'mp_test')
    def test_truncated_node_array(self):
        with self.assertRaises(ExportError):path_graph(self.regions(fixture()[:400]),BASE,'mp_test')
if __name__=='__main__':unittest.main()
