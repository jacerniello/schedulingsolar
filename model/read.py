# reads from existing training data to build existing model
# TODO will have a way to load data from the database and update the model weights

import pandas as pd

df = pd.read_excel("updated_dataset.xlsx")
print(df)

columns = df.iloc[1, :].values.tolist()
for c in columns:
    print(c)