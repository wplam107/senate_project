import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import plotly.graph_objects as go

import pandas as pd
import numpy as np

from functions import *

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

sim_df = pd.read_csv('voting_sim.csv', index_col=0)
cur_sim_df = pd.read_csv('vs_current.csv', index_col=0)
data_df = pd.read_csv('sen_data.csv', index_col=0)
with open('sen_info.p', 'rb') as f:
    sen_info = pickle.load(f)



if __name__ == '__main__':
    app.run_server(debug=True)