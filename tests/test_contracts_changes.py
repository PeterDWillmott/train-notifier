import unittest
from datetime import date, datetime, time

from contracts import LONDON, Leg, StationRef, StopStatus, TrainStopUpdate


class StationRefEquality(unittest.TestCase):
    def test_same_crs_different_tiploc_equal_and_hash_equal(self):
        a = StationRef("BTHNLGR", "BTH")
        b = StationRef("BTHNLGE", "BTH")
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))
        self.assertNotEqual(a.tiploc, b.tiploc)

    def test_different_crs_not_equal(self):
        self.assertNotEqual(StationRef("SAME1", "AAA"), StationRef("SAME1", "BBB"))

    def test_normalisation(self):
        s = StationRef("  bthnlgr ", " rdg\t")
        self.assertEqual(s.tiploc, "BTHNLGR")
        self.assertEqual(s.crs, "RDG")
        self.assertEqual(s, StationRef("OTHER", "RDG"))

    def test_bad_tiploc(self):
        for bad in ("", "   ", "TOOLONG88", "AB-C", "AB C", "ÄBC"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    StationRef(bad, "RDG")

    def test_bad_crs(self):
        for bad in ("", "RD", "RDGG", "R1G", "R G", "RÉG"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    StationRef("TIPLOC1", bad)

    def test_leg_same_crs_different_tiploc_rejected(self):
        with self.assertRaises(ValueError):
            Leg(StationRef("AAA1", "AAA"), StationRef("AAA2", "AAA"), time(7, 0), time(8, 0))

    def test_usable_as_dict_and_set_keys(self):
        a = StationRef("BTHNLGR", "BTH")
        b = StationRef("BTHNLGE", "BTH")
        c = StationRef("OTHER1", "CCC")
        self.assertEqual(len({a, b, c}), 2)
        d = {a: "x"}
        self.assertEqual(d[b], "x")
        self.assertNotIn(c, d)


def stop(status, received_at=None, **kw):
    fields = dict(
        train_id="rid", uid="u", service_date=date(2026, 1, 5), headcode=None, toc=None,
        tiploc="RDNGSTN", scheduled_departure=time(8, 0), scheduled_arrival=None,
        estimated_departure=None, estimated_arrival=None, actual_departure=None,
        actual_arrival=None, platform=None, status=status,
        received_at=received_at or datetime(2026, 1, 5, 7, 0, tzinfo=LONDON),
    )
    fields.update(kw)
    return TrainStopUpdate(**fields)


class TrainStopUpdateStatus(unittest.TestCase):
    def test_member_kept(self):
        self.assertIs(stop(StopStatus.on_time).status, StopStatus.on_time)

    def test_valid_string_coerced(self):
        self.assertIs(stop("delayed").status, StopStatus.delayed)

    def test_invalid_string_raises(self):
        with self.assertRaises(ValueError):
            stop("late")

    def test_none_raises(self):
        with self.assertRaises(ValueError):
            stop(None)

    def test_naive_received_at_raises(self):
        with self.assertRaises(ValueError):
            stop(StopStatus.on_time, received_at=datetime(2026, 1, 5, 7, 0))

    def test_non_whole_minute_raises(self):
        with self.assertRaises(ValueError):
            stop(StopStatus.on_time, estimated_departure=time(8, 1, 30))


if __name__ == "__main__":
    unittest.main()
