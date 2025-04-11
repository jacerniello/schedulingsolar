# loads the data as is, with the exception of time stamp values
# good for initial model testing 

import pandas as pd

from datetime import timedelta

# Function to handle timedelta conversion
def convert_to_serializable(value):
    if isinstance(value, timedelta):
        # Convert timedelta to total seconds (or any other representation you prefer)
        return value.total_seconds()
    return value


from app.models import Data, DataField, DataFieldValue

official_fields = {x.verbose_name: x for x in Data._meta.fields}


df = pd.read_excel("/Users/juliancerniello/directory/UVA/ENGR_2/schedulingsolar/schedulingsolar/model/updated_dataset.xlsx")
df = df.fillna(value="nan")

columns = df.iloc[1, :].values.tolist()
rows = df.iloc[2:, :].values.tolist()

accepted_fields = DataField.objects.all()

col_assoc = {}
for i in range(len(columns)):
    column = columns[i]
    if column not in ['nan']:
        is_bad = True
        for field in accepted_fields:
            if field.check_reduced(column):
                col_assoc[column] = field
                is_bad = False
        print("bad", is_bad, column)


for j in range(len(rows)):
    data_obj = Data(project_id=j+1)
    data_obj.save()
    vals = []
    for i in range(len(columns)):
        column_name = columns[i]
        if column_name in col_assoc:
            assoc_field = col_assoc[column_name]
            raw_value = rows[j][i]
            serializable_value = convert_to_serializable(raw_value)
            
            val = DataFieldValue(data=data_obj, field=assoc_field, value=serializable_value)
            val.save()
            vals.append(val)
    
    data_obj.field_values.set(vals)
    data_obj.save()