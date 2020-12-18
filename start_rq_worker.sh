#!/bin/bash
echo Opening rw workers...
cd /root/Database_app
export DATABASE_URL="postgresql://admin:zxcASD123@localhost:5432/data_pro"
export SECRET_KEY="132sdaADS1@$%xczmghk"
export FLASK_CONFIG="production"
__conda_setup="$('/root/anaconda3/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/root/anaconda3/etc/profile.d/conda.sh" ]; then
        . "/root/anaconda3/etc/profile.d/conda.sh"
    else
        export PATH="/root/anaconda3/bin:$PATH"
    fi
fi
unset __conda_setup

conda activate database
rq worker