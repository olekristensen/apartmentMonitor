
FROM python:2

COPY server/ /src/server/
COPY get_data/ /src/get_data/

RUN pip install flask requests

CMD cd /src/get_data && \
    (python -d hue_polling_to_db.py > ../log.txt &) &&\
    cd ../server &&\
    python api.py
