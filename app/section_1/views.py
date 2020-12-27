from flask import render_template, redirect, request, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from . import section_1
from ..models import User, Research, ScrapDate
from ..utils import countries, format_type, region, CustomError
from .forms import LoginForm
from flask import render_template, redirect, request, url_for, flash, current_app, jsonify
from datetime import datetime
from .. import config, db
from sqlalchemy import and_, or_, inspect, desc, asc
from sqlalchemy.orm import load_only
import json
import dateutil.parser

def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


@section_1.route('/edit')
@login_required
def edit():
    return render_template('section_1/edit.html')

@section_1.route('/search', methods=['GET'])
@login_required
def search():
    return render_template('section_1/search.html')

@section_1.route('/get_filters', methods=['GET'])
@login_required
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
@login_required
def search_results(page):
    # print(request.get_json())
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
        query = query.order_by(asc(Research.company_name))
        query = query.paginate(page,per_page,error_out=False)
        total_page = query.pages
        total_results = query.total

        output = []
        if query:
            for item in query.items:
                dict_t = object_as_dict(item)
                dict_t['countries'] = json.loads(dict_t['countries'])

                if dict_t['research_date']:
                    dict_t['research_date'] = str(dict_t['research_date'].strftime('%d-%m-%Y'))

                temp = item.scrap_dates.order_by(desc(ScrapDate.id)).first()

                if temp:
                    dict_t['scrap_dates'] = str(temp.dates.strftime('%d-%m-%Y'))
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
@login_required
def update():
    data = request.get_json()
    # print(data)
    if not data:
        return jsonify({"message": "No data!"}), 400

    try:
        for index, item in enumerate(data):
            obj = db.session.query(Research).get(item['id'])

            if str(item['company']).strip() != "":
                obj.company_name = item['company'].strip()
            else:
                raise CustomError("Company column must have a value!")

            if str(item['domain']).strip() != "":
                obj.domain = str(item['domain']).strip()
            else:
                raise CustomError("Domain column must have a value!")

            if item['linkedin presence'].strip().isnumeric():
                obj.linkedin_presence = int(item['linkedin presence'].strip())
            elif item['linkedin presence'] == "":
                obj.linkedin_presence = 0
            else:
                raise CustomError("Expected Number for Linkedin Presence column!")
        
            if item['industry'].strip().isnumeric()!=True:
                obj.industry = item['industry'].strip()
            else:
                raise CustomError("Industry column can't be Number!")
            
            obj.note = item['notes'].strip()

            if isinstance(item['email format'], str) and '@' in item['email format']:
                obj.email_format = item['email format'].strip()
            else:
                raise CustomError("Expected String and @ in Email Format column!")
            
            obj.format_name = item['format name'].strip()
            
            if isinstance(item['format type'], str) and item['format type'].strip() in format_type:
                obj.format_type = item['format type'].strip()
            else:
                raise CustomError("Expected Format Type to be one of these values : {}".format(format_type))

            obj.other_email_format = item['other email format(s)'].strip()
            
            if item['region'].strip() in region:
                obj.region = item['region'].strip()
            else:
                raise CustomError("Expected Region to be one of these values : {}".format(region))

            if item['research date'].strip()!="":
                obj.research_date = dateutil.parser.parse(item['research date'].strip(), dayfirst=True).date()

            countries_obj = json.loads(obj.countries)

            for key in list(countries_obj.keys()):
                if key.lower() in list(item.keys()):

                    countries_obj[key] = int(item[key.lower()])

            obj.total_count = sum(countries_obj.values())
            obj.countries=json.dumps(countries_obj)


            temp = obj.scrap_dates.order_by(desc(ScrapDate.id)).first()
            if temp:
                if temp == datetime.utcnow().date():
                    # print("Already exists")
                    db.session.add(obj)
            else:
                scrap_date = ScrapDate(dates=datetime.utcnow().date())
                obj.scrap_dates.append(scrap_date)
                db.session.add(obj)
                db.session.add(scrap_date)




        db.session.commit()
        return jsonify({"message": "Data Updated!"}), 200
    except Exception as e:
        return jsonify({"message": "Error at row {} : {}".format(index+1, e)}), 200

#edit.html
@section_1.route('/', methods=['POST'])
@login_required
def entry():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data!"}), 400
    try:
        for index, item in enumerate(data):
            result = db.session.query(Research).filter(
                        Research.company_name==item['company'].strip()).first()
            if not result:
                print(item)
                row = Research(
                        note=str(item['notes']).strip(),
                        format_name=str(item['format name']).strip(),
                        format_type=str(item['format type']).strip(),
                        other_email_format=str(item['other email format(s)']).strip(),
                        countries=json.dumps(countries)
                        )

                    
                if item['total count'].strip().isnumeric():
                    row.total_count = int(item['total count'].strip())
                elif item['total count'] == "":
                    row.total_count = 0
                else:
                    raise CustomError("Expected Number for Total Count column!")

                if str(item['company']).strip() != "":
                    row.company_name = item['company'].strip()
                else:
                    raise CustomError("Company column must have a value!")

                if str(item['domain']).strip() != "":
                    row.domain = str(item['domain']).strip()
                else:
                    raise CustomError("Domain column must have a value!")

                if item['linkedin presence'].strip().isnumeric():
                    row.linkedin_presence = int(item['linkedin presence'].strip())
                elif item['linkedin presence'] == "":
                    row.linkedin_presence = 0
                else:
                    raise CustomError("Expected Number for Linkedin Presence column!")

                if item['industry'].strip().isnumeric()!=True:
                    row.industry = item['industry'].strip()
                else:
                    raise CustomError("Industry column can't be Number!")

                if isinstance(item['email format'], str) and '@' in item['email format']:
                    row.email_format = item['email format'].strip()
                else:
                    raise CustomError("Expected String and @ in Email Format column!")

                if isinstance(item['format type'], str) and item['format type'].strip() in format_type:
                    row.format_type = item['format type'].strip()
                else:
                    raise CustomError("Expected Format Type to be one of these values : {}".format(format_type))

                if item['region'].strip() in region:
                    row.region = item['region'].strip()
                else:
                    raise CustomError("Expected Region to be one of these values : {}".format(region))

                if item['research date'].strip()!="":
                    row.research_date=dateutil.parser.parse(item['research date'].strip(), dayfirst=True).date()

                scrap_date = ScrapDate(dates=datetime.utcnow().date())
                row.scrap_dates.append(scrap_date)

                db.session.add(row)
            else:
                return jsonify({"message": "Duplicate Company at row {}".format(index+1)}), 200

        db.session.commit()
        return jsonify({"message": "Data Uploaded!"}), 200
    except Exception as e:
        return jsonify({"message": "Error at row {} : {}".format(index+1, e)}), 200

@section_1.route('/check', methods=['POST'])
@login_required
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
@login_required
def upload():
    data = request.get_json()

    if data:
        job = current_app.worker_q.enqueue('app.tasks.section_1_upload', data, countries, format_type, region, job_timeout='20m', failure_ttl=1000)
        return jsonify({ 
                        "task": 1,
                        "job_id": job.id
                        }), 200
    else:
        return jsonify({ 
                    "task": 0
                    }), 200

@section_1.route('/task_check', methods=['POST'])
@login_required
def task_check():
    data = request.get_json()
    job = current_app.worker_q.fetch_job(data["job_id"])

    if job.get_status() == "failed":
        return jsonify({
            "result": 2
        }), 200
    
    if job.result:
        return jsonify({
            "result": 1,
            "data": job.result
        }), 200

    # print(job.result)
    return jsonify({
            "result": 0,
        }), 200