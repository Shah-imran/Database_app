import time
import pandas as pd
import os
from app import create_app, db
from app.models import Scrap, Research, ScrapDate
import dateutil.parser
from sqlalchemy import and_, or_, inspect, func, case
from sqlalchemy.sql import label
from flask import jsonify
from datetime import datetime
import math
import json

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
app.app_context().push()

def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}

def section_2a_search(filters):
    pass

def section_2b_download(data):
    query = db.session.query(Scrap)

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

    if data['sent']=='1':
        query = query.filter(Scrap.sent==True)
    else:
        query = query.filter(Scrap.sent==False)

    if data['delivered']=='1':
        query = query.filter(Scrap.delivered==True)
    else:
        query = query.filter(Scrap.delivered==False)

    if data['soft_bounces']=='1':
        query = query.filter(Scrap.soft_bounces==True)
    else:
        query = query.filter(Scrap.soft_bounces==False)

    if data['hard_bounces']=='1':
        query = query.filter(Scrap.hard_bounces==True)
    else:
        query = query.filter(Scrap.hard_bounces==False)

    if data['opened']=='1':
        query = query.filter(Scrap.opened==True)
    else:
        query = query.filter(Scrap.opened==False)

    if data['unsubscribed']=='1':
        query = query.filter(Scrap.unsubscribed==True)
    else:
        query = query.filter(Scrap.unsubscribed==False)

    upload_start = dateutil.parser.parse(data['upload_daterange'].split("-")[0].strip()).date()
    upload_end = dateutil.parser.parse(data['upload_daterange'].split("-")[1].strip()).date()

    query = query.filter(and_(Scrap.upload_date>upload_start, Scrap.upload_date<upload_end))
    query = query.filter(and_(Scrap.percentage>=data['p_start'], Scrap.percentage<=data['p_end']))
    total_results = query.count()
    results = []

    for item in query:
        tmp = {
            "id": item.id,
            "country": item.country,
            "email": item.email,
            "first_name": item.first_name,
            "last_name": item.last_name,
            "industry": item.industry,
            "validity_grade": item.validity_grade,
            "link": item.link,
            "position": item.position,
            "company_name": item.company_name,
            "sent": item.sent,
            "delivered": item.delivered,
            "soft_bounces": item.soft_bounces,
            "hard_bounces": item.hard_bounces,
            "opened": item.opened,
            "unsubscribed": item.unsubscribed
        }
        if item.blast_date is not None:
            tmp['blast_date'] = str(item.blast_date.strftime('%m-%d-%Y'))
        else:
            tmp['blast_date'] = ""
        
        tmp['upload_date'] = str(item.upload_date.strftime('%m-%d-%Y'))

        results.append(tmp.copy())
        
    return {
        "data": results,
        "headers": list(results[0].keys()),
        "total_results": total_results,
    }


def section_2a_download_blast(data):
    query = db.session.query(Scrap).with_entities(Scrap.email)

    start = dateutil.parser.parse(data['old_data_daterange'].split("-")[0].strip()).date()
    end = dateutil.parser.parse(data['old_data_daterange'].split("-")[1].strip()).date()
    query = query.filter(and_(Scrap.blast_date>start, Scrap.blast_date<end, Scrap.unblasted==False))

    remove = [ item.email for item in query ]
    remove = tuple(remove)
    data = section_2a_download_normal(data)
    results = data["data"]
    total_results = data["total_results"]
    for index, item in enumerate(results):
        if item['email'] in remove:
            results.pop(index)
            # print("removing")
        else:
            obj = db.session.query(Scrap).get(item['id'])
            obj.blast_date = datetime.utcnow().date()
            obj.unblasted = False
            db.session.add(obj)

    db.session.commit()
    new_total_results = len(results)
    # print(new_total_results, total_results)

    return {
        "data": results,
        "headers": list(results[0].keys()),
        "total_results": total_results,
        "new_total_results": new_total_results,
        "type": "blast"
    }

def section_2a_download_normal(data):
    query = db.session.query(Scrap).with_entities(
        Scrap.id, Scrap.country, Scrap.company_name, Scrap.email, Scrap.first_name, Scrap.last_name, Scrap.industry, Scrap.validity_grade,
        Scrap.link, Scrap.position)

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
        tmp = {
            "id": item.id,
            "country": item.country,
            "email": item.email,
            "first_name": item.first_name,
            "last_name": item.last_name,
            "industry": item.industry,
            "validity_grade": item.validity_grade,
            "link": item.link,
            "position": item.position,
            "company_name": item.company_name
        }

        results.append(tmp.copy())
    return {
        "data": results,
        "headers": list(results[0].keys()),
        "total_results": total_results,
        "type": "normal"
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

def section_2b_upload(data):
    filename = data['filename']
    df = pd.DataFrame(data['data'])
    print("starting upload: {} {}".format(filename, len(df)))
    
    for index, row in df.iterrows():
        date = dateutil.parser.parse(row['ts']).date()
        obj = db.session.query(Scrap).filter(and_(Scrap.email==row['email'], 
                                        Scrap.blast_date==date)).first()
        if obj:
            if row['st_text'] == "Sent":
                obj.sent = True
            elif row['st_text'] == "Delivered":
                obj.delivered = True
            elif row['st_text'] == "Soft bounce":
                obj.soft_bounces = True
            elif row['st_text'] == "Hard bounce":
                obj.hard_bounces = True
            elif row['st_text'] == "Opened":
                obj.opened = True
            elif row['st_text'] == "Unsubscribed":
                obj.unsubscribed == True
            
            db.session.add(obj)
    db.session.commit()
    print("Finished uploading: {}".format(filename))

def section_3_search_results(data):
    per_page = int(data['per_page'])
    page = data['page']

    query = db.session.query(Scrap)

    if data['company']:
        filter = [ Scrap.company_name.ilike("%{}%".format(sq)) for sq in data['company'] ]
        query = query.filter(or_(*filter))

    if data['industry']:
        filter = [ Scrap.industry.ilike("%{}%".format(sq)) for sq in data['industry'] ]
        query = query.filter(or_(*filter))

    blast_start = dateutil.parser.parse(data['blast_daterange'].split("-")[0].strip()).date()
    blast_end = dateutil.parser.parse(data['blast_daterange'].split("-")[1].strip()).date()
    if data['unblasted']:
        query = query.filter(Scrap.unblasted==data['unblasted'])
    else:
        query = query.filter(and_(Scrap.blast_date>blast_start, Scrap.blast_date<blast_end))
        query = query.filter(Scrap.unblasted==data['unblasted'])

    upload_start = dateutil.parser.parse(data['upload_daterange'].split("-")[0].strip()).date()
    upload_end = dateutil.parser.parse(data['upload_daterange'].split("-")[1].strip()).date()

    query = query.filter(and_(Scrap.upload_date>upload_start, Scrap.upload_date<upload_end))

    validity_grade = {}
    if data['validity_grade']:
        for item in data['validity_grade']:
            validity_grade[item] = 0 

    country = {}  
    if data['country']:
        for item in data['country']:
            country[item] = 0 
        filter = [ Scrap.country.ilike("%{}%".format(sq)) for sq in data['country'] ]
        query = query.filter(or_(*filter))

    

    t_query = query.with_entities(
                        label('blast_date', Scrap.blast_date), 
                        label('upload_date', Scrap.upload_date), 
                        label('industry', Scrap.industry), 
                        label('company_name', Scrap.company_name), 
                        label('total_count', func.count()),
                        label('unblasted', func.count().filter(Scrap.unblasted==data['unblasted'])),
                        label('sent', func.count().filter(Scrap.sent==data['sent'])), 
                        label('delivered', func.count().filter(Scrap.delivered==data['delivered'])), 
                        label('soft_bounces', func.count().filter(Scrap.soft_bounces==data['soft_bounces'])), 
                        label('hard_bounces', func.count().filter(Scrap.hard_bounces==data['hard_bounces'])), 
                        label('opened', func.count().filter(Scrap.opened==data['opened'])), 
                        label('unsubscribed', func.count().filter(Scrap.unsubscribed==data['unsubscribed'])) 
                            )
    
    t_query = t_query.group_by(Scrap.company_name).paginate(page,per_page,error_out=False)
    total_page = t_query.pages
    total_results = t_query.total
    print(total_page, total_results)
    results = {}
    company = []
    for index, item in enumerate(t_query.items):
        results[item.company_name] = { 
                    "blast_date": str(item.blast_date.strftime('%m-%d-%Y')) if item.blast_date is not None else "",
                    "upload_date": str(item.upload_date.strftime('%m-%d-%Y')),
                    "industry": item.industry,
                    "total_count": item.total_count,
                    "country": country.copy(),
                    "validity_grade": validity_grade.copy(),
                    "unblasted": item.unblasted,
                    "sent": item.sent,
                    "delivered": item.delivered,
                    "soft_bounces": item.soft_bounces,
                    "hard_bounces": item.hard_bounces,
                    "opened": item.opened,
                    "unsubscribed": item.unsubscribed
                                    } 
        company.append(item.company_name)
    # print(len(company))
    # print(query.count())
    if company:
        filter = [ Scrap.company_name.ilike("%{}%".format(sq)) for sq in company ]
        query = query.filter(or_(*filter))
    # print(query.count())
    
    t2_query = query.with_entities(
                    label('company_name', Scrap.company_name), 
                    label('country', Scrap.country), 
                    label('country_count', func.count()) 
                        )

    for index, item in enumerate(t2_query.group_by(Scrap.company_name, Scrap.country)):
        results[item.company_name]['country'][item.country] = item.country_count 

    t2_query = query.with_entities(
                    label('company_name', Scrap.company_name), 
                    label('country', Scrap.country), 
                    label('validity_grade', Scrap.validity_grade),
                    label('count',func.count()) 
                        )

    for index, item in enumerate(t2_query.group_by(Scrap.company_name, Scrap.country, Scrap.validity_grade)):
        if item.validity_grade in validity_grade:
            results[item.company_name]['validity_grade'][item.validity_grade] = item.count 

    # print(results)
    # print(time.perf_counter())



    return {
            "data": results,
            "total_page": total_page,
            "current_page": page,
            "total_results": total_results,
            "has_next": t_query.has_next,
            "has_prev": t_query.has_prev
        }

def section_1_upload(data, countries):
    filename = data['filename']
    print("starting upload: {}".format(filename))
    for item in data['data']:
        result = db.session.query(Research).filter(
                    Research.company_name==item['Company']).first()
        if not result:
            # print(datetime.strptime(item['research date'], '%m/%d/%Y'))
            row = Research(
                    company_name=item['Company'].strip(),
                    linkedin_presence=item['Linkedin Presence'].strip(),
                    industry=item['Industry'].strip(),
                    region=item['Region'].strip(),
                    note=item['Notes'].strip(),
                    email_format=item['Email Format'].strip(),
                    format_name=item['Format Name'].strip(),
                    format_type=item['Format Type'].strip(),
                    total_count=item['Total Count'].strip(),
                    other_email_format=item['Other Email Format(s)'].strip(),
                    domain=item['Domain'].strip(),
                    countries=json.dumps(countries)
                    )
            if item['Research Date'].strip()!="":
                row.research_date=dateutil.parser.parse(item['Research Date'].strip()).date()

            scrap_date = ScrapDate(dates=datetime.utcnow().date())
            row.scrap_dates.append(scrap_date)
            # print(row)
            db.session.add(row)
            db.session.add(scrap_date)
    db.session.commit()
    print("Finished upload: {}".format(filename))