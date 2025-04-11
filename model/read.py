# reads from existing training data to build existing model
# TODO will have a way to load data from the database and update the model weights

import pandas as pd


from app.models import Data
import numpy as np
official_fields = {x.verbose_name: x for x in Data._meta.fields}


df = pd.read_excel("/Users/juliancerniello/directory/UVA/ENGR_2/schedulingsolar/schedulingsolar/model/updated_dataset.xlsx")
df = df.fillna(value="nan")

columns = df.iloc[1, :].values.tolist()

rows = df.iloc[2:, :].values.tolist()

def format_hours(hour_str):
    nums = [x for x in hour_str.split(' ') if x.isdigit()]
    if len(nums) > 2:
        raise Exception("number error")
    elif len(nums) == 2:
        hours, minutes = nums
    elif len(nums) == 1:
        hours, minutes = 0, nums[0]
    else:
        hours, minutes = 0, 0
    result = float(hours) + float(minutes) / 60
    print(hour_str, result)
    return result


def yes_or_no_func(x):
    print(x, type(x), "ff")
    if isinstance(x, bool):
        return x
    elif x.lower() == "yes":
        return True
    return False

def to_hours(value):
    from datetime import timedelta
    print("value is", value)
    print(type(value))
    if isinstance(value, timedelta):
        print("here")
        return value.total_seconds() / 3600
    if isinstance(value, str):
        try:
            # Handle "HH:MM:SS"
            if ':' in value:
                h, m, s = [float(x) for x in value.split(':')]
                return h + m / 60 + s / 3600
            # Handle "1 day, HH:MM:SS"
            if 'day' in value:
                parts = value.split(', ')
                days = int(parts[0].split(' ')[0])
                h, m, s = [float(x) for x in parts[1].split(':')]
                return days * 24 + h + m / 60 + s / 3600
        except Exception:
            pass
    elif isinstance(value, (float, int)):
        return float(value)
    raise ValueError(f"Cannot parse hours from: {value}")


transformations = {
    "Project ID": lambda x: int(x),
    "Drive Time": lambda x: format_hours(x),
    "Tilt": lambda x: str(x),
    "Consumption Monitoring": yes_or_no_func,
    "Azimuth": lambda x: str(x),
    "Squirrel Screen": yes_or_no_func,
    "Reinforcements": yes_or_no_func,
    "Rough Electrical Inspection": yes_or_no_func,
    "Estimated Salary Hours": to_hours,
    "Estimated Total Direct Time": to_hours,
    "Total Direct Time for Project for Hourly Employees (Including Drive Time)": to_hours
}

for i, row in enumerate(rows):
    print(row) 
    data_obj = Data()
    for j, c in enumerate(columns):
        if c == "nan": continue
        if c not in official_fields:
            print("ISSUE:", c, type(c))
        else:
            # is a valid field, print the model's associated field
            print('ll', official_fields[c], row[j])
            field = official_fields[c]
            print("zz", field.verbose_name, field.name)
            # Validate data type (if the data is an invalid type, raise this error)
            # TODO make sure that the input form has validation so this doesn't need to be run
            expected_type = field.get_internal_type()
            value = row[j]
            print("c", c, expected_type, value, type(value))
            if value == "nan" or str(value).lower() == "nan" or pd.isna(value) or value == None:
                # default values
                if expected_type in ["IntegerField", "BigIntegerField"]:
                    value = -1
                elif expected_type in ["FloatField", "DecimalField"]:
                    value = -1.
                elif expected_type == "BooleanField":
                    value = False
                elif expected_type in ["CharField", "TextField"]:
                    value = ""
                elif expected_type in ["DateTimeField", "DateField", "TimeField"]:
                    value = None
            if c in transformations:
                value = transformations[c](value)
            
            if expected_type in ["IntegerField", "BigIntegerField"] and not isinstance(value, int):
                raise Exception(f"Expected an integer for {c}, but got {type(value).__name__}")
            elif expected_type in ["FloatField", "DecimalField"] and not isinstance(value, (float, int)):
                raise Exception(f"Expected a float/decimal for {c}, but got {type(value).__name__}")
            elif expected_type == "BooleanField" and not isinstance(value, bool):
                raise Exception(f"Expected a boolean for {c}, but got {type(value).__name__}")
            elif expected_type in ["CharField", "TextField"] and not isinstance(value, str):
                raise Exception(f"Expected a string for {c}, but got {type(value).__name__}")
            print("fff", c, "-->", value, "kkk", type(value))
            setattr(data_obj, field.name, value)
    print("----------")
    data_obj.save()