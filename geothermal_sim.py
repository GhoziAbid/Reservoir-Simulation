from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class SimulationState:
    time_days: float
    pressure_pa: float
    temperature_c: float
    fluid_mass_kg: float
    cumulative_heat_extracted_j: float


@dataclass
class GeothermalReservoir:
    volume_m3: float
    porosity: float
    fluid_density_kg_m3: float
    total_compressibility_pa_inv: float
    fluid_cp_j_kg_k: float
    rock_density_kg_m3: float
    rock_cp_j_kg_k: float
    initial_pressure_pa: float
    initial_temperature_c: float
    history: List[SimulationState] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self._pore_volume = self.porosity * self.volume_m3
        self._rock_mass = (1.0 - self.porosity) * self.volume_m3 * self.rock_density_kg_m3
        self._fluid_mass = self._pore_volume * self.fluid_density_kg_m3
        self._total_energy_j = self._compute_total_energy(self.initial_temperature_c)
        self._cumulative_heat_extracted_j = 0.0
        initial_state = SimulationState(
            time_days=0.0,
            pressure_pa=self.initial_pressure_pa,
            temperature_c=self.initial_temperature_c,
            fluid_mass_kg=self._fluid_mass,
            cumulative_heat_extracted_j=self._cumulative_heat_extracted_j,
        )
        self.history.append(initial_state)

    def _compute_total_energy(self, temperature_c: float) -> float:
        fluid_energy = self._fluid_mass * self.fluid_cp_j_kg_k * temperature_c
        rock_energy = self._rock_mass * self.rock_cp_j_kg_k * temperature_c
        return fluid_energy + rock_energy

    def _update_pressure(self, mass_change_kg: float) -> float:
        delta_p = mass_change_kg / (self.total_compressibility_pa_inv * self._pore_volume * self.fluid_density_kg_m3)
        return self.history[-1].pressure_pa + delta_p

    def _update_energy(self, injection_mass_kg: float, production_mass_kg: float, injection_temp_c: float) -> None:
        self._total_energy_j += injection_mass_kg * self.fluid_cp_j_kg_k * injection_temp_c
        produced_energy = production_mass_kg * self.fluid_cp_j_kg_k * self.history[-1].temperature_c
        self._total_energy_j -= produced_energy
        self._cumulative_heat_extracted_j += produced_energy

    def step(self, dt_days: float, production_rate_kg_s: float, injection_rate_kg_s: float, injection_temperature_c: float) -> SimulationState:
        if dt_days <= 0:
            raise ValueError("dt_days must be positive")
        seconds = dt_days * 86_400.0
        produced_mass = production_rate_kg_s * seconds
        injected_mass = injection_rate_kg_s * seconds
        mass_change = injected_mass - produced_mass

        if produced_mass > (self._fluid_mass + injected_mass):
            # prevent negative mass: clamp production to available-in-step inventory
            produced_mass = max(self._fluid_mass + injected_mass, 0.0)
            mass_change = injected_mass - produced_mass

        self._fluid_mass += mass_change
        new_pressure = self._update_pressure(mass_change)
        self._update_energy(injected_mass, produced_mass, injection_temperature_c)

        total_heat_capacity = (self._fluid_mass * self.fluid_cp_j_kg_k) + (self._rock_mass * self.rock_cp_j_kg_k)
        new_temperature = self._total_energy_j / total_heat_capacity

        new_state = SimulationState(
            time_days=self.history[-1].time_days + dt_days,
            pressure_pa=new_pressure,
            temperature_c=new_temperature,
            fluid_mass_kg=self._fluid_mass,
            cumulative_heat_extracted_j=self._cumulative_heat_extracted_j,
        )
        self.history.append(new_state)
        return new_state

    def run(self, duration_days: float, dt_days: float, production_rate_kg_s: float, injection_rate_kg_s: float, injection_temperature_c: float) -> List[SimulationState]:
        steps = int(duration_days / dt_days)
        for _ in range(steps):
            self.step(dt_days, production_rate_kg_s, injection_rate_kg_s, injection_temperature_c)
        return self.history

    def run_schedule(self, schedule: List[dict], dt_days: float) -> List[SimulationState]:
        """
        Run a piecewise-constant production/injection schedule.

        Each schedule item is a dict containing:
        - duration_days
        - production_kgps
        - injection_kgps
        - injection_temperature_c
        """
        for item in schedule:
            duration = float(item["duration_days"])
            if duration <= 0:
                raise ValueError("Each schedule duration must be positive")
            steps = int(round(duration / dt_days))
            for _ in range(steps):
                self.step(
                    dt_days,
                    production_rate_kg_s=float(item["production_kgps"]),
                    injection_rate_kg_s=float(item["injection_kgps"]),
                    injection_temperature_c=float(item["injection_temperature_c"]),
                )
        return self.history


def run_cli() -> None:
    import argparse
    import csv
    import json

    parser = argparse.ArgumentParser(description="Run a simple geothermal reservoir material and energy balance simulation.")
    parser.add_argument("--duration-days", type=float, required=True, help="Total simulation duration in days.")
    parser.add_argument("--dt-days", type=float, default=1.0, help="Time step in days.")
    parser.add_argument("--production-kgps", type=float, required=True, help="Production rate in kg/s.")
    parser.add_argument("--injection-kgps", type=float, required=True, help="Injection rate in kg/s.")
    parser.add_argument("--injection-temperature", type=float, default=70.0, help="Injection fluid temperature in Celsius.")
    parser.add_argument(
        "--schedule",
        type=str,
        default="",
        help="Optional path to JSON/CSV schedule with duration_days, production_kgps, injection_kgps, injection_temperature_c.",
    )
    parser.add_argument("--output", type=str, default="", help="Optional CSV file to store results.")

    args = parser.parse_args()

    reservoir = GeothermalReservoir(
        volume_m3=2.5e8,
        porosity=0.15,
        fluid_density_kg_m3=950.0,
        total_compressibility_pa_inv=1.5e-9,
        fluid_cp_j_kg_k=4_200.0,
        rock_density_kg_m3=2_650.0,
        rock_cp_j_kg_k=880.0,
        initial_pressure_pa=12e6,
        initial_temperature_c=230.0,
    )

    if args.schedule:
        with open(args.schedule, "r", newline="") as schedule_file:
            if args.schedule.lower().endswith(".json"):
                schedule = json.load(schedule_file)
            else:
                reader = csv.DictReader(schedule_file)
                schedule = list(reader)
        history = reservoir.run_schedule(schedule=schedule, dt_days=args.dt_days)
    else:
        history = reservoir.run(
            duration_days=args.duration_days,
            dt_days=args.dt_days,
            production_rate_kg_s=args.production_kgps,
            injection_rate_kg_s=args.injection_kgps,
            injection_temperature_c=args.injection_temperature,
        )

    if args.output:
        with open(args.output, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["time_days", "pressure_pa", "temperature_c", "fluid_mass_kg", "cumulative_heat_extracted_j"])
            for state in history:
                writer.writerow(
                    [state.time_days, state.pressure_pa, state.temperature_c, state.fluid_mass_kg, state.cumulative_heat_extracted_j]
                )
    else:
        for state in history:
            print(
                f"Day {state.time_days:8.2f} | Pressure {state.pressure_pa/1e6:6.2f} MPa | "
                f"Temp {state.temperature_c:6.2f} C | Fluid mass {state.fluid_mass_kg/1e9:6.3f} Gkg | "
                f"Cum heat out {state.cumulative_heat_extracted_j/3.6e9:6.3f} GWh"
            )


if __name__ == "__main__":
    run_cli()
