import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from build_native import inspect_ios_object


class ObjectEvidenceTests(unittest.TestCase):
    def fixture(self):
        return struct.pack('<8I', 0xfeedfacf, 0x100000c, 0, 1, 1, 24, 0, 0) + struct.pack('<6I', 0x32, 24, 2, 17 << 16, 0, 0)

    def test_correct_platform(self):
        result = inspect_ios_object(self.fixture())
        self.assertEqual(result['architecture'], 'arm64')
        self.assertEqual(result['platform'], 'iOS')
        self.assertEqual(result['minimum_os'], '17.0.0')

    def test_all_truncations_fail(self):
        data = self.fixture()
        for size in range(len(data)):
            with self.subTest(size=size), self.assertRaises(ValueError):
                inspect_ios_object(data[:size])

    def test_wrong_architecture_file_type_and_platform(self):
        for offset, value in ((4, 0x1000007), (12, 2), (40, 7), (44, 12 << 16)):
            data = bytearray(self.fixture())
            struct.pack_into('<I', data, offset, value)
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                inspect_ios_object(data)

    def test_invalid_command_size(self):
        data = bytearray(self.fixture())
        struct.pack_into('<I', data, 36, 0)
        with self.assertRaises(ValueError):
            inspect_ios_object(data)


if __name__ == '__main__':
    unittest.main()
