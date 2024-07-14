from vehicle_simulation import VehicleSimulation

csv_path = r'Datasets/GPS_input_simulation.zip'#too big so path of zip given change while running with actual path
road_shapefile = r'Datasets/Roads-Shapefiles/Combined/mergedroad.shx'
mainroad_shapefile = r'Datasets/Roads-Shapefiles/Highways/mainroads_part1.shx'
output_csv_path = r'Datasets/simulated_output.csv'

simulation = VehicleSimulation(csv_path, road_shapefile, mainroad_shapefile, output_csv_path)
simulation.load_data()
simulation.simulate()
