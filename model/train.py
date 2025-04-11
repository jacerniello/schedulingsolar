# training code
"""
https://scikit-learn.org/stable/ 
regression model

https://stackoverflow.com/questions/29623171/simple-prediction-using-linear-regression-with-python

"""

# scikit-learn
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn import linear_model
from sklearn.datasets import updated_dataset

mae = mean_absolute_error(y_test,y_pred)
mae = mean_squared_error(y_test,y_pred)
rmse = np.sqrt(mse)

data = updated_dataset()
df = pd.DataFrame(data = data.data, columns = data.feature_names)

y = df['*variable to be predicted*']
x = df['*input variables*']