import requests
import json
import configparser
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime

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
    if most_recent != last_bill:
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
        new_votes = []
        new_sens = []
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
                    bill_tup = (
                        csr_id,
                        congress,
                        session,
                        roll_call,
                        item['bill']['bill_id'],
                        vote['date']
                    )
                    bill_to_db.append(bill_tup)

                    for position in item['positions']:
                        vote_tup = (
                            position['member_id'],
                            csr_id,
                            position['vote_position']
                        )
                        new_votes.append(vote_tup)
                        if position['member_id'] not in sen_ids:
                            new_sens.append(position['member_id'])
    else:
        update = False
        list_of_bills = []
        new_votes = []

    # Get newest list of senators from latest bill
    if len(list_of_bills) != 0:
        current_congress = [ mem['member_id'] for mem in list_of_bills[0]['votes']['vote']['positions'] ]
    else:
        current_congress = []

    # Compare current members to database members and add new member
    members_to_add = []
    for member in current_congress:
        if member not in sen_ids:
            members_to_add.append(member)

    # Get senator data from API
    sen_dicts = []
    for mem in members_to_add:
        r = requests.get(
                f'https://api.propublica.org/congress/v1/members/{mem}.json',
                headers={'X-API-Key': api_key}
            )
        results = r.json()['results']

    # Using function from scraping notebook
    def get_senators(members):
        senators = []
        for member in members:
            senator = (
                member['id'],
                member['first_name'],
                member['last_name'],
                member['party'],
                member['gender'],
                member['state'],
            )
            senators.append(senator)
        return senators

    new_sens = get_senators(sen_dicts)
    if len(new_sens) != 0:
        update_sen = True
    else:
        update_sen = False

    # Prepare queries
    add_senator = (
        """
        INSERT INTO senators (sen_id, f_name, l_name, party, gender, state)
        VALUES (%s, %s, %s, %s, %s, %s);
        """
    )

    add_bill = (
        """
        INSERT INTO bills (csr_id, congress, session, roll_call, bill_id, date)
        VALUES (%s, %s, %s, %s, %s, %s);
        """
    )

    add_vote = (
        """
        INSERT INTO votes (sen_id, csr_id, position)
        VALUES (%s, %s, %s);
        """
    )

    # Insert bills and votes into database
    if update == True:
        # Must add bills first as it is a FK for votes
        cursor.executemany(add_bill, bill_to_db)
        cursor.executemany(add_vote, new_votes)
        if update_sen == True:
            cursor.executemany(add_senator, new_sens)

    cursor.close()
    conn.close()

    # Write update date to file
    f = open('../recent_update.txt', 'a')
    f.write(f'Date: {datetime.date(datetime.now())}, Update: {update}, New Senators: {update_sen}\n')
    f.close()

    