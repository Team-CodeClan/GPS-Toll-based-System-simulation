from vehicle_simulation import VehicleSimulation

csv_path = r'D:\intel\datasets\sim_fina\26_06_simrun_pt4.csv'
road_shapefile = r'D:\intel\mergedroad_part\mergedroad.shx'
mainroad_shapefile = r'D:\intel\mainroad_part\mainroads_part1.shx'
output_csv_path = r'26_06_simout_pt7.csv'

simulation = VehicleSimulation(csv_path, road_shapefile, mainroad_shapefile, output_csv_path)
simulation.load_data()
simulation.simulate()
