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

def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


@section_2.route('/2a', methods=['GET'])
def _2a():
    return render_template('section_2/2a.html')

@section_2.route('/2b', methods=['GET'])
def _2b():
    return render_template('section_2/2b.html')

@section_2.route('/2a/upload', methods=['POST'])
def upload_2a():
    data = request.get_json()

    fields = ['Country', 'Email', 'First Name', 'Last Name', 'Company',
                     'Industry', 'Link', 'Position', 'Validity Grade']
    resutls = ""
    for item in data:
        if item['meta']['fields'] == fields:
            print("got it")
            for index, row in enumerate(item['data']):
                try:
                    company = Research.query.filter_by(company_name=row['Company'].strip()).first()
                    if company:
                        scrap = Scrap(
                        country = row['Country'].strip(),
                        email = row['Email'].strip(),
                        first_name = row['First Name'].strip(),
                        last_name = row['Last Name'].strip(),
                        industry = row['Industry'].strip(),
                        link = row['Link'].strip(),
                        position = row['Position'].strip(),
                        validity_grade = row['Validity Grade'].strip(),
                        research_id = company.id)
                        db.session.add(scrap)
                    else:
                        print('not found')
                except Exception as e:
                    print("Error at upload_2a: {} {}".format(index, e))
            resutls += "{}: File uploaded\n".format(item['filename'])
        else:
            resutls += "{}: File not uploaded\n".format(item['filename'])
    print(db.session)
    db.session.commit()
    return jsonify(resutls), 200