
FROM python:2

COPY . /src/

RUN pip install flask

CMD cd /src/get_data && \
    (python -d hue_polling_to_db.py > ../log.txt &) &&\
    cd ../server &&\
    python api.py
