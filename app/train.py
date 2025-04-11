from django.shortcuts import render, HttpResponse
from app.models import Data, DataField
from datetime import timedelta
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib
import os
from datetime import datetime
import joblib
from django.contrib import messages

class FormattingPipeline:
    def __init__(self, data):
        self.data = data
        self.processed = []
        self.category_names = {
            'categorical': [],
            'numerical': [],
            "boolean": [],
            "misc": []
        }
        all_field_types = DataField.objects.all()
        self.field_process = {}
        self.process_map = {
            "degrees": self.process_degrees,
            "char": self.process_char,
            "int": self.process_int,
            "float": self.process_float,
            "bool": self.process_bool,
            "choice": self.process_choice,
            "datetime": self.process_datetime
        }
        self.field_lookup = {data_field.verbose_name: data_field for data_field in all_field_types}
        for data_obj in self.data:
            self.processed.append(self.process_data_obj(data_obj))
    
    def process_data_obj(self, data_obj):
        processed_field_values = {}
        field_values = data_obj.get_all_field_values()
        for field, value in field_values.items():
            # print(field, value)
            result, field_type = self.process(field, value)
            if isinstance(result, dict):
                for r in result:
                    self.add_to_categories(r, field_type)
                    if r in processed_field_values: raise Exception("conflict!")
                    processed_field_values[r] = result[r]
            else:
                processed_field_values[field] = result
        return processed_field_values
    
    def add_to_categories(self, cat, cat_type):
        if cat_type == "choice":
            if cat not in self.category_names["categorical"]:
                self.category_names["categorical"].append(cat)
        elif cat_type in ['degrees', "int", "float", "datetime"]:
            if cat not in self.category_names["numerical"]:
                self.category_names["numerical"].append(cat)
        elif cat_type == "bool":
            if cat not in self.category_names["boolean"]:
                self.category_names["boolean"].append(cat)
        else:
            if cat not in self.category_names["misc"]:
                self.category_names["misc"].append(cat)
        

    def process(self, field_name, obj):
        field = self.field_lookup.get(field_name, None)
        if field_name == "project_id":
            return self.process_int(obj, field), "int"
        if not field:
            print("could not find", field_name)
            return None, None # could not find the field, do not process this data.
        field_type = field.field_type
        if self.check_nan(obj, field):
            return None, None # return None if nan
        self.add_to_categories(field_name, field_type)
        return self.process_map[field_type](obj, field), field_type # process the object depending on its field
    
    def check_nan(self, obj, field):
        if isinstance(obj, str) and obj.lower().strip() == "nan":
            return True
        elif obj is None:
            return True
        return False

    def process_degrees(self, obj, field):
        # process degrees
        field_name = field.verbose_name
        all_degrees = {f'{field_name} 1': None, f'{field_name} 2': None, f'{field_name} 3': None}
        idx = 0
        deg_keys = list(all_degrees.keys())
        if isinstance(obj, str):
            obj = obj.replace(" ", "/").replace("&", "/").replace("°", "")
            if "/" in obj:
                obj = obj.split("/")
            else:
                obj = [obj]
            for item in obj:
                all_degrees[deg_keys[idx]] = float(item)
                idx += 1
        else:
            all_degrees[deg_keys[idx]] = float(obj)
        return all_degrees

    def process_char(self, obj, field):
        # for now do not consider this field, it will be mainly irrelevant
        # may want to do this later but not now
        return None 
    
    def process_int(self, obj, field):
        return self.process_float(obj, field)
    
    def process_float(self, obj, field):
        new_obj = None
        if isinstance(obj, str):
            if obj.replace('.', '').isdigit():
                new_obj = float(obj)
        elif isinstance(obj, float) or isinstance(obj, int):
            new_obj = float(obj)
        return new_obj
        

    def process_bool(self, obj, field):
        new_obj = None
        if isinstance(obj, str):
            obj = obj.lower().strip()
            if obj in ['yes', 'true']:
                new_obj = True
            elif obj in ['no', 'false']:
                new_obj = False
        return new_obj

    def process_choice(self, obj, field):
        # TODO maybe you shouldn't need to enter matching categories manually
        # if you want it to do this automatically
        for idx, choice in enumerate(field.choices):
            if choice == obj:
                return idx # returns the category's index
        '''if len(final.keys()) == 0:
            print("error", final, "|", obj, "|", field, field.choices)'''
        return None

    def process_datetime(self, obj, field):
        new_obj = None
        if isinstance(obj, str):
            test_obj = obj.strip().split(" ")[0]
            if test_obj.replace(".", "").isdigit():
                new_obj = float(test_obj)
        elif isinstance(obj, float) or isinstance(obj, int):
            new_obj = float(obj)
        return new_obj



def convert_from_serializable(value):
    if isinstance(value, (int, float)):
        return timedelta(seconds=value)
    return value

def convert_from_serializable_readout(value):
    if isinstance(value, (int, float)):
        duration = convert_from_serializable(value)
        days = duration.days
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        # Return as a formatted string
        return f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"
    return value



matplotlib.use('Agg') 

def plot_feature_importances(self, model, X_train, feature_names):
    # Extract the trained model from the pipeline
    
    # Get feature importances from the model
    feature_importances = model.feature_importances_

    # Create a DataFrame with feature names and their importance
    feature_importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': feature_importances
    })
    
    # Sort the DataFrame by importance
    feature_importance_df = feature_importance_df.sort_values(by='importance', ascending=False)
    
    # Plot the top 10 most important features
    plt.figure(figsize=(25, 20))
    sns.barplot(x='importance', y='feature', data=feature_importance_df, palette='viridis')
    plt.title('Features By Importance')
    plt.xlabel('Importance')
    plt.ylabel('Feature')

    image_path = "app/static/images/feature_importance.png"
    if os.path.exists(image_path):
        os.remove(image_path)
    plt.tight_layout()
    plt.savefig(image_path)
    plt.close()
    return image_path.replace("app/", "")




class Model:
    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.data = self.pipeline.processed
        self.feature_image_path = None
        print(self.data[0])
        self.feature_types = self.pipeline.category_names
        print("fff")
        print(self.feature_types)
        all_columns = set()
        for row in self.data:
            for item in row:
                all_columns.add(item)
        
        data_reorganized = {c: [] for c in all_columns}

        for row in self.data:
            not_found = list(all_columns)
            for item in row:
                if item in not_found:
                    data_reorganized[item].append(row[item])
                    not_found.remove(item)
            if not_found:
                for item in not_found:
                    data_reorganized[item].append(None)

        df = pd.DataFrame(data_reorganized)

        self.trained = self.build_and_train_pipeline(
            df=df,
            feature_types = self.feature_types,
            target_column="Total Direct Time for Project for Hourly Employees (Including Drive Time)",
            exclude_columns=["Total # of Days on Site", "Estimated Total Direct Time", "Estimated # of Salaried Employees on Site", "project_id"]
        )
    
    def build_and_train_pipeline(
        self,
        df: pd.DataFrame,
        feature_types: dict,
        target_column: str,
        exclude_columns: list = None
    ):
        # Step 1: Drop excluded columns
        if exclude_columns:
            df = df.drop(columns=exclude_columns, errors='ignore')
        df = df.dropna(axis=1, how="all")
        
        # Step 2: Set types
        df = df.copy()
        df[feature_types['categorical']] = df[feature_types['categorical']].astype('category')
        df[feature_types['boolean']] = df[feature_types['boolean']].astype('boolean')
        df.to_csv("sample.csv")

        # Step 3: Separate target
        y = df[target_column]
        print(y)
        print("zzz")
        X = df.drop(columns=[target_column])

        # Step 4: Build model
        model = RandomForestRegressor(n_estimators=100)

        # Step 5: Fit
        print(X.columns, len(X.columns), 'ffccdd')
        # Split the dataset into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        # Train the model with the pipeline
        model.fit(X_train, y_train)
        
        # Evaluate the model on the test set
        y_pred = model.predict(X_test)
        print(y_test)
        print(y_pred)
        self.absolute_error = np.abs(y_test - y_pred)

        # Calculate over-estimation (where predicted > actual)
        self.over_estimation = np.mean(self.absolute_error[y_pred > y_test])

        # Calculate under-estimation (where predicted < actual)
        self.under_estimation = np.mean(self.absolute_error[y_pred < y_test])

        # Calculate average absolute error
        self.average_absolute_error = np.mean(self.absolute_error)

        print(f"average_absolute_error: {self.average_absolute_error}")
        
        self.feature_image_path = plot_feature_importances(self, model, X_train, X.columns)
        self.trained = model
        return model

    def save(self, dir):
        if not os.path.exists(dir):
            os.mkdir(dir)

        # List existing versions
        versions = sorted(
            [f for f in os.listdir(dir) if f.startswith("trained_model_") and f.endswith(".joblib")]
        )

        # Delete the oldest version if there are already 5
        if len(versions) >= 5:
            oldest = versions[0]
            os.remove(os.path.join(dir, oldest))
            print(f"Deleted old model version: {oldest}")

        # Create a new timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = os.path.join(dir, f"trained_model_{timestamp}.joblib")
        joblib.dump(self.trained, model_path)
        print(f"Model saved to {model_path}")

    def load(self, dir, version="latest"):
        versions = sorted(
            [f for f in os.listdir(dir) if f.startswith("trained_model_") and f.endswith(".joblib")]
        )

        if not versions:
            raise FileNotFoundError(f"No saved model versions found in {dir}")

        if version == "latest":
            model_file = versions[-1]
        else:
            matches = [v for v in versions if version in v]
            if not matches:
                raise FileNotFoundError(f"No model version matching '{version}' found in {dir}")
            model_file = matches[-1]  # use the most recent matching version

        model_path = os.path.join(dir, model_file)
        print(f"Model loaded from {model_path}")

        # Set loaded model to the instance
        self.trained = joblib.load(model_path)



    def predict(self, input_data: dict):
        # Convert input_data to DataFrame with one row
        df_input = pd.DataFrame([input_data])

        # Ensure column types match training data
        for col in self.feature_types['categorical']:
            if col in df_input.columns:
                df_input[col] = df_input[col].astype('category')
        for col in self.feature_types['boolean']:
            if col in df_input.columns:
                df_input[col] = df_input[col].astype('boolean')

        # Reindex to match training data
        trained_columns = self.trained.feature_names_in_
        df_input = df_input.reindex(columns=trained_columns, fill_value=0)

        # Predict
        prediction = self.trained.predict(df_input)[0]
        return prediction


def train(request):
    all_data = Data.objects.all()
    print(all_data)
    
    pipeline_obj = FormattingPipeline(all_data)
    model = Model(pipeline_obj)
    model.save("models")
    # need to make sure to handle lists well
    if not model.feature_image_path:
        messages.error(request, "Something went wrong")
    
    messages.success(request, "Trained & saved model successfully!")
    return render(request, "model_results.html", {
        "image_path": convert_from_serializable_readout(model.feature_image_path),
        "Average_Absolute_Error": convert_from_serializable_readout(model.average_absolute_error),
        "Average_Overestimation": convert_from_serializable_readout(model.over_estimation),
        "Average_Underestimation": convert_from_serializable_readout(model.under_estimation)
    })
