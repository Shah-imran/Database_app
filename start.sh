#!/bin/bash
echo Starting Flask app.
cd /root/Database_app
conda init bash
conda activate database
gunicorn -w 9 -b 127.0.0.1:8080 wsgi:app