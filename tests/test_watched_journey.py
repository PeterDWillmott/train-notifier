import unittest
from datetime import time

from contracts import Leg, StationRef, WatchedJourney

A = StationRef("ORIGIN1", "AAA")
B = StationRef("BTHNLGR", "BBB")
B2 = StationRef("BTHNLGE", "BBE")  # nearby second station
C = StationRef("DEST1", "CCC")


def journey(leg1_dest=B, leg2_origin=B, arr1=time(8, 0), dep2=time(8, 10), **kw):
    return WatchedJourney(
        id="j1",
        name="Morning",
        leg1=Leg(A, leg1_dest, time(7, 30), arr1),
        leg2=Leg(leg2_origin, C, dep2, time(8, 40)),
        **kw,
    )


class SameStationInterchange(unittest.TestCase):
    def test_same_station_ok(self):
        j = journey()
        self.assertFalse(j.is_walking_interchange)
        self.assertEqual(j.arrival_station, j.departure_station)
        self.assertEqual(j.required_connection_mins, 5)

    def test_different_stations_without_walk_rejected(self):
        with self.assertRaises(ValueError):
            journey(leg2_origin=B2)


class WalkingInterchange(unittest.TestCase):
    def test_walk_between_stations_ok(self):
        j = journey(leg2_origin=B2, interchange_walk_mins=7)
        self.assertTrue(j.is_walking_interchange)
        self.assertEqual(j.arrival_station, B)
        self.assertEqual(j.departure_station, B2)
        self.assertEqual(j.required_connection_mins, 12)

    def test_walk_gap_too_short_rejected(self):
        with self.assertRaises(ValueError):
            journey(leg2_origin=B2, interchange_walk_mins=15)  # only 10 min scheduled gap

    def test_walk_gap_exactly_equal_ok(self):
        journey(leg2_origin=B2, interchange_walk_mins=10)

    def test_negative_walk_rejected(self):
        with self.assertRaises(ValueError):
            journey(interchange_walk_mins=-1)

    def test_walk_at_same_station_adds_to_required_time(self):
        self.assertEqual(journey(interchange_walk_mins=3).required_connection_mins, 8)

    def test_hashable(self):
        hash(journey(leg2_origin=B2, interchange_walk_mins=7))


if __name__ == "__main__":
    unittest.main()
