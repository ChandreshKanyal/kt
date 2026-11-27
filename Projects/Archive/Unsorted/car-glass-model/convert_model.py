import joblib
import pickle
import sklearn
import numpy as np

print(f"Python sklearn version: {sklearn.__version__}")
print(f"joblib version: {joblib.__version__}")
print("-" * 50)

# Load the original model
model_path = "c:/Users/chandresh.kanyal/Downloads/model.joblib"
print(f"Loading model from: {model_path}")
model = joblib.load(model_path)

# Print model type
print(f"\nModel type: {type(model)}")

# Number of features
n_features = None
if hasattr(model, 'n_features_in_'):
    n_features = model.n_features_in_
    print(f"Number of features (n_features_in_): {n_features}")
elif hasattr(model, 'n_features_'):
    n_features = model.n_features_
    print(f"Number of features (n_features_): {n_features}")
else:
    print("Number of features: not available")

# Feature names
if hasattr(model, 'feature_names_in_'):
    print(f"Feature names: {list(model.feature_names_in_)}")
else:
    print("Feature names: not available (model was trained without feature names)")

# Re-save as native pickle
output_path = "c:/Users/chandresh.kanyal/Downloads/model_compatible.pkl"
with open(output_path, "wb") as f:
    pickle.dump(model, f)
print(f"\nModel re-saved to: {output_path}")
print("Done.")
