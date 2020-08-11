import numpy as np
import pandas as pd
import pickle
import re

from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

import configparser
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

config = configparser.ConfigParser()
config.read('../config.ini')
ENDPOINT = config.get('aws', 'ENDPOINT')
PORT = config.get('aws', 'PORT')
USR = config.get('aws', 'USER')
PWD = config.get('aws', 'PASSWORD')
DB = config.get('aws', 'DATABASE')

# Function to get votes
def congress_votes():
    conn = psycopg2.connect(
        host=ENDPOINT,
        user=USR,
        password=PWD,
        port=PORT,
        database=DB
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT CONCAT(senators.f_name, ' ', senators.l_name), votes.csr_id, votes.position
        FROM votes
        JOIN bills ON votes.csr_id = bills.csr_id
        JOIN senators ON votes.sen_id = senators.sen_id
        ;
        """
    )
    votes = cursor.fetchall()
    cursor.close()
    conn.close()
    return votes

# Function to get index and columns for table
def get_ind_col(votes):
    sen_index = []
    vote_cols = []
    for vote in votes:
        if vote[1] not in vote_cols:
            vote_cols.append(vote[1])
        if vote[0] not in sen_index:
            sen_index.append(vote[0])
    return sen_index, vote_cols

# Function to assign numerical values to votes
def vote2score(position):
    dicty = {'Yes': 1, 'Not Voting': 0, 'Present': 0, 'No': -1}
    return dicty[position]

# Funtion to build csv from SQL query votes
def build_csv():
    """
    Function to create csv by making SQL query to database and processing votes
    """
    votes = congress_votes()
    ind, cols = get_ind_col(votes)

    # Instantiate DataFrame with NaN values
    df = pd.DataFrame(
        index=ind,
        columns=cols,
        dtype=int,
    )

    # Assign values at index = senator name, column = bill csr_id
    for vote in votes:
        df.at[vote[0], vote[1]] = vote2score(vote[2])

    return df

# Function to return agreement/total votes
def vote_sim(v1, v2):
    return sum(abs(abs(v1 - v2)/2 - 1)) / len(v1)

# Create matrix for voting similarity between senators
def similarity_matrix(df):
    senators = list(df.index)
    l = len(senators)

    sim_mat = np.zeros((l,l))
    for i in range(l):
        for j in range(l):
            if i != j:
                temp = df.loc[[senators[i], senators[j]]].dropna(axis=1)
                v1 = temp.loc[senators[i]]
                v2 = temp.loc[senators[j]]
                sim = vote_sim(v1, v2)
                sim_mat[i][j] = round(sim, 2)
            else:
                sim_mat[i][j] = np.nan
    return sim_mat

# Retrieve most recent congress number
def get_congress_number():
    conn = psycopg2.connect(
        host=ENDPOINT,
        user=USR,
        password=PWD,
        port=PORT,
        database=DB
    )

    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT MAX(congress) FROM bills
        ;
        """
    )
    
    current_congress = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return current_congress

# Get list of bills from congress (by current of congress number)
def get_bills_list(cong_number, current=True):
    if current == True:
        congress = get_congress_number()
    else:
        congress = cong_number
        
    bills = []
    for col in list(df.columns):
        if re.search(f'^{congress}', col):
            bills.append(col)
    return bills

# Function to get senator information
def senator_info():
    conn = psycopg2.connect(
        host=ENDPOINT,
        user=USR,
        password=PWD,
        port=PORT,
        database=DB
    )

    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM senators
        ;
        """
    )
    
    senator_info = cursor.fetchall()
    cursor.close()
    conn.close()
    return senator_info

if __name__ == '__main__':
    df = build_csv()
    print('Received votes')
    df = pd.DataFrame(np.where(df == 0, np.nan, df), index=df.index, columns=df.columns)
    sim_mat = similarity_matrix(df)
    sim_df = pd.DataFrame(sim_mat, index=df.index, columns=df.index)
    print('Similarities created')
    sen_info = senator_info()
    print('Senator info received')

    # Create DataFrames (similarity and votes) for current Congress
    bills = get_bills_list(116)
    print('List of bills for current congress created')
    df_current = df[bills].copy(deep=True)
    sim_current = pd.DataFrame(similarity_matrix(df_current), index=df_current.index, columns=df_current.index)
    df_current = pd.DataFrame(
        np.where(df_current.isna() == True, 0, df_current),
        index=df_current.index,
        columns=df_current.columns
    )
    print('DataFrames for current congress created')

    # Hard coding will be replaced
    df_current.drop(index='Kelly Loeffler', inplace=True)
    df.drop(index='Kelly Loeffler', inplace=True)
    sim_df.drop(index='Kelly Loeffler', inplace=True)
    sim_df.drop(columns='Kelly Loeffler', inplace=True)
    sim_current.drop(index='Kelly Loeffler', inplace=True)
    sim_current.drop(columns='Kelly Loeffler', inplace=True)

    # Following to build DataFrame for PCA visualizations
    # Number of bills voted on per senator
    sen_length = []
    for sen in list(df_current.index):
        l = len(df.loc[sen].dropna())
        sen_length.append(l)
        
    sen_length = pd.Series(sen_length)
    sen_length.name = 'voting_length'
    df_sl = pd.DataFrame(list(df_current.index), columns=['name']).join(sen_length)
    df_sl.set_index('name', inplace=True)

    # 2 component dimensionality
    pca = PCA(2)
    X = pca.fit_transform(df_current)

    # Clustering algorithm
    cl_algo = KMeans(5)
    labels = cl_algo.fit_predict(df_current)
    sen_name = pd.Series(df_current.index)

    # DataFrame for x, y data
    sen_name.name = 'name'
    df_xy = pd.DataFrame(X, columns=['x', 'y']).join(sen_name)
    df_xy.set_index('name', inplace=True)

    # DataFrame for labels
    df_lbs = pd.DataFrame([sen_name, labels]).T
    df_lbs.columns = ['name', 'label']
    df_lbs.set_index('name', inplace=True)

    # DataFrame for senator info
    df_plot = pd.DataFrame(sen_info)
    df_plot['name'] = df_plot[1] + ' ' + df_plot[2]
    df_plot.drop(columns=[0, 1, 2], inplace=True)
    df_plot.columns = ['party', 'gender', 'state', 'name']
    df_plot.set_index('name', inplace=True)

    # Drop Kelly Loeffler, change Richard Shelby to Republican
    df_plot.drop('Kelly Loeffler', inplace=True) # Replace in future
    df_plot.loc['Richard Shelby']['party'] = 'R'

    # Merge DataFrames
    df_plot = df_plot.join(df_xy, on='name').join(df_lbs, on='name').join(df_sl, on='name')
    df_plot.reset_index(inplace=True)

    # Create cluster names
    df_plot['cluster'] = np.nan
    for i in list(df_plot['label'].unique()):
        temp = df_plot.loc[df_plot['label'] == i]
        cluster = temp.loc[temp['voting_length'] == max(temp['voting_length'])]['name']
        df_plot['cluster'] = np.where(df_plot['label'] == i, cluster + ' Cluster', df_plot['cluster'])

    # Convert DataFrames to csvs and senator list to pickle
    sim_df.to_csv('../app/data/voting_sim.csv')
    sim_current.to_csv('../app/data/vs_current.csv')
    df_plot.to_csv('../app/data/sen_data.csv')
    with open('../app/data/sen_info.p', 'wb') as f:
        pickle.dump(sen_info, f)
    print('CSVs and pickles created')
