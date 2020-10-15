import time
import pandas as pd
import os
from app import create_app, db
from app.models import Scrap
import dateutil.parser
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
app.app_context().push()


def section_2a_upload(data):
    filename = data['filename']
    print("starting upload: {}".format(filename))
    df = pd.DataFrame(data['data'])
    df.insert(4, "Percentage", 0) 

    groups = df.groupby(['Company', 'Country'])
    for group_name, df_group in groups:
        # print('Group Name: {}'.format(group_name))
        len_group = len(df_group)
        increment = 100/len_group
        sum = 0
        for row_index, row in df_group.iterrows():
            sum+=increment
            row['Percentage'] = round(sum, 2)

            if row['Blast Date']:

                row['Blast Date'] = dateutil.parser.parse(row['Blast Date'].strip()).date()
                scrap = Scrap(
                            country = row['Country'].strip(),
                            email = row['Email'].strip(),
                            first_name = row['First Name'].strip(),
                            last_name = row['Last Name'].strip(),
                            industry = row['Industry'].strip(),
                            link = row['Link'].strip(),
                            position = row['Position'].strip(),
                            validity_grade = row['Validity Grade'].strip(),
                            company_name = row['Company'].strip(),
                            percentage = row['Percentage'],
                            blast_date=row['Blast Date'],
                            unblasted=False
                        )
            else:

                scrap = Scrap(
                            country = row['Country'].strip(),
                            email = row['Email'].strip(),
                            first_name = row['First Name'].strip(),
                            last_name = row['Last Name'].strip(),
                            industry = row['Industry'].strip(),
                            link = row['Link'].strip(),
                            position = row['Position'].strip(),
                            validity_grade = row['Validity Grade'].strip(),
                            company_name = row['Company'].strip(),
                            percentage = row['Percentage']
                        )
            db.session.add(scrap)

    db.session.commit()
    print("Finished uploading: {}".format(filename))