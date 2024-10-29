FROM public.ecr.aws/lambda/python:3.12

ENV BACKEND_FOLDER='quetzal-network-editor-backend'
ARG SERVICE_NAME='./'
ENV SERVICE_NAME=$SERVICE_NAME


COPY ${BACKEND_FOLDER}/services/${SERVICE_NAME}/requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt

COPY ./quetzal/quetzal ./quetzal/quetzal
COPY ./quetzal/syspy ./quetzal/syspy

COPY ${BACKEND_FOLDER}/services/${SERVICE_NAME}/ ./



CMD ["main.handler"]

