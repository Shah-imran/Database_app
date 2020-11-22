from flask import render_template, redirect, request, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from . import section_3
from ..models import User, Research, ScrapDate, Scrap
from rq.registry import StartedJobRegistry, FinishedJobRegistry, FailedJobRegistry
from ..utils import countries
from flask import render_template, redirect, request, url_for, flash, current_app, jsonify
from datetime import datetime
from .. import config, db
from sqlalchemy import and_, or_, inspect, func, case
from sqlalchemy.sql import label
from sqlalchemy.orm import load_only
import json
import pandas as pd
import dateutil.parser
import math
import time


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


@section_3.route('/index', methods=['GET'])
@login_required
def index():
    return render_template('section_3/index.html')

@section_3.route('/search_results', methods=['POST'], defaults={"page": 1})
@section_3.route('/search_results/<int:page>', methods=['POST'])
@login_required
def search_results(page):
    data = request.get_json()
    if data:
        data['page'] = page
        job = current_app.worker_q.enqueue('app.tasks.section_3_search_results', data, job_timeout='20m', failure_ttl=1000)
        return jsonify({ 
                    "task": 1,
                    "job_id": job.id
                    }), 200
    else:
        return jsonify({ 
                    "task": 0
                    }), 200

@section_3.route('/task_check', methods=['POST'])
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
    

def find(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return -1