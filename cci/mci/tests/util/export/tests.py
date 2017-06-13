from django.test import SimpleTestCase

from mci.util.export import UniquePathManager
from StringIO import StringIO

class UniquePathManagerTestCase(SimpleTestCase):
    def test(self):
        up_man = UniquePathManager()
        naive_path_without_extension = "paths/of/glory/file"
        extension = "txt"
        unique_path_0 = up_man.add(naive_path_without_extension, extension)
        unique_path_1 = up_man.add(naive_path_without_extension, extension)

        self.assertEqual(unique_path_0, naive_path_without_extension + "." + extension)
        self.assertEqual(unique_path_1, naive_path_without_extension + " - 1" + "." + extension)
