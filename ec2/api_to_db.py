import requests
import json
import configparser
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Set up connection to AWS RDS
config1 = configparser.ConfigParser()
config1.read('../config.ini')
ENDPOINT = config1.get('aws', 'ENDPOINT')
PORT = config1.get('aws', 'PORT')
USR = config1.get('aws', 'USER')
PWD = config1.get('aws', 'PASSWORD')
DB = config1.get('aws', 'DATABASE')

if __name__ == '__main__':
    # Fetch last bill in the database
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
        SELECT congress, session, roll_call FROM bills
        WHERE date = (
            SELECT MAX(date) FROM bills
        )
        ;
        """
    )
    last_bill = cursor.fetchall()[-1]

    # Fetch list of senators in database
    cursor.execute(
        """
        SELECT sen_id FROM senators
        ;
        """
    )
    sen_ids = cursor.fetchall()
    sen_ids = [ sen[0] for sen in sen_ids ]

    # Make API call to ProPublica for 20 most recent votes
    config2 = configparser.ConfigParser()
    config2.read('../config.ini')
    api_key = config2.get('propublica', 'PROPUBLICA_API_KEY')
    r = requests.get(
        'https://api.propublica.org/congress/v1/senate/votes/recent.json',
        headers={'X-API-Key': api_key}
    )
    votes = r.json()['results']['votes']
    most_recent = (votes[0]['congress'], votes[0]['session'], votes[0]['roll_call'])

    # Determine if there are new votes
    if most_recent == last_bill:
        update = False
    else:
        update = True
        rcs_to_pull = []
        for vote in votes:
            congress = vote['congress']
            session = vote['session']
            rc = vote['roll_call']
            if (congress, session, rc) == last_bill:
                break # Stop when last_bill is reached
            else:
                rcs_to_pull.append((congress, session, rc))

        # Make API calls
        list_of_bills = []
        for bill in rcs_to_pull:
            r = requests.get(
                f'https://api.propublica.org/congress/v1/{bill[0]}/senate/sessions/{bill[1]}/votes/{bill[2]}.json',
                headers={'X-API-Key': api_key}
            )
            results = r.json()['results']
            list_of_bills.append(results)

        # Convert results to dictionaries to be inserted into database
        bill_to_db = []
        votes = []
        for bill in list_of_bills:
            item = bill['votes']['vote']
            if item['bill'] != {}: # Ignore nominations
                try:
                    int(item['bill']['bill_id']) # Ignore treaty votes, etc.
                except:
                    congress = item['congress']
                    session = item['session']
                    roll_call = item['roll_call']
                    date = item
                    csr_id = f'{congress}.{session}.{roll_call}'
                    bill_dict = {
                        'csr_id': csr_id,
                        'congress': congress,
                        'session': session,
                        'roll_call': roll_call,
                        'bill_id': item['bill']['bill_id'],
                        'date': vote['date']
                    }
                    bill_to_db.append(bill_dict)

                    for position in item['positions']:
                        vote_dict = {
                            'sen_id': position['member_id'],
                            'csr_id': csr_id,
                            'position': position['vote_position']
                        }
                        votes.append(vote_dict)

    # Insert bills and votes into database
    if update == True:
        for vote in votes:


    cursor.close()
    conn.close()
    