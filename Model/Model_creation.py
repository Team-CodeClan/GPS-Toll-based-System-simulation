import pandas as pd
from sklearn.model_selection import train_test_split
import lightgbm as lgb
from sklearn.metrics import mean_squared_error, r2_score
import time
import joblib

# Load your dataset
df = pd.read_csv(r'C:\Users\mathe\Documents\Intel Industrial Training\App Deployment\06_07_latlong.csv')

# Convert start_time and end_time to datetime objects
df['start_time'] = pd.to_datetime(df['start_time'], format='%d-%m-%Y %H:%M', errors='coerce')
df['end_time'] = pd.to_datetime(df['end_time'], format='%M:%S.%f', errors='coerce')

# Handle cases where end_time might not have seconds
df['end_time'] = df['end_time'].fillna(pd.to_datetime(df['end_time'], format='%M:%S.%f', errors='coerce'))

# Extract features from datetime columns
df['start_hour'] = df['start_time'].dt.hour
df['start_minute'] = df['start_time'].dt.minute
df['end_minute'] = df['end_time'].dt.minute
df['end_second'] = df['end_time'].dt.second
df['end_msecond'] = df['end_time'].dt.microsecond / 1000  # convert microseconds to milliseconds

# Select relevant features (inputs) and target (output)
base_features = ['start_hour', 'start_minute','end_minute','end_second','start_x','start_y','end_x','end_y','distance','average_speed' ]
target = ['fee']

# Convert categorical vehicle_id feature to numerical using one-hot encoding
df = pd.get_dummies(df, columns=['vehicle_id'])

# Update features list to include the one-hot encoded vehicle_id columns
encoded_vehicle_id_columns = [col for col in df.columns if 'vehicle_id' in col]
features = base_features + encoded_vehicle_id_columns

print(features)
list_length=len(features)
print(list_length)

X = df[features]
y = df[target]

print(df[features].values)

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize LightGBM model
model = lgb.LGBMRegressor(n_estimators=100, random_state=42)

# Train the model
model.fit(X_train, y_train)

print(X_test)

# Make predictions
predictions = model.predict(X_test)

# Calculate Mean Squared Error (MSE) and R^2 score as measures of model performance
mse = mean_squared_error(y_test, predictions)
r2 = r2_score(y_test, predictions)

print(f"Mean Squared Error: {mse}")
print(f"R^2 Score: {r2}")

#joblib.dump(model, "06_07_lgbm_model.sav")