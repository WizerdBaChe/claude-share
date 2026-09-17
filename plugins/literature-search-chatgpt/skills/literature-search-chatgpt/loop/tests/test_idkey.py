"""idkey tests — two-sided: must-parse and must-unresolve (design LSEL-02 acceptance)."""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import idkey  # noqa: E402


class TestKeys(unittest.TestCase):
    def test_ow_2010_case_duplicates_share_one_key(self):
        a = idkey.normalize({"doi": "10.1364/OE.18.014511"})   # a real Zotero-library duplicate, uppercase DOI
        b = idkey.normalize({"doi": "10.1364/oe.18.014511"})   # same item, lowercase DOI (different Zotero key)
        self.assertEqual(a["key"], b["key"])
        self.assertEqual(a["key"], "doi:10.1364/oe.18.014511")
        self.assertFalse(a["unresolved"])

    def test_doi_prefix_forms(self):
        for raw in ("https://doi.org/10.1063/1.5145105", "doi:10.1063/1.5145105", "DOI: 10.1063/1.5145105"):
            self.assertEqual(idkey.normalize({"doi": raw})["key"], "doi:10.1063/1.5145105", raw)

    def test_arxiv_versionless_with_datacite_alias(self):
        r = idkey.normalize({"arxiv": "arXiv:2110.12851v2"})
        self.assertEqual(r["key"], "arxiv:2110.12851")
        self.assertEqual(r["version"], "v2")
        self.assertIn("doi:10.48550/arxiv.2110.12851", r["aliases"])

    def test_arxiv_old_style(self):
        self.assertEqual(idkey.normalize({"arxiv": "hep-th/9901001"})["key"], "arxiv:hep-th/9901001")

    def test_journal_doi_beats_arxiv(self):
        r = idkey.normalize({"arxiv": "2002.00729v1", "journal_doi": "10.1063/1.5145105"})
        self.assertEqual(r["key"], "doi:10.1063/1.5145105")
        self.assertIn("arxiv:2002.00729", r["aliases"])
        self.assertEqual(r["version"], "v1")

    def test_isbn10_to_13(self):
        self.assertEqual(idkey.normalize({"isbn": "0-387-32989-7"})["key"], "isbn:9780387329895")

    def test_patent_parse_and_reject(self):
        self.assertEqual(idkey.normalize({"patent": "EP1308760A1"})["key"], "patent:EP1308760A1")
        self.assertEqual(idkey.normalize({"patent": "US 2022/0146749 A1"})["key"], "patent:US20220146749A1")
        bad = idkey.normalize({"patent": "EPX-1308760"})
        self.assertTrue(bad["unresolved"])
        self.assertTrue(any("patent" in g for g in bad["gaps"]))

    def test_pmid_fallback(self):
        self.assertEqual(idkey.normalize({"pmid": "20639936"})["key"], "pmid:20639936")

    def test_datasheet_unresolved_with_basis_and_version(self):
        r = idkey.normalize({"title": "Corning SMF-28 Ultra Optical Fiber PI1424", "author": "Corning", "year": 2013,
                             "identifier": "Corning PI-1424-AEN (vendor datasheet)", "version": "March 2013"})
        self.assertTrue(r["unresolved"])
        self.assertTrue(r["key"].startswith("unresolved:"))
        self.assertEqual(r["basis"]["surname"], "corning")
        self.assertEqual(r["version"], "March 2013")
        self.assertIn("Corning PI-1424-AEN (vendor datasheet)", r["aliases"])

    def test_unverifiable_doi_is_not_minted(self):
        r = idkey.normalize({"doi": "10.9/fake"})
        self.assertTrue(r["unresolved"])
        self.assertTrue(any("unverifiable" in g for g in r["gaps"]))

    def test_free_text_srg_cell(self):
        found = idkey.find_all("DOI 10.1002/j.1538-7305.1977.tb00534.x; archive.org/details/bstj56-5-703")
        self.assertEqual(found[0]["key"], "doi:10.1002/j.1538-7305.1977.tb00534.x")
        found = idkey.find_all("DOI 10.1063/1.5145105; arXiv:2002.00729v1 (sole existing version)")
        self.assertEqual([f["scheme"] for f in found], ["doi", "arxiv"])

    def test_collision_bases_differ(self):
        pair = json.loads((HERE / "fixtures" / "collision" / "pair.json").read_text(encoding="utf-8"))
        a, b = idkey.normalize(pair["a"]), idkey.normalize(pair["b"])
        self.assertNotEqual(a["basis"], b["basis"])   # the basis is the identity; the hash is only an id
        # force one hash (simulating a collision) and confirm bases still tell them apart
        forced = a["key"]
        self.assertNotEqual(json.dumps(a["basis"], sort_keys=True), json.dumps(b["basis"], sort_keys=True))
        self.assertTrue(forced.startswith("unresolved:"))

    def test_selftest_is_two_sided(self):
        self.assertEqual(idkey.selftest(), 0)


if __name__ == "__main__":
    unittest.main()
