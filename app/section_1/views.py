from flask import render_template, redirect, request, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from . import section_1
from ..models import User, Research, ScrapDate
from ..utils import countries
from .forms import LoginForm
from flask import render_template, redirect, request, url_for, flash, current_app, jsonify
from datetime import datetime
from .. import config, db
from sqlalchemy import and_, or_, inspect
from sqlalchemy.orm import load_only
import json

def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


@section_1.route('/edit')
def edit():
    return render_template('section_1/edit.html')

@section_1.route('/search', methods=['GET'])
def search():
    return render_template('section_1/search.html')

@section_1.route('/get_filters', methods=['GET'])
def get_filters():
    company_name = []
    industry = [ item.industry for item in db.session.query(Research.industry).distinct() ]
    country = list(countries.keys())
    domain = []
    notes = [ item.note for item in db.session.query(Research.note).distinct() ]
    for item in Research.query.all():
        company_name.append(item.company_name)
        domain.append(item.domain)
    return jsonify(
                    {
                        "company_name": company_name,
                        "industry": industry,
                        "country": country,
                        "domain": domain,
                        "notes": notes
                    } ), 200

@section_1.route('/search_results', methods=['POST'])
def search_results():
    print(request.get_json())
    data = request.get_json()
    company = data['company']
    industry = data['industry']
    domain = data['domain']
    notes = data['notes']
    research_start = datetime.strptime(data['research'].split(" - ")[0], '%m/%d/%Y').date()
    research_end = datetime.strptime(data['research'].split(" - ")[1], '%m/%d/%Y').date()
    scrap_start = datetime.strptime(data['scrap'].split(" - ")[0], '%m/%d/%Y').date()
    scrap_end = datetime.strptime(data['scrap'].split(" - ")[1], '%m/%d/%Y').date()
    scrap_results = db.session.query(ScrapDate).filter(and_(
                        ScrapDate.dates>=scrap_start,
                        ScrapDate.dates<=scrap_end))
    scrap_country = [ item.research.company_name for item in scrap_results ]
    scrap_country = list(set(scrap_country))
    print(scrap_country)
    results = Research.query.filter(or_(or_(Research.company_name.in_(company),
                            Research.domain.in_(domain)),
                            and_(or_(Research.industry.in_(industry),
                            Research.note.in_(notes)),
                            Research.company_name.in_(scrap_country),
                            and_(Research.research_date>=research_start,
                            Research.research_date<=research_end))))

    output = []
    if results:
        for item in results:
            dict_t = object_as_dict(item)
            dict_t['countries'] = json.loads(dict_t['countries'])
            dict_t['research_date'] = str(dict_t['research_date'].strftime('%m-%d-%Y'))
            dict_t['scrap_dates'] = [ str(item1.dates.strftime('%m-%d-%Y')) for item1 in item.scrap_dates ]
            output.append(dict_t.copy())
    else:
        print("not found")
    return jsonify(output), 200

@section_1.route('/', methods=['PUT'])
def update():
    data = request.get_json()
    print(data)
    if not data:
        return jsonify({"message": "No data!"}), 400


    for item in data:
        obj = Research.query.filter_by(company_name=item['company']).first()
        obj.company_name = item['company']
        obj.domain = item['domain']
        obj.linkedin_presence = item['linkedin presence']
        obj.industry = item['industry']
        obj.note = item['notes']
        obj.email_format = item['email format']
        obj.format_name = item['format name']
        obj.format_type = item['format type']
        obj.other_email_format = item['other email format(s)']
        obj.research_date = datetime.strptime(item['research date'], '%m-%d-%Y')
        countries_obj = json.loads(obj.countries)
        # print(countries_obj)
        for key in list(countries_obj.keys()):
            if key.lower() in list(item.keys()):
                # print(key)
                countries_obj[key] = int(item[key.lower()])
        print(countries_obj)
        obj.total_count = sum(countries_obj.values())
        obj.countries=json.dumps(countries_obj)



        scrap_dates = [ item1.dates for item1 in obj.scrap_dates ]
        if datetime.utcnow().date() in scrap_dates:
            print("Already exists")
            db.session.add(obj)
        else:
            scrap_date = ScrapDate(dates=datetime.utcnow().date())
            obj.scrap_dates.append(scrap_date)
            db.session.add(obj)
            db.session.add(scrap_date)



    db.session.commit()


    return jsonify({"message": "Data Updated!"}), 200


@section_1.route('/', methods=['POST'])
def entry():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data!"}), 400
    for item in data:
        result = Research.query.filter(or_(
                    Research.company_name==item['company'], Research.domain==item['domain'])).first()
        if not result:
            # print(datetime.strptime(item['research date'], '%m/%d/%Y'))
            row = Research(
                    company_name=item['company'],
                    linkedin_presence=item['linkedin presence'],
                    industry=item['industry'],
                    note=item['notes'],
                    email_format=item['email format'],
                    format_name=item['format name'],
                    format_type=item['format type'],
                    total_count=item['total count'],
                    other_email_format=item['other email format(s)'],
                    domain=item['domain'],
                    research_date=datetime.strptime(item['research date'], '%m/%d/%Y').date(),
                    countries=json.dumps(countries)
                    )
            print(row)
            db.session.add(row)
    db.session.commit()
    return jsonify({"message": "Data Uploaded!"}), 200

@section_1.route('/check', methods=['POST'])
def check():
    data = request.get_json()
    print(data)
    if data:
        if data['type'] == 'company':
            if Research.query.filter_by(company_name=data['value']).first():
                print("yup")
                return jsonify({"message": "Already Exists"}), 200
            else:
                return jsonify({"message": "Not found"}), 200
        else:
            if Research.query.filter_by(domain=data['value']).first():
                return jsonify({"message": "Already Exists"}), 200
            else:
                return jsonify({"message": "Not found"}), 200

    return jsonify({"message": "Not found!"}), 200


