import pandas as pd
import simpy
from geopy.distance import geodesic
import geopandas as gpd
import networkx as nx
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points

class VehicleSimulation:
    def __init__(self, csv_path, road_shapefile, mainroad_shapefile, output_csv_path):
        self.csv_path = csv_path
        self.road_shapefile = road_shapefile
        self.mainroad_shapefile = mainroad_shapefile
        self.output_csv_path = output_csv_path
        self.FEE_PER_KILOMETER = {
            'H': 6,  # Heavy vehicles
            'T': 0.5,  # Two-wheelers
            'M': 2, # Medium vehicles
            'S': 0  # Special vehicles
        }
        self.RUSH_HOUR_FEE = 1.2  # Additional fee for rush-hour times
        self.results = []

    def load_data(self):
        try:
            self.df = pd.read_csv(self.csv_path)
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'], format="%d-%m-%Y %H:%M")
        except FileNotFoundError:
            print("Error: CSV file not found. Please make sure the file path is correct.")
            exit()
        except pd.errors.ParserError:
            print("Error: Parsing CSV file failed. Please check the file format.")
            exit()

        if 'timestamp' not in self.df.columns:
            print("Error: 'timestamp' column not found in the DataFrame. Please check the CSV file.")
            exit()

        try:
            self.roads = gpd.read_file(self.road_shapefile)
            self.main_roads = gpd.read_file(self.mainroad_shapefile)
        except FileNotFoundError:
            print("Error: Shapefile not found. Please make sure the file path is correct.")
            exit()
        # Ensure the road networks use the same coordinate reference system (CRS)
        self.roads = self.roads.to_crs(epsg=4326)
        self.main_roads = self.main_roads.to_crs(epsg=4326)
        self.main_roads_buffer = self.main_roads.buffer(0.0001)
        self.G = nx.Graph()
        self._build_graph()

    def _build_graph(self):
        for _, road in self.roads.iterrows():
            line = road.geometry
            for i in range(len(line.coords) - 1):
                start = (line.coords[i][0], line.coords[i][1])
                end = (line.coords[i + 1][0], line.coords[i + 1][1])
                distance = geodesic((start[1], start[0]), (end[1], end[0])).meters
                self.G.add_edge(start, end, weight=distance)

    def simulate(self):
        env = simpy.Environment()
        vehicles = [Vehicle(env, vehicle_id, self) for vehicle_id in self.df['vehicle_id'].unique()]
        env.run()
        results_df = pd.DataFrame(self.results)
        results_df.to_csv(self.output_csv_path, index=False)

    def nearest_road_point(self, point):
        nearest_geom = nearest_points(point, self.roads.geometry.unary_union)[1]
        return (nearest_geom.x, nearest_geom.y)

    def add_node_to_graph(self, node):
        nearest_existing_node = min(self.G.nodes, key=lambda n: geodesic((n[1], n[0]), (node[1], node[0])).meters)
        distance = geodesic((nearest_existing_node[1], nearest_existing_node[0]), (node[1], node[0])).meters
        self.G.add_edge(nearest_existing_node, node, weight=distance)

    def calculate_road_distance(self, start, end):
        try:
            path = nx.shortest_path(self.G, source=start, target=end, weight='weight')
            path_edges = zip(path[:-1], path[1:])
            distance = sum(self.G[u][v]['weight'] for u, v in path_edges)
            return distance
        except nx.NetworkXNoPath:
            return geodesic(start, end).meters

    def is_on_main_road(self, point):
        return any(point.within(buffer) for buffer in self.main_roads_buffer)

    # Check if the timestamp is within rush-hour periods
    def is_rush_hour(self, timestamp):
        morning_rush_hour = timestamp.time() >= pd.Timestamp('08:00:00').time() and timestamp.time() <= pd.Timestamp('10:00:00').time()
        evening_rush_hour = timestamp.time() >= pd.Timestamp('16:00:00').time() and timestamp.time() <= pd.Timestamp('18:00:00').time()
        return morning_rush_hour or evening_rush_hour

class Vehicle:
    def __init__(self, env, vehicle_id, simulation):
        self.env = env
        self.vehicle_id = vehicle_id
        self.vehicle_type = vehicle_id[0]
        self.simulation = simulation
        self.segments = []
        self.data = simulation.df[simulation.df['vehicle_id'] == vehicle_id]
        self.action = env.process(self.run())

    def run(self):
        for i in range(len(self.data) - 1):
            current = self.data.iloc[i]
            next_point = self.data.iloc[i + 1]
            duration = (next_point['timestamp'] - current['timestamp']).total_seconds()
            start = Point(current['x'], current['y'])
            end = Point(next_point['x'], next_point['y'])

             # Check if the vehicle is on the main road
            if self.simulation.is_on_main_road(start) and self.simulation.is_on_main_road(end):
                nearest_start = self.simulation.nearest_road_point(start)
                nearest_end = self.simulation.nearest_road_point(end)

                if nearest_start not in self.simulation.G:
                    self.simulation.add_node_to_graph(nearest_start)
                if nearest_end not in self.simulation.G:
                    self.simulation.add_node_to_graph(nearest_end)

                # Calculate the distance along the road network
                distance = self.simulation.calculate_road_distance(nearest_start, nearest_end)
                # Calculate the fee for this segment
                fee = 0 if distance < 30 else (distance / 1000) * self.simulation.FEE_PER_KILOMETER[self.vehicle_type]

                if self.simulation.is_rush_hour(current['timestamp']):
                    fee += self.simulation.RUSH_HOUR_FEE

                # Calculate realistic travel time based on speed
                if 'speed_kmph' in current and current['speed_kmph'] > 0:
                    travel_time = (distance / 1000) / current['speed_kmph'] * 3600
                else:
                    travel_time = duration

                end_time = current['timestamp'] + pd.Timedelta(seconds=travel_time)
                average_speed = (distance / 1000) / (travel_time / 3600) if travel_time > 0 else 0

                self.segments.append({
                    'vehicle_id': self.vehicle_id,
                    'start_time': current['timestamp'],
                    'end_time': end_time,
                    'start_x': start.x,
                    'start_y': start.y,
                    'end_x': end.x,
                    'end_y': end.y,
                    'distance': distance,
                    'fee': fee,
                    'average_speed': average_speed
                })

                print(f"Vehicle {self.vehicle_id} moving from {start} to {end}. Distance: {distance:.2f} meters. Fee: {fee:.2f} Rs. Travel Time: {travel_time:.2f} seconds. Average Speed: {average_speed:.2f} km/h.")
            yield self.env.timeout(duration)

        print(f"Vehicle {self.vehicle_id} total distance traveled on main roads: {sum(s['distance'] for s in self.segments):.2f} meters. Total fee: {sum(s['fee'] for s in self.segments):.2f} Rs.")
        self.simulation.results.extend(self.segments)

if __name__ == "__main__":
    csv_path = r'Datasets/GPS_input_simulation.zip'#too big so path of zip given change while running with actual path
    road_shapefile = r'Datasets/Roads-Shapefiles/Combined/mergedroad.shx'
    mainroad_shapefile = r'Datasets/Roads-Shapefiles/Highways/mainroads_part1.shx'
    output_csv_path = r'Datasets/simulated_output.csv'

    simulation = VehicleSimulation(csv_path, road_shapefile, mainroad_shapefile, output_csv_path)
    simulation.load_data()
    simulation.simulate()
