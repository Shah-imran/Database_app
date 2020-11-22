from flask import render_template, redirect, request, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from . import section_2
from ..models import User, Research, ScrapDate, Scrap
from rq.registry import StartedJobRegistry, FinishedJobRegistry, FailedJobRegistry
from ..utils import countries
from flask import render_template, redirect, request, url_for, flash, current_app, jsonify
from datetime import datetime
from .. import config, db
from sqlalchemy import and_, or_, inspect, desc, asc
from sqlalchemy.orm import load_only
import json
import pandas as pd
import dateutil.parser
import math


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


@section_2.route('/2a', methods=['GET'])
def _2a():
    return render_template('section_2/2a.html')

@section_2.route('/2b', methods=['GET'])
def _2b():
    return render_template('section_2/2b.html')

@section_2.route('/2b/task_check', methods=['POST'])
def task_check_2b():
    data = request.get_json()
    job = current_app.worker_q.fetch_job(data["job_id"])

    # print(job.get_status())
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

@section_2.route('/2b/download', methods=['POST'])
def download_2b():
    data = request.get_json()
    # print(data)
    if data:
        job = current_app.worker_q.enqueue('app.tasks.section_2b_download', data, job_timeout='20m', failure_ttl=1000)
        return jsonify({ 
                    "task": 1,
                    "job_id": job.id
                    }), 200
    else:
        return jsonify({ 
                    "task": 0
                    }), 200


@section_2.route('/2a/task_check', methods=['POST'])
def task_check_2a():
    data = request.get_json()
    job = current_app.worker_q.fetch_job(data["job_id"])

    # print(job.get_status())
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

@section_2.route('/2a/download', methods=['POST'])
def download_2a():
    data = request.get_json()
    # print(data)
    if data:
        if "old_data_daterange" in data:
            print("daterange")
            job = current_app.worker_q.enqueue('app.tasks.section_2a_download_blast', data, job_timeout='20m', failure_ttl=1000)
        else:
            print("no daterange")
            job = current_app.worker_q.enqueue('app.tasks.section_2a_download_normal', data, job_timeout='20m', failure_ttl=1000)
        return jsonify({ 
                    "task": 1,
                    "job_id": job.id
                    }), 200
    else:
        return jsonify({ 
                    "task": 0
                    }), 200


@section_2.route('/2a/update', methods=['PUT'])
def update_2a():
    data = request.get_json()
    print(len(data))
    if data:
        for item in data:
            obj = db.session.query(Scrap).get(item['id'])
            if obj:
                if item['blast date']!="":
                    obj.blast_date = dateutil.parser.parse(item['blast date']).date()
                obj.company = item['company'].strip()
                obj.country = item['country'].strip()
                
                if "@" in item['email'].strip():
                    obj.email = item['email'].strip()
                else:
                    return jsonify({"message": "Emails must have '@' in it {}".format(item['id'])}), 200
                
                obj.first_name = item['first name'].strip()
                obj.last_name = item['last name'].strip()
                
                if str(item['industry'].strip()).isnumeric()==False:
                    obj.industry = item['industry'].strip()
                else:
                    return jsonify({"message": "Industry can't be numeric {}".format(item['id'])}), 200
                
                obj.link = item['link'].strip()
                obj.position = item['position'].strip()
                
                if item['validity grade'].strip() == "A" or item['validity grade'].strip() == "B":
                    obj.validity_grade = item['validity grade'].strip()
                else:
                    return jsonify({"message": "Validity Grade must be A or B {}".format(item['id'])}), 200
                
                if "unblasted" in item:
                    if item['unblasted'].strip() == "false":
                        obj.unblasted = False
                    else:
                        obj.unblasted = True

                if "sent" in item:
                    if item['sent'].strip() == "false":
                        obj.sent = False
                    else:
                        obj.sent = True
                    
                if "delivered" in item:
                    if item['delivered'].strip() == "false":
                        obj.delivered = False
                    else:
                        obj.delivered = True

                if "soft bounces" in item:
                    if item['soft bounces'].strip() == "false":
                        obj.soft_bounces = False
                    else:
                        obj.soft_bounces = True

                if "hard bounces" in item:
                    if item['hard bounces'].strip() == "false":
                        obj.hard_bounces = False
                    else:
                        obj.hard_bounces = True

                if "opened" in item:
                    if item['opened'].strip() == "false":
                        obj.opened = False
                    else:
                        obj.opened = True

                if "unsubscribed" in item:
                    if item['unsubscribed'].strip() == "false":
                        obj.unsubscribed = False
                    else:
                        obj.unsubscribed = True

                db.session.add(obj)
        
        db.session.commit()
    else:
        return jsonify({"message": "No data"}), 200


    return jsonify({"message": "Updated"}), 200

@section_2.route('/2a/search_results', methods=['POST'], defaults={"page": 1})
@section_2.route('/2a/search_results/<int:page>', methods=['POST'])
def search_results_2a(page):
    data = request.get_json()

    per_page = int(data['per_page'])
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
    print(blast_start)

    if data['unblasted']=='1':
        query = query.filter(Scrap.unblasted==True)
    else:
        query = query.filter(Scrap.unblasted==False)
        query = query.filter(and_(Scrap.blast_date>blast_start, Scrap.blast_date<blast_end))

    if "sent" in data:
        if data['sent']=='1':
            query = query.filter(Scrap.sent==True)
        else:
            query = query.filter(Scrap.sent==False)

    if "delivered" in data:
        if data['delivered']=='1':
            query = query.filter(Scrap.delivered==True)
        else:
            query = query.filter(Scrap.delivered==False)

    if "soft_bounces" in data:
        if data['soft_bounces']=='1':
            query = query.filter(Scrap.soft_bounces==True)
        else:
            query = query.filter(Scrap.soft_bounces==False)

    if "hard_bounces" in data:
        if data['hard_bounces']=='1':
            query = query.filter(Scrap.hard_bounces==True)
        else:
            query = query.filter(Scrap.hard_bounces==False)

    if "opened" in data:
        if data['opened']=='1':
            query = query.filter(Scrap.opened==True)
        else:
            query = query.filter(Scrap.opened==False)

    if "unsubscribed" in data:
        if data['unsubscribed']=='1':
            query = query.filter(Scrap.unsubscribed==True)
        else:
            query = query.filter(Scrap.unsubscribed==False)


    upload_start = dateutil.parser.parse(data['upload_daterange'].split("-")[0].strip()).date()
    upload_end = dateutil.parser.parse(data['upload_daterange'].split("-")[1].strip()).date()
    # print(blast_end, blast_start)
    # query = query.filter(and_(Scrap.blast_date>blast_start, Scrap.blast_date<blast_end))
    query = query.filter(and_(Scrap.upload_date>upload_start, Scrap.upload_date<upload_end))
    query = query.filter(and_(Scrap.percentage>=data['p_start'], Scrap.percentage<=data['p_end']))
    
    results = []
    query = query.order_by(asc(Scrap.email))
    query = query.paginate(page,per_page,error_out=False)
    total_page = query.pages
    total_results = query.total
    print(total_page, total_results)
    # print(query.has_next , query.has_prev)

    for item in query.items:
        tmp = object_as_dict(item)
        if tmp['blast_date'] is not None:
            tmp['blast_date'] = str(tmp['blast_date'].strftime('%d-%m-%Y'))
        else:
            tmp['blast_date'] = ""
        
        tmp['upload_date'] = str(tmp['upload_date'].strftime('%d-%m-%Y'))
        results.append(tmp.copy())
    return jsonify({
        "data": results,
        "total_page": total_page,
        "current_page": page,
        "total_results": total_results,
        "has_next": query.has_next,
        "has_prev": query.has_prev
    }), 200

@section_2.route('/2a/get_filters', methods=['GET'])
def get_filters_2a():
    country = list(countries.keys())
    validity_grade = [ item.validity_grade for item in db.session.query(Scrap.validity_grade).distinct() ]
    return jsonify(
                    {
                        "country": country,
                        "validity_grade": validity_grade
                    } ), 200

@section_2.route('/2a/upload', methods=['POST'])
def upload_2a():
    data = request.get_json()

    if data:
        job = current_app.worker_q.enqueue('app.tasks.section_2a_upload', data, job_timeout='20m', failure_ttl=1000)

        return jsonify({ 
                        "task": 1,
                        "job_id": job.id
                        }), 200
    else:
        return jsonify({ 
                    "task": 0
                    }), 200

@section_2.route('/2b/upload', methods=['POST'])
def upload_2b():
    data = request.get_json()
    if data:
        job = current_app.worker_q.enqueue('app.tasks.section_2b_upload', data[0], job_timeout='20m', failure_ttl=1000)
        
        return jsonify({ 
                        "task": 1,
                        "job_id": job.id
                        }), 200
    else:
        return jsonify({ 
                    "task": 0
                    }), 200
