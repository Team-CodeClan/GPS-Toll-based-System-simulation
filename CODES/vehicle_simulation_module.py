import geopandas as gpd
from shapely.geometry import LineString, Point
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import math

class VehicleSimulation:
    def __init__(self, shapefile_path, utm_zone=32633):
        self.shapefile_path = shapefile_path
        self.utm_zone = utm_zone
        self.gdf, self.original_crs = self.load_shapefile()
        self.all_coordinates_utm = self.extract_lines()

    def load_shapefile(self):
        gdf = gpd.read_file(self.shapefile_path)
        original_crs = gdf.crs
        gdf = gdf.to_crs(epsg=self.utm_zone)
        return gdf, original_crs

    def extract_lines(self):
        return [list(line.coords) for line in self.gdf.geometry if isinstance(line, LineString)]

    @staticmethod
    def calculate_total_distance(coords_list):
        return sum(
            np.linalg.norm(np.array(coords[i]) - np.array(coords[i-1]))
            for coords in coords_list
            for i in range(1, len(coords))
        )

    @staticmethod
    def calculate_bearing(start, end):
        start_lat, start_lon = start
        end_lat, end_lon = end
        delta_lon = end_lon - start_lon
        x = math.sin(delta_lon) * math.cos(end_lat)
        y = math.cos(start_lat) * math.sin(end_lat) - math.sin(start_lat) * math.cos(end_lat) * math.cos(delta_lon)
        initial_bearing = math.atan2(x, y)
        initial_bearing = math.degrees(initial_bearing)
        compass_bearing = (initial_bearing + 360) % 360
        return compass_bearing

    @staticmethod
    def calculate_time_increment(distance, speed_mps):
        return distance / speed_mps

    @staticmethod
    def generate_vehicle_id(vehicle_type, vehicle_count):
        return f'{vehicle_type}-{vehicle_count}'

    def simulate_vehicle_movement(self, num_heavy=10, num_two_wheeler=10, num_medium=10, num_special=5, num_steps=1000, max_speed_kmph=60, start_time=None):
        if start_time is None:
            start_time = datetime.now()
        all_vehicle_data = []
        total_distance = self.calculate_total_distance(self.all_coordinates_utm)
        max_speed_mps = max_speed_kmph / 3.6  # Convert max speed to meters per second

        vehicle_counts = {
            'H': num_heavy,
            'T': num_two_wheeler,
            'M': num_medium,
            'S': num_special
        }
        
        for vehicle_type, num_vehicles in vehicle_counts.items():
            for vehicle_count in range(1, num_vehicles + 1):
                vehicle_id = self.generate_vehicle_id(vehicle_type, vehicle_count)
                vehicle_data = []
                current_distance = np.random.uniform(0, total_distance)
                speed_mps = np.random.uniform(0.5, max_speed_mps)  # Speed in meters per second
                timestamp = start_time

                for step in range(num_steps):
                    accumulated_distance = 0.0
                    speed_multiplier = 1.0  # Multiplier for speed adjustments

                    for coords in self.all_coordinates_utm:
                        for i in range(1, len(coords)):
                            start = np.array(coords[i-1])
                            end = np.array(coords[i])
                            segment_distance = np.linalg.norm(end - start)

                            if accumulated_distance + segment_distance >= current_distance:
                                ratio = (current_distance - accumulated_distance) / segment_distance
                                point_utm = start + ratio * (end - start)
                                
                                point_utm_geometry = gpd.GeoSeries([Point(point_utm)], crs=self.gdf.crs)
                                point = point_utm_geometry.to_crs(self.original_crs).iloc[0].coords[0]
                                
                                if np.random.uniform() < 0.1:  # Adjust probability as needed
                                    speed_multiplier = np.random.uniform(1.1, 1.5)  # Randomly increase speed
                                adjusted_speed_mps = speed_mps * speed_multiplier
                                
                                speed_kmph = adjusted_speed_mps * 3.6  # Convert speed back to km/h for recording
                                direction = self.calculate_bearing(start, point)
                                time_increment = self.calculate_time_increment(segment_distance, adjusted_speed_mps)
                                timestamp += timedelta(seconds=time_increment)
                                
                                formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M')
                                vehicle_data.append((vehicle_id, step, point[0], point[1], speed_kmph, formatted_timestamp, direction))
                                
                                current_distance += adjusted_speed_mps / num_steps
                                break
                            accumulated_distance += segment_distance
                        
                        if accumulated_distance >= current_distance:
                            break

                all_vehicle_data.extend(vehicle_data)

        df = pd.DataFrame(all_vehicle_data, columns=['vehicle_id', 'step', 'x', 'y', 'speed_kmph', 'timestamp', 'direction'])
        return df

if __name__ == "__main__":
    shapefile_path = r'Datasets/Roads-Shapefiles/Combined/mergedroad.shx'
    simulation = VehicleSimulation(shapefile_path)

    print(simulation.gdf.head())
    
    num_heavy = 12
    num_two_wheeler = 15
    num_medium = 20
    num_special = 14
    num_steps = 80
    max_speed_kmph = 100
    start_time = datetime(2024, 1, 1, 0, 0, 0)
    
    vehicle_data = simulation.simulate_vehicle_movement(num_heavy, num_two_wheeler, num_medium, num_special, num_steps, max_speed_kmph, start_time)
    print(vehicle_data.head())
    
    output_path = 'GPS_input_simulation.csv'
    vehicle_data.to_csv(output_path, index=False)
    print(f"Simulated vehicle paths saved to {output_path}")
