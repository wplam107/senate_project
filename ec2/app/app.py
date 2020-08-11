import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import plotly.graph_objects as go

from dash.dependencies import Input, Output

import pandas as pd
import numpy as np

from functions import *

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

sim_df = pd.read_csv('data/voting_sim.csv', index_col=0)
cur_sim_df = pd.read_csv('data/vs_current.csv', index_col=0)
data_df = pd.read_csv('data/sen_data.csv', index_col=0)
with open('data/sen_info.p', 'rb') as f:
    sen_info = pickle.load(f)

# Options
states = list(set([ sen[5] for sen in sen_info ]))
states.sort()
genders = list(set([ sen[4] for sen in sen_info ]))
genders.sort()
parties = list(set([ sen[3] for sen in sen_info ]))
parties.sort()

app.layout = html.Div(children=[
    html.H1(children=[
        'Senator Similarity Dashboard',
        html.A(
            html.Img(
                src='assets/GitHub-Mark-64px.png',
                style={'float': 'right', 'height': '50px'}
            ), href='https://github.com/wplam107/senate_project'
        )
    ]),
    dcc.Tabs([
        dcc.Tab(label='Visualization of Congress', children=[
            html.Div(children=[
                html.H3('Senator Votes in 2-Dimensions'),
                html.Div(children=[
                    html.Div(children=[
                        dcc.Markdown(
                            '''
                            In this plot senator votes over the current Congress has been projected onto 2 dimensions
                            using principal component analysis (PCA).  PCA in this plot is only used as an aid for visualization.
                            Clustering of senators with KMeans (5 clusters) was performed on the senators across all votes
                            in the current Congress (each vote treated as a feature).  Clusters were assigned 
                            names based on the most senior (most votes on bills) member.
                            '''
                        ),
                        dcc.RadioItems(
                            id='disable-state',
                            options=[
                                {'label': 'All States', 'value': 'disable'},
                                {'label': 'Select States', 'value': 'enable'}
                            ],
                            labelStyle={'display': 'inline-block'},
                            value='disable',
                        ),
                        dcc.Dropdown(
                            id='state-pca',
                            options=[ {'label': state, 'value': state} for state in states ],
                            multi=True,
                            disabled=False,
                            placeholder='Select State(s)',
                            clearable=False
                        ),
                        dcc.RadioItems(
                            id='disable-gender',
                            options=[
                                {'label': 'All Genders', 'value': 'disable'},
                                {'label': 'Select Genders', 'value': 'enable'}
                            ],
                            labelStyle={'display': 'inline-block'},
                            value='disable',
                        ),
                        dcc.Dropdown(
                            id='gender-pca',
                            options=[ {'label': gender, 'value': gender} for gender in genders ],
                            multi=True,
                            disabled=False,
                            placeholder='Select Gender(s)',
                            clearable=False
                        ),
                        dcc.RadioItems(
                            id='disable-party',
                            options=[
                                {'label': 'All Parties', 'value': 'disable'},
                                {'label': 'Select Parties', 'value': 'enable'}
                            ],
                            labelStyle={'display': 'inline-block'},
                            value='disable',
                        ),
                        dcc.Dropdown(
                            id='party-pca',
                            options=[ {'label': party, 'value': party} for party in parties ],
                            multi=True,
                            disabled=False,
                            placeholder='Select Party/Parties',
                            clearable=False
                        ),
                    ], className='six columns'),
                    html.Div(dcc.Graph(id='pca-plot'), className='six columns')
                ], className='row')
            ])
        ]),
        dcc.Tab(label='Senator Similarities', children=[
            html.Div([
                html.H3('Tab content 2')
            ])
        ])
    ]),
])

@app.callback(
    Output('state-pca', 'disabled'),
    [Input('disable-state', 'value')])
def pca_state_disable(value):
    if value == 'disable':
        return True
    else:
        return False

@app.callback(
    Output('gender-pca', 'disabled'),
    [Input('disable-gender', 'value')])
def pca_state_disable(value):
    if value == 'disable':
        return True
    else:
        return False

@app.callback(
    Output('party-pca', 'disabled'),
    [Input('disable-party', 'value')])
def pca_state_disable(value):
    if value == 'disable':
        return True
    else:
        return False

@app.callback(
    Output('pca-plot', 'figure'),
    [Input('state-pca', 'value'),
    Input('gender-pca', 'value'),
    Input('party-pca', 'value'),
    Input('disable-state', 'value'),
    Input('disable-gender', 'value'),
    Input('disable-party', 'value')])
def update_pca_plot(state, gender, party, s, g, p):
    if s == 'disable':
        state = states
    if g == 'disable':
        gender = genders
    if p == 'disable':
        party = parties
    return pca_plot(data_df, sen_info, state=state, gender=gender, party=party)
    

if __name__ == '__main__':
    app.run_server(debug=True)