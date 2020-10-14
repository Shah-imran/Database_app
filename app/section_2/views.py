from flask import render_template, redirect, request, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from . import section_2
from ..models import User, Research, ScrapDate, Scrap

from ..utils import countries
from flask import render_template, redirect, request, url_for, flash, current_app, jsonify
from datetime import datetime
from .. import config, db
from sqlalchemy import and_, or_, inspect
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

@section_2.route('/2a/search_results', methods=['POST'], defaults={"page": 1})
@section_2.route('/2a/search_results/<int:page>', methods=['POST'])
def search_results_2a(page):
    per_page = current_app.config["PER_PAGE_PAGINATION"]
    data = request.get_json()
    print(data)
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

    if data['filename']:
        filter = [ Scrap.filename.ilike("%{}%".format(sq)) for sq in data['filename'] ]
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
    
    if data['unblasted']:
        query = query.filter(Scrap.unblasted==data['unblasted'])

    blast_start = dateutil.parser.parse(data['blast_daterange'].split("-")[0].strip())
    blast_end = dateutil.parser.parse(data['blast_daterange'].split("-")[1].strip())

    upload_start = dateutil.parser.parse(data['upload_daterange'].split("-")[0].strip())
    upload_end = dateutil.parser.parse(data['upload_daterange'].split("-")[1].strip())
    # print(blast_end, blast_start)
    # query = query.filter(and_(Scrap.blast_date>blast_start, Scrap.blast_date<blast_end))
    query = query.filter(and_(Scrap.upload_date>upload_start, Scrap.upload_date<upload_end))
    query = query.filter(and_(Scrap.percentage>=data['p_start'], Scrap.percentage<=data['p_end']))
    total = query.count()
    total_page = math.ceil(total/per_page)
    print(total_page)
    results = []
    
    query = query.paginate(page,per_page,error_out=False)

    for item in query.items:
        results.append(object_as_dict(item).copy())
    return jsonify({
        "data": results,
        "total_page": total_page,
        "current_page": page
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

    fields = ['Country', 'Email', 'First Name', 'Last Name', 'Company',
                     'Industry', 'Link', 'Position', 'Validity Grade']
    results = ""
    for item in data:
        if item['meta']['fields'] == fields:
            job = current_app.worker_q.enqueue('app.tasks.section_2a_upload', item)
            print(job.id)
            print(job.result)
            results += "{}: File added to upload task queue\n".format(item['filename'])
        else:
            results += "{}: File not added to upload task queue\n".format(item['filename'])

    return jsonify(results), 200