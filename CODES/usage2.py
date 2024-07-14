from vehicle_simulation_module import VehicleSimulation
from datetime import datetime

shapefile_path = r'D:\intel\mergedroad_part\mergedroad.shx'
simulation = VehicleSimulation(shapefile_path)

num_heavy = 12
num_two_wheeler = 15
num_medium = 20
num_special = 14
num_steps = 80
max_speed_kmph = 100
start_time = datetime(2024, 1, 1, 0, 0, 0)

vehicle_data = simulation.simulate_vehicle_movement(num_heavy, num_two_wheeler, num_medium, num_special, num_steps, max_speed_kmph, start_time)
print(vehicle_data.head())

output_path = 'simulated_vehicle_paths_hour_org_org.csv'
vehicle_data.to_csv(output_path, index=False)
print(f"Simulated vehicle paths saved to {output_path}")
