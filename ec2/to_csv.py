import numpy as np
import pandas as pd

import configparser
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

config = configparser.ConfigParser()
config.read('config.ini')
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
def build_csv(votes):
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

