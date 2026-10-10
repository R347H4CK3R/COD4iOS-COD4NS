import tempfile
import unittest
import zlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "iw5"))
from verify_fastfiles import probe

class FastfileVerifierTests(unittest.TestCase):
    def write(self, folder, payload, magic=b"IWffu100", trailer=b""):
        f = Path(folder) / "synthetic.ff"
        f.write_bytes(magic + bytes(13) + zlib.compress(payload, 9) + trailer)
        return f

    def test_complete_stream(self):
        with tempfile.TemporaryDirectory() as d:
            result = probe(self.write(d, b"test data" * 9000))
            self.assertEqual(result["status"], "complete")
            self.assertEqual(result["decoded_bytes"], 81000)
            self.assertEqual(result["trailing_bytes"], 0)

    def test_trailing_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            result = probe(self.write(d, b"abc", trailer=b"1234"))
            self.assertEqual(result["status"], "complete")
            self.assertEqual(result["trailing_bytes"], 4)

    def test_truncated_stream(self):
        with tempfile.TemporaryDirectory() as d:
            f = self.write(d, b"0123456789" * 2000)
            f.write_bytes(f.read_bytes()[:-3])
            self.assertEqual(probe(f)["status"], "truncated")

    def test_wrong_magic(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(probe(self.write(d, b"abc", magic=b"NOT_IW5!"))["status"], "unsupported_magic")

if __name__ == "__main__":
    unittest.main()
