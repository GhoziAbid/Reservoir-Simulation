import unittest

import geothermal_sim


class GeothermalReservoirTests(unittest.TestCase):
    def setUp(self) -> None:
        self.reservoir = geothermal_sim.GeothermalReservoir(
            volume_m3=1.0e7,
            porosity=0.2,
            fluid_density_kg_m3=950.0,
            total_compressibility_pa_inv=1.0e-9,
            fluid_cp_j_kg_k=4_200.0,
            rock_density_kg_m3=2_650.0,
            rock_cp_j_kg_k=880.0,
            initial_pressure_pa=10e6,
            initial_temperature_c=200.0,
        )

    def test_pressure_increases_with_net_injection(self) -> None:
        self.reservoir.step(dt_days=1.0, production_rate_kg_s=50.0, injection_rate_kg_s=70.0, injection_temperature_c=80.0)
        new_pressure = self.reservoir.history[-1].pressure_pa
        self.assertGreater(new_pressure, self.reservoir.initial_pressure_pa)

    def test_temperature_drops_with_cold_injection(self) -> None:
        self.reservoir.step(dt_days=1.0, production_rate_kg_s=60.0, injection_rate_kg_s=60.0, injection_temperature_c=50.0)
        new_temperature = self.reservoir.history[-1].temperature_c
        self.assertLess(new_temperature, self.reservoir.initial_temperature_c)


if __name__ == "__main__":
    unittest.main()
