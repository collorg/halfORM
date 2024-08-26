from unittest import TestCase, skip
from half_orm.packager.changelog import Changelog

class Test(TestCase):
    def test_sort_releases(self):
        "it should sort the releases"
        releases = ["0.0.1", "0.0.10", "1.0.0", "0.10.0", "0.2.0", "0.0.2"]
        sorted_releases = ["0.0.1", "0.0.2", "0.0.10", "0.2.0", "0.10.0", "1.0.0"]
        self.assertEqual(Changelog._sort_releases(releases), sorted_releases)
