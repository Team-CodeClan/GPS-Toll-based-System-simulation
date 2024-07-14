from flask import Flask, jsonify, request , Response ,render_template
from flask_cors import CORS
import joblib
import pandas as pd
import os
import git
import secrets
import geopandas as gpd
import networkx as nx
import folium
from shapely.geometry import Point


global last_journey_details

app = Flask(__name__)

# Allow CORS for specific origins
CORS(app, resources={
    r"/predict": {"origins": "https://muhammedanees-loony.github.io"},
    r"/plot_map": {"origins": "https://muhammedanees-loony.github.io"}
})

# Set the secret key
app.secret_key = secrets.token_hex(16)  # Generate a new secret key

# GitHub repository details
GITHUB_REPO_URL = 'https://github.com/MuhammedAnees-loony/test.git'  # Replace with your repository URL
LOCAL_REPO_PATH = 'local_repo'  # Local path to clone the repository

# Clone the repository if it doesn't exist
if not os.path.exists(LOCAL_REPO_PATH):
    git.Repo.clone_from(GITHUB_REPO_URL, LOCAL_REPO_PATH)

# Function to list all files in the repository (for debugging)
#def list_all_files(directory):
    #for root, dirs, files in os.walk(directory):
        #for file in files:
            #print(os.path.join(root, file))

# List all files in the repository (for debugging)
#print("Files in the repository after cloning:")
#list_all_files(LOCAL_REPO_PATH)

# Function to pull the latest changes from the repository
def pull_latest_changes():
    repo = git.Repo(LOCAL_REPO_PATH)
    origin = repo.remotes.origin
    origin.pull()

# Load the model from the cloned repository
def load_model():
    model_path = os.path.join(LOCAL_REPO_PATH, r'flaskapp\06_07_lgbm_model.sav')
    if os.path.exists(model_path):
        return joblib.load(model_path)
    else:
        raise FileNotFoundError(f'Model file {model_path} not found.')

model = load_model()

# Function to push changes to the repository
def push_changes(commit_message):
    repo = git.Repo(LOCAL_REPO_PATH)
    repo.git.add(A=True)
    repo.index.commit(commit_message)
    origin = repo.remotes.origin
    origin.push()

@app.route('/')
def home():
    return "Welcome to the LightGBM Model API!"

@app.route('/predict', methods=['POST'])
def predict():
    pull_latest_changes()  # Pull the latest changes from the repository
    global last_journey_details
    global vehicle_id
    # Directory containing the CSV files
    directory_path = os.path.join(LOCAL_REPO_PATH, 'users')  # Adjust the path as needed

    # Ensure the directory exists
    if not os.path.exists(directory_path):
        return jsonify({'error': 'CSV directory does not exist'}), 400

    # Features expected by the model
    features = ['start_hour', 'start_minute', 'end_minute', 'end_second', 'start_x', 'start_y', 'end_x', 'end_y', 'distance', 'average_speed', 'vehicle_id_H', 'vehicle_id_M', 'vehicle_id_S', 'vehicle_id_T']
    plot_features = ['start_x', 'start_y', 'end_x', 'end_y']
    
    # Get vehicle_id from request data
    if not request.is_json:
        return jsonify({'error': 'Request body must be JSON'}), 400
    if 'vehicle_id' not in request.json:
        return jsonify({'error': 'vehicle_id is required in the request'}), 400

    vehicle_id = request.json['vehicle_id']

    # Print the received vehicle_id
    print(f'Received vehicle_id: {vehicle_id}')

    # Initialize a list to collect DataFrames
    pass_df_list = []

    # Process each CSV file in the directory
    predictions_made = False
    for file_name in os.listdir(directory_path):
        if file_name.endswith('.csv'):
            file_path = os.path.join(directory_path, file_name)
            #print(f'Processing file: {file_path}')  # Print the CSV file name

            df = pd.read_csv(file_path)
            #print(f'CSV data from {file_name}:')
            #print(df)  # Print the contents of the CSV file

            # Filter DataFrame by vehicle_no
            df_filtered = df[df['vehicle_no'] == vehicle_id]
            #print(f'Filtered data for vehicle_no {vehicle_id}:')
            #print(df_filtered)  # Print the filtered data

            # Check if the filtered DataFrame is empty
            if df_filtered.empty:
                continue  # Skip this file if no matching vehicle_no is found

            # Convert datetime columns to numerical features
            df_filtered['start_time'] = pd.to_datetime(df_filtered['start_time'], format='%d-%m-%Y %H:%M', errors='coerce')
            df_filtered['end_time'] = pd.to_datetime(df_filtered['end_time'], format='%M:%S.%f', errors='coerce')

            df_filtered['start_hour'] = df_filtered['start_time'].dt.hour
            df_filtered['start_minute'] = df_filtered['start_time'].dt.minute
            df_filtered['end_minute'] = df_filtered['end_time'].dt.minute
            df_filtered['end_second'] = df_filtered['end_time'].dt.second

            # Drop datetime columns
            df_filtered = df_filtered.drop(['start_time', 'end_time'], axis=1)
            #print(df_filtered)

            # Convert categorical variables to dummies (one-hot encoding)
            df_encoded = pd.get_dummies(df_filtered, columns=['vehicle_id'], prefix='vehicle_id')

            # Ensure all expected columns are present after one-hot encoding
            for feature in features:
                if feature not in df_encoded.columns:
                    df_encoded[feature] = 0  # Add missing feature columns with default value

            # Ensure columns are in the correct order
            df_encoded = df_encoded[features]

            #print(df_encoded)

            # Extract the input features
            input_data = df_encoded.values

            #print(df_encoded.values)

            # Predict the fee
            predictions = model.predict(input_data)
            #print(f'Predictions: {predictions}')  # Print the predictions

            # Add the predictions to the DataFrame (if needed)
            df.loc[df['vehicle_no'] == vehicle_id, 'fee'] = predictions

            # Save the updated DataFrame back to the CSV file (if needed)
            df.to_csv(file_path, index=False)
            predictions_made = True

            # Store the distance and fee into a new DataFrame
            pass_df = df_filtered[['distance']].copy()
            pass_df['fee'] = predictions
            pass_df_list.append(pass_df)

            # Extract and print the last journey details
            len_csv=len(df_filtered)
            last_journey_details = df_filtered.iloc[(len_csv)-1][plot_features]
            #print("Last journey details:")
            #print(last_journey_details)

    # Check if any predictions were made
    if not predictions_made:
        return jsonify({'error': 'No data found for the provided vehicle_id'}), 400

    push_changes("Update CSV files with predictions")  # Push the changes back to the repository

    # Concatenate all DataFrames in the list into a single DataFrame
    if pass_df_list:
        final_pass_df = pd.concat(pass_df_list, ignore_index=True)
        #print("Final pass_df DataFrame:")
        #print(final_pass_df)
        # Convert DataFrame to JSON
        pass_df_json = final_pass_df.to_json(orient='records')
        
    #print(last_journey_details)
    return jsonify(pass_df_json), 200

@app.route('/plot_map', methods=['POST'])
def plot_map():
    global last_journey_details
    global vehicle_id
    #print("This Is Inside Plot")
    #print(last_journey_details)

    # Plotting code
    main_shapefile_path = os.path.join(LOCAL_REPO_PATH, r'mainroad_part\mainroads_part1.shp')
    additional_shapefile_path = os.path.join(LOCAL_REPO_PATH, r'mergedroad_part\mergedroad.shp')

    # Load the main shapefile using Geopandas
    gdf_main = gpd.read_file(main_shapefile_path)

    # Load the additional shapefile using Geopandas
    gdf_additional = gpd.read_file(additional_shapefile_path)

    # Convert the main GeoDataFrame to a graph using NetworkX
    graph = nx.Graph()

    for _, row in gdf_main.iterrows():
        coords = list(row.geometry.coords)
        for i in range(len(coords) - 1):
            graph.add_edge(coords[i], coords[i+1], length=Point(coords[i]).distance(Point(coords[i+1])))

    # Latitude and Longitude to center the map
    latitude = gdf_main.geometry.centroid.y.mean()
    longitude = gdf_main.geometry.centroid.x.mean()

    # Initialize the folium map
    m = folium.Map(location=[latitude, longitude], zoom_start=12)

    # Add the main road network to the map
    folium.GeoJson(gdf_main).add_to(m)

    # Add the additional road network to the map in red color
    folium.GeoJson(gdf_additional, style_function=lambda x: {'color': 'red'}).add_to(m)

    # Plot the vehicle journey from last_journey_details
    start_point = (last_journey_details['start_y'], last_journey_details['start_x'])
    end_point = (last_journey_details['end_y'], last_journey_details['end_x'])

    #print(start_point,end_point)

    # Find the nearest nodes in the graph
    start_node = min(graph.nodes, key=lambda n: Point(n).distance(Point(start_point)))
    end_node = min(graph.nodes, key=lambda n: Point(n).distance(Point(end_point)))

    # Calculate the shortest path
    shortest_path = nx.shortest_path(graph, source=start_node, target=end_node, weight='length')

    # Extract the coordinates of the nodes in the shortest path
    path_coords = [(node[1], node[0]) for node in shortest_path]

    # Add markers for start and end points
    folium.Marker(location=[start_point[1], start_point[0]], popup=f"Start {vehicle_id}").add_to(m)
    folium.Marker(location=[end_point[1], end_point[0]], popup=f"End {vehicle_id}").add_to(m)

    # Add the shortest path as a PolyLine
    folium.PolyLine(locations=path_coords, color='blue', weight=2.5, opacity=1).add_to(m)

    # Get the HTML representation of the map
    map_html = m.get_root().render()

    # The HTML content of the map (for example purposes)
    html_content = map_html
    
    # Return the HTML content of the map using jsonify
    return jsonify({"map_html": map_html})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
