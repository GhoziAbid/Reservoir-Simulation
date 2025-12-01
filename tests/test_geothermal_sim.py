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

    def test_cumulative_heat_tracking(self) -> None:
        self.reservoir.step(dt_days=0.5, production_rate_kg_s=40.0, injection_rate_kg_s=0.0, injection_temperature_c=50.0)
        heat_out = self.reservoir.history[-1].cumulative_heat_extracted_j
        self.assertGreater(heat_out, 0.0)
        self.reservoir.step(dt_days=0.5, production_rate_kg_s=40.0, injection_rate_kg_s=0.0, injection_temperature_c=50.0)
        self.assertGreater(self.reservoir.history[-1].cumulative_heat_extracted_j, heat_out)

    def test_run_schedule(self) -> None:
        schedule = [
            {"duration_days": 1, "production_kgps": 50.0, "injection_kgps": 50.0, "injection_temperature_c": 80.0},
            {"duration_days": 1, "production_kgps": 30.0, "injection_kgps": 60.0, "injection_temperature_c": 90.0},
        ]
        history = self.reservoir.run_schedule(schedule=schedule, dt_days=0.5)
        self.assertEqual(len(history), 1 + int(2 / 0.5))
        last_state = history[-1]
        self.assertLess(last_state.temperature_c, self.reservoir.initial_temperature_c)
        self.assertGreater(last_state.pressure_pa, self.reservoir.initial_pressure_pa)


if __name__ == "__main__":
    unittest.main()
