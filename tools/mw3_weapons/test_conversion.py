import unittest
from convert_acr import info_parse, info_write, techniques, convert_material


class ConversionTests(unittest.TestCase):
    def test_weapon_empty_and_multiline_fields(self):
        fields={'gunModel':'real_acr','handModel':'','hideTags':'tag_a\ntag_b'}
        self.assertEqual(info_parse(info_write(fields)),fields)
        with self.assertRaises(ValueError): info_parse('WEAPONFILE\\key')

    def test_named_techniques_not_shifted_indices(self):
        iw3=techniques('enum MaterialTechniqueType { TECHNIQUE_LIT=0x7, TECHNIQUE_LIT_END=0x15, TECHNIQUE_UNLIT=4, };')
        self.assertEqual(iw3,{'TECHNIQUE_LIT':7,'TECHNIQUE_UNLIT':4})
        material={'_game':'iw5','cameraRegion':'litOpaque','techniqueSet':'iw5_only',
                  'stateBitsEntry':list(range(54)),'stateBits':[{'gammaWrite':True}],
                  'textures':[{'name':'colorMap'},{'name':'normalMap'},{'name':'specularMap'}]}
        result=convert_material(material,'native',iw3,{'TECHNIQUE_LIT':9,'TECHNIQUE_UNLIT':4})
        self.assertEqual(result['stateBitsEntry'][7],9)
        self.assertEqual(result['stateBitsEntry'][4],4)
        self.assertEqual(result['stateBitsEntry'][0],-1)
        self.assertEqual(len(result['stateBitsEntry']),34)
        self.assertEqual(result['_game'],'iw3')
        self.assertEqual(result['cameraRegion'],'lit')
        self.assertNotIn('gammaWrite',result['stateBits'][0])
        self.assertEqual([t['name'] for t in result['textures']],['colorMap','normalMap'])
        self.assertEqual(material['_game'],'iw5')


if __name__=='__main__': unittest.main()
