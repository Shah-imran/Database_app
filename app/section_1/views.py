from flask import render_template, redirect, request, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from . import section_1
from ..models import User, Research, ScrapDate
from ..utils import countries
from .forms import LoginForm
from flask import render_template, redirect, request, url_for, flash, current_app, jsonify
from datetime import datetime
from .. import config, db
from sqlalchemy import and_, or_, inspect, desc
from sqlalchemy.orm import load_only
import json
import dateutil.parser

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
    # company_name = []
    # industry = [ item.industry for item in db.session.query(Research.industry).distinct() ]
    country = list(countries.keys())
    # domain = []
    # notes = [ item.note for item in db.session.query(Research.note).distinct() ]
    # for item in Research.query.all():
    #     company_name.append(item.company_name)
    #     domain.append(item.domain)
    return jsonify({
                        "country": country
                    }), 200

@section_1.route('/search_results', methods=['POST'], defaults={"page": 1})
@section_1.route('/search_results/<int:page>', methods=['POST'])
def search_results(page):
    print(request.get_json())
    data = request.get_json()
    if data:
        per_page = int(data['per_page'])
        query = db.session.query(Research)

        company = data['company']
        industry = data['industry']
        domain = data['domain']
        notes = data['notes']
        research_start = dateutil.parser.parse(data['research'].split(" - ")[0].strip()).date()
        research_end = dateutil.parser.parse(data['research'].split(" - ")[1].strip()).date()
        scrap_start = dateutil.parser.parse(data['scrap'].split(" - ")[0].strip()).date()
        scrap_end = dateutil.parser.parse(data['scrap'].split(" - ")[1].strip()).date()
        
        if data['company']:
            filter = [ Research.company_name.ilike("%{}%".format(sq)) for sq in data['company'] ]
            query = query.filter(or_(*filter))

        if data['industry']:
            filter = [ Research.industry.ilike("%{}%".format(sq)) for sq in data['industry'] ]
            query = query.filter(or_(*filter))

        if data['domain']:
            filter = [ Research.domain.ilike("%{}%".format(sq)) for sq in data['domain'] ]
            query = query.filter(or_(*filter))

        if data['notes']:
            filter = [ Research.notes.ilike("%{}%".format(sq)) for sq in data['notes'] ]
            query = query.filter(or_(*filter))
        
        if data['region']:
            filter = [ Research.region.ilike("%{}%".format(sq)) for sq in data['region'] ]
            query = query.filter(or_(*filter))

        query = query.filter(and_(Research.research_date>research_start, Research.research_date<research_end))
        query = query.join(ScrapDate).filter(and_(ScrapDate.dates>scrap_start, ScrapDate.dates<scrap_end))

        query = query.paginate(page,per_page,error_out=False)
        total_page = query.pages
        total_results = query.total

        output = []
        if query:
            for item in query.items:
                dict_t = object_as_dict(item)
                dict_t['countries'] = json.loads(dict_t['countries'])

                if dict_t['research_date']:
                    dict_t['research_date'] = str(dict_t['research_date'].strftime('%m-%d-%Y'))

                temp = item.scrap_dates.order_by(desc(ScrapDate.id)).first()

                if temp:
                    dict_t['scrap_dates'] = str(temp.dates.strftime('%m-%d-%Y'))
                else:
                    dict_t['scrap_dates'] = ""
                output.append(dict_t.copy())

    return jsonify({
        "data": output,
        "total_page": total_page,
        "current_page": page,
        "total_results": total_results,
        "has_next": query.has_next,
        "has_prev": query.has_prev
    }), 200

@section_1.route('/', methods=['PUT'])
def update():
    data = request.get_json()
    # print(data)
    if not data:
        return jsonify({"message": "No data!"}), 400


    for item in data:
        obj = db.session.query(Research).filter_by(company_name=item['company']).first()
        obj.company_name = item['company'].strip()
        obj.domain = item['domain'].strip()
        obj.linkedin_presence = item['linkedin presence'].strip()
        obj.industry = item['industry'].strip()
        obj.note = item['notes'].strip()
        obj.email_format = item['email format'].strip()
        obj.format_name = item['format name'].strip()
        obj.format_type = item['format type'].strip()
        obj.other_email_format = item['other email format(s)'].strip()
        if item['research date'].strip()!='':
            obj.research_date = datetime.strptime(item['research date'], '%m-%d-%Y')
        countries_obj = json.loads(obj.countries)
        # print(countries_obj)
        for key in list(countries_obj.keys()):
            if key.lower() in list(item.keys()):
                # print(key)
                countries_obj[key] = int(item[key.lower()])
        # print(countries_obj)
        obj.total_count = sum(countries_obj.values())
        obj.countries=json.dumps(countries_obj)


        temp = obj.scrap_dates.order_by(desc(ScrapDate.id)).first()
        if temp:
            if temp == datetime.utcnow().date():
                print("Already exists")
                db.session.add(obj)
        else:
            scrap_date = ScrapDate(dates=datetime.utcnow().date())
            obj.scrap_dates.append(scrap_date)
            db.session.add(obj)
            db.session.add(scrap_date)




    db.session.commit()


    return jsonify({"message": "Data Updated!"}), 200

#edit.html
@section_1.route('/', methods=['POST'])
def entry():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data!"}), 400
    for item in data:
        result = db.session.query(Research).filter(
                    Research.company_name==item['company']).first()
        if not result:
            # print(datetime.strptime(item['research date'], '%m/%d/%Y'))
            row = Research(
                    company_name=item['company'].strip(),
                    linkedin_presence=item['linkedin presence'].strip(),
                    industry=item['industry'].strip(),
                    region=item['region'].strip(),
                    note=item['notes'].strip(),
                    email_format=item['email format'].strip(),
                    format_name=item['format name'].strip(),
                    format_type=item['format type'].strip(),
                    total_count=item['total count'].strip(),
                    other_email_format=item['other email format(s)'].strip(),
                    domain=item['domain'].strip(),
                    countries=json.dumps(countries)
                    )
            if item['research date'].strip()!="":
                row.research_date=dateutil.parser.parse(item['research date'].strip()).date()

            scrap_date = ScrapDate(dates=datetime.utcnow().date())
            row.scrap_dates.append(scrap_date)
            # print(row)
            db.session.add(row)
            db.session.add(scrap_date)
    db.session.commit()
    return jsonify({"message": "Data Uploaded!"}), 200

@section_1.route('/check', methods=['POST'])
def check():
    data = request.get_json()
    print(data)
    if data:
        if data['type'] == 'company':
            if db.session.query(Research).filter_by(company_name=data['value'].strip()).first():
                print("yup")
                return jsonify({"message": "Already Exists"}), 200
            else:
                return jsonify({"message": "Not found"}), 200
        else:
            if db.session.query(Research).filter_by(domain=data['value'].strip()).first():
                return jsonify({"message": "Already Exists"}), 200
            else:
                return jsonify({"message": "Not found"}), 200

    return jsonify({"message": "Not found!"}), 200

@section_1.route('/upload', methods=['POST'])
def upload():
    data = request.get_json()
    fields = ["Company", "Linkedin Presence", "Industry", 
                "Notes", "Email Format", "Format Name", "Format Type",  "Other Email Format(s)",
                "Region", "Total Count", "Domain", "Research Date"]

    results = ""
    for item in data:
        if item['meta']['fields'] == fields:
            job = current_app.worker_q.enqueue('app.tasks.section_1_upload', item, countries, job_timeout='20m', failure_ttl=1000)
            results += "{}: File added to upload task queue\n".format(item['filename'])

        else:
            results += "{}: Header's doesn't match\n".format(item['filename'])
    return jsonify(results), 200
