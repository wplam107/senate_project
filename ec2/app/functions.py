import numpy as np
import pandas as pd
import pickle

import plotly.graph_objects as go
import plotly.express as px

# Function for filtering senators
def sen_by_q(senator_info, party=None, gender=None, state=None):
    senators = []
    if party == None:
        party = ['R', 'D', 'ID']
    if gender == None:
        gender = ['M', 'F', 'N']
    if type(party) != list:
        party = [party]
    if type(gender) != list:
        gender = [gender]
        
    for senator in senator_info:
        sen_name = f'{senator[1]} {senator[2]}'
        sen_party = senator[3]
        sen_gender = senator[4]
        sen_state = senator[5]
        if state == None:
            if sen_party in party and sen_gender in gender:
                senators.append(sen_name)
        else:
            if type(state) != list:
                state = [state]
            if sen_party in party and sen_gender in gender and sen_state in state:
                senators.append(sen_name)
    return senators

# Function for selected senator similarity
def selected_senator_sim(sim_df, senator):
    sen_sim = sim_df.loc[senator]
    sen_list = list(sen_sim.index)
    sen = [ (sen_list[i], sen_sim[i]) for i in range(len(sen_list)) if sen_list[i] != senator ]
    sim_list = sorted(sen, key=lambda x: x[1])
    least = sim_list[:10]
    most = sim_list[::-1][:10]
    return least, most

def pca_plot(df, sen_info, party=None, gender=None, state=None):
    senators = sen_by_q(sen_info, party, gender, state)
    if len(senators) == 0:
        senators = sen_by_q(sen_info)
    if 'Kelly Loeffler' in senators:
        senators.remove('Kelly Loeffler')
    temp = df.set_index('name').loc[senators].reset_index()
    fig = px.scatter(
        temp,
        x='x',
        y='y',
        color='party',
        hover_name='name',
        hover_data=['party', 'state'],
        color_discrete_map={'R': 'red', 'D': 'blue', 'ID': 'light green'},
        size='voting_length',
        symbol='cluster',
        range_x=(-11,11),
        range_y=(-6, 14)
    )
    return fig

def sim_plot(df, senator):
    least, most = selected_senator_sim(df, senator)
    X1 = 100 * np.array([ sen[1] for sen in least ])
    Y1 = [ sen[0] for sen in least ]
    X2 = 100 * np.array([ sen[1] for sen in most ])
    Y2 = [ sen[0] for sen in most ]
    
    fig1 = go.Figure(go.Bar(
        x=X1,
        y=Y1,
        orientation='h',
        hovertemplate=
        'Senator: %{y}' +
        '<br>Percent Agreement: %{x}%<extra></extra>',
    ))
    fig1.update_layout(yaxis={'categoryorder':'total descending'}, height=600, width=700)
    fig1.update_layout(title='Bottom 10: Least Similar Senators', xaxis_title='Rate of Agreement (%)')
    
    fig2 = go.Figure(go.Bar(
        x=X2, 
        y=Y2, 
        orientation='h',
        hovertemplate=
        'Senator: %{y}' +
        '<br>Percent Agreement: %{x}%<extra></extra>',
    ))
    fig2.update_layout(yaxis={'categoryorder':'total ascending'}, height=600, width=700)
    fig2.update_layout(title='Top 10: Most Similar Senators', xaxis_title='Rate of Agreement (%)')
    return fig1, fig2