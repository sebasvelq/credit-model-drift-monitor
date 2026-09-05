FROM public.ecr.aws/lambda/python:3.10

RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY drift_check.py ${LAMBDA_TASK_ROOT}

CMD ["drift_check.handler"]