from iot.simulate import EnvSimulator, RadarSimulator


def test_env_simulator_ranges():
    sim = EnvSimulator(seed=42)
    temp, hum = sim.temperature_humidity()
    assert 15 <= temp <= 35
    assert 30 <= hum <= 90
    light = sim.light()
    assert 0 <= light <= 1023
    gas = sim.gas()
    assert 0 <= gas <= 1023
    analog, digital = sim.sound()
    assert 0 <= analog <= 1023
    assert isinstance(digital, bool)


def test_radar_simulator_scan():
    radar = RadarSimulator(sectors=6)
    samples = radar.scan(0, 180, 30)
    assert len(samples) >= 6
    for angle, distance in samples:
        assert 0 <= angle <= 180
        assert distance > 0
