from iot.radar_occupancy import RadarOccupancy


def test_sector_metrics():
    occupancy = RadarOccupancy(sectors=6, object_threshold_m=1.5)
    samples = [
        (0, 1.0),
        (10, 2.0),
        (35, 1.0),
        (70, 1.0),
        (80, 2.5),
        (100, 1.2),
        (120, 0.8),
        (150, 2.5),
    ]
    metrics = occupancy.process(samples)
    assert metrics["sector_0_pct"] == 50.0
    assert metrics["sector_2_pct"] == 50.0
    assert metrics["objects_count"] == 3
    assert metrics["min_distance_m"] == 0.8
