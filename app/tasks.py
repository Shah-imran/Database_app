import time
import pandas as pd
import numpy as np
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
            tmp['blast_date'] = str(item.blast_date.strftime('%d-%m-%Y'))
        else:
            tmp['blast_date'] = ""
        
        tmp['upload_date'] = str(item.upload_date.strftime('%d-%m-%Y'))

        results.append(tmp.copy())
        
    return {
        "type": 'download',
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
    print("starting upload...")
    try:
        result = {'type': "upload"}
        df = pd.DataFrame(data)
        email_error = df.index[~df['Email'].str.contains("@", na=False)].tolist()
        email_error = [ str(item+2) for item in email_error ]
        
        if email_error:
            result['status'] = "Unexpected Values at Email Column : {}".format(", ".join(email_error))
            return result

        industry_error = df.index[df['Industry'].apply(lambda x: not isinstance(x, str))].tolist()
        industry_error = [ str(item+2) for item in industry_error ]
        
        if industry_error:
            result['status'] = "Unexpected Values at Industry Column : {}".format(", ".join(industry_error))
            return result
        
        validity_error = df.index[(df['Validity Grade']!="A") & (df['Validity Grade']!="B")]
        validity_error = [ str(item+2) for item in validity_error ]

        if validity_error:
            result['status'] = "Unexpected Values at Industry Column : {}".format(", ".join(validity_error))
            return result
        

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
                obj = db.session.query(Scrap).filter(and_(Scrap.email==row['Email'].strip(), 
                        Scrap.upload_date==datetime.utcnow().date())).first()
                if not obj:
                    if row['Blast Date']:

                        row['Blast Date'] = dateutil.parser.parse(row['Blast Date'].strip(), dayfirst=True).date()

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
                                    upload_date = datetime.utcnow().date(),
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
                                    upload_date = datetime.utcnow().date(),
                                    percentage = row['Percentage']
                                )
                    db.session.add(scrap)
                else:
                    result['status'] = "Already Exists for today : {}".format(row['Email'].strip())
                    return result


        db.session.commit()
        print("Finished uploading...")
        result['status'] = "Finished uploading"
        return result
    except Exception as e:
        print("Failed uploading : {}".format(e))
        result['status'] = "Failed uploading : {}".format(e)
        return result

def section_2b_upload(data):
    filename = data['filename']
    df = pd.DataFrame(data['data'])
    print("starting upload: {} {}".format(filename, len(df)))
    sent = 0
    delivered = 0
    soft_bounces = 0
    hard_bounces = 0
    opened = 0
    unsubscribed = 0
    for index, row in df.iterrows():
        date = dateutil.parser.parse(row['ts'].split(" ")[0], dayfirst=True).date()

        obj = db.session.query(Scrap).filter(and_(Scrap.email==row['email'], 
                                        Scrap.blast_date==date)).first()
        if obj:

            if row['st_text'] == "Sent":
                obj.sent = True
                sent+=1
            elif row['st_text'] == "Delivered":
                obj.delivered = True
                delivered+=1
            elif row['st_text'] == "Soft bounce":
                obj.soft_bounces = True
                soft_bounces+=1 
            elif row['st_text'] == "Hard bounce":
                obj.hard_bounces = True
                hard_bounces+=1 
            elif row['st_text'] == "Opened":
                obj.opened = True
                opened+=1 
            elif row['st_text'] == "Unsubscribed":
                obj.unsubscribed == True
                unsubscribed+=1

            
            db.session.add(obj)
    db.session.commit()
    print("Finished uploading: {}".format(filename))
    return {
        "type": "upload",
        "sent": sent,
        "delivered": delivered,
        "soft_bounces": soft_bounces,
        "hard_bounces": hard_bounces,
        "opened": opened,
        "unsubscribed": unsubscribed
        }

def check(val):
    return True if val==1 else False

def section_3_search_results(data):
    # print(data)
    per_page = int(data['per_page'])
    page = data['page']

    query = db.session.query(Scrap)

    upload_start = dateutil.parser.parse(data['upload_daterange'].split("-")[0].strip()).date()
    upload_end = dateutil.parser.parse(data['upload_daterange'].split("-")[1].strip()).date()

    query = query.filter(and_(Scrap.upload_date>upload_start, Scrap.upload_date<upload_end))

    blast_start = dateutil.parser.parse(data['blast_daterange'].split("-")[0].strip()).date()
    blast_end = dateutil.parser.parse(data['blast_daterange'].split("-")[1].strip()).date()


    query = query.filter(or_(and_(Scrap.blast_date>blast_start, Scrap.blast_date<blast_end), Scrap.unblasted==True))


    if data['company']:
        filter = [ Scrap.company_name.ilike("%{}%".format(sq)) for sq in data['company'] ]
        query = query.filter(or_(*filter))

    if data['industry']:
        filter = [ Scrap.industry.ilike("%{}%".format(sq)) for sq in data['industry'] ]
        query = query.filter(or_(*filter))


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

    unblasted = check(data['unblasted'])
    sent = check(data['sent'])
    delivered = check(data['delivered'])
    soft_bounces = check(data['soft_bounces'])
    hard_bounces = check(data['hard_bounces'])
    opened = check(data['opened'])
    unsubscribed = check(data['unsubscribed'])
    
    t_query = query.with_entities(
                label('company_name', Scrap.company_name), 
                label('total_count', func.count()),
                label('unblasted', func.count().filter(Scrap.unblasted == unblasted)),
                label('sent', func.count().filter(Scrap.sent == sent)), 
                label('delivered', func.count().filter(Scrap.delivered == delivered)), 
                label('soft_bounces', func.count().filter(Scrap.soft_bounces == soft_bounces)), 
                label('hard_bounces', func.count().filter(Scrap.hard_bounces == hard_bounces)), 
                label('opened', func.count().filter(Scrap.opened == opened)), 
                label('unsubscribed', func.count().filter(Scrap.unsubscribed == unsubscribed)) 
            )

    t_query = t_query.group_by(Scrap.company_name).paginate(page,per_page,error_out=False)

    total_page = t_query.pages
    total_results = t_query.total
    # print(total_page, total_results)
    results = {}
    company = []
    
    for index, item in enumerate(t_query.items):

        temp = query.filter(Scrap.company_name==item.company_name).first()
        results[item.company_name] = { 
                    "blast_date": str(temp.blast_date.strftime('%d-%m-%Y')) if temp.blast_date is not None else "",
                    "upload_date": str(temp.upload_date.strftime('%d-%m-%Y')),
                    "industry": temp.industry,
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

    if company:
        filter = [ Scrap.company_name.ilike("%{}%".format(sq)) for sq in company ]
        query = query.filter(or_(*filter))

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
            results[item.company_name]['validity_grade'][item.validity_grade] = item.count + results[item.company_name]['validity_grade'][item.validity_grade]




    return {
            "data": results,
            "total_page": total_page,
            "current_page": page,
            "total_results": total_results,
            "has_next": t_query.has_next,
            "has_prev": t_query.has_prev
        }

def section_1_upload(data, countries, format_type, region):
    print("starting upload ...")
    try:
        for index, item in enumerate(data):
            result = db.session.query(Research).filter(
                        Research.company_name==item['Company'].strip()).first()
            if not result:
                # print("Index - {}".format(index), end="\r")
                row = Research(
                        note=str(item['Notes']).strip(),
                        format_name=str(item['Format Name']).strip(),
                        format_type=str(item['Format Type']).strip(),
                        other_email_format=str(item['Other Email Format(s)']).strip(),
                        countries=json.dumps(countries)
                        )

                if item['Total Count'].strip().isnumeric():
                    row.total_count = int(item['Total Count'])
                elif item['Total Count'] == "":
                    row.total_count = 0
                else:
                    raise CustomError("Expected Number for Total Count column!")
                    
                if str(item['Company']).strip() != "":
                    row.company_name = item['Company'].strip()
                else:
                    raise CustomError("Company column must have a value!")

                if str(item['Domain']).strip() != "":
                    row.domain = str(item['Domain']).strip()
                else:
                    raise CustomError("Domain column must have a value!")

                if item['Linkedin Presence'].strip().isnumeric():
                    row.linkedin_presence = int(item['Linkedin Presence'].strip())
                elif item['Linkedin Presence'] == "":
                    row.linkedin_presence = 0
                else:
                    raise CustomError("Expected Number for Linkedin Presence column!")

                if isinstance(item['Industry'], str) and item['Industry'].strip().isnumeric()!=True:
                    row.industry = item['Industry'].strip()
                else:
                    raise CustomError("Industry column can't be Number!")

                if isinstance(item['Email Format'], str) and '@' in item['Email Format']:
                    row.email_format = item['Email Format'].strip()
                else:
                    raise CustomError("Expected String and @ in Email Format column!")

                if isinstance(item['Format Type'], str) and item['Format Type'].strip() in format_type:
                    row.format_type = item['Format Type'].strip()
                else:
                    raise CustomError("Got: {}\nExpected Format Type to be one of these values : {}".format(item['Format Type'].strip(),
                        format_type))

                if item['Region'].strip() in region:
                    row.region = item['Region'].strip()
                else:
                    raise CustomError("Expected Region to be one of these values : {}".format(region))



                if item['Research Date'].strip()!="":
                    row.research_date = dateutil.parser.parse(item['Research Date'].strip(), dayfirst=True).date()
                else:
                    row.research_date = datetime.utcnow().date()

                # scrap_date = ScrapDate(dates=datetime.utcnow().date())
                # row.scrap_dates.append(scrap_date)

                db.session.add(row)
            else:
                return "Duplicate Company at row {}".format(index+2)

        db.session.commit()
        print("Finished uploading...")
        return "Finished uploading"
    except Exception as e:
        print("Failed uploading : {}".format(e))
        return "Error at row {} : {}".format(index+2, e)


class CustomError(Exception):
    pass