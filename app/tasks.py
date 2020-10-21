import time
import pandas as pd
import os
from app import create_app, db
from app.models import Scrap
import dateutil.parser
from sqlalchemy import and_, or_, inspect
from flask import jsonify

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
app.app_context().push()

def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}

def section_2a_search(filters):
    pass
    

def section_2a_download_blast(data):
    query = Scrap.query

    start = dateutil.parser.parse(data['old_data_daterange'].split("-")[0].strip()).date()
    end = dateutil.parser.parse(data['old_data_daterange'].split("-")[1].strip()).date()
    query = query.filter(and_(Scrap.blast_date>start, Scrap.blast_date<end, Scrap.unblasted==False))
    remove = list()
    for item in query:
        remove.append(item.email)
    remove = tuple(remove)
    results = section_2a_download_normal(data)["data"]

    for index, item in enumerate(results):
        if item['email'] in remove:
            results.pop(index)
        else:
            obj = Scrap.query.get(item['id'])
            obj.blast_date = 

def section_2a_download_normal(data):
    query = Scrap.query

    if data['company']:
        filter = [ Scrap.company_name.ilike("%{}%".format(sq)) for sq in data['company'] ]
        query = query.filter(or_(*filter))

    if data['industry']:
        filter = [ Scrap.industry.ilike("%{}%".format(sq)) for sq in data['industry'] ]
        query = query.filter(or_(*filter))

    if data['country']:
        filter = [ Scrap.country.ilike("%{}%".format(sq)) for sq in data['country'] ]
        query = query.filter(or_(*filter))

    if data['email']:
        filter = [ Scrap.email.ilike("%{}%".format(sq)) for sq in data['email'] ]
        query = query.filter(or_(*filter))

    if data['first_name']:
        filter = [ Scrap.first_name.ilike("%{}%".format(sq)) for sq in data['first_name'] ]
        query = query.filter(or_(*filter))

    if data['last_name']:
        filter = [ Scrap.last_name.ilike("%{}%".format(sq)) for sq in data['last_name'] ]
        query = query.filter(or_(*filter))

    if data['position']:
        filter = [ Scrap.position.ilike("%{}%".format(sq)) for sq in data['position'] ]
        query = query.filter(or_(*filter))

    if data['validity_grade']:
        query = query.filter(Scrap.validity_grade.in_(data['validity_grade']))
    
    blast_start = dateutil.parser.parse(data['blast_daterange'].split("-")[0].strip()).date()
    blast_end = dateutil.parser.parse(data['blast_daterange'].split("-")[1].strip()).date()
    # print(blast_start)
    if data['unblasted']=='1':
        query = query.filter(Scrap.unblasted==True)
    else:
        query = query.filter(Scrap.unblasted==False)
        query = query.filter(and_(Scrap.blast_date>blast_start, Scrap.blast_date<blast_end))


    upload_start = dateutil.parser.parse(data['upload_daterange'].split("-")[0].strip()).date()
    upload_end = dateutil.parser.parse(data['upload_daterange'].split("-")[1].strip()).date()

    query = query.filter(and_(Scrap.upload_date>upload_start, Scrap.upload_date<upload_end))
    query = query.filter(and_(Scrap.percentage>=data['p_start'], Scrap.percentage<=data['p_end']))
    total_results = query.count()
    results = []

    for item in query:
        tmp = object_as_dict(item)
        if tmp['blast_date'] is not None:
            tmp['blast_date'] = str(tmp['blast_date'].strftime('%m-%d-%Y'))
        else:
            tmp['blast_date'] = ""
        
        tmp['upload_date'] = str(tmp['upload_date'].strftime('%m-%d-%Y'))
        results.append(tmp.copy())
    return {
        "data": results,
        "total_results": total_results
    }


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
                # print(row['Blast Date'])
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