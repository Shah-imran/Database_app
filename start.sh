#!/bin/bash
echo Starting Flask app.
cd /Database_app
conda activate database
gunicorn -w 9 -b 127.0.0.1:8080 wsgi:app