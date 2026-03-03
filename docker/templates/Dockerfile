# docker build need to be run from folder containing model and quetzal library
FROM public.ecr.aws/lambda/python:3.12

ARG QUETZAL_MODEL_NAME='./'
ENV QUETZAL_MODEL_NAME=$QUETZAL_MODEL_NAME

# libexpat.so.1 is needed but not present in lambda layer anymore
RUN dnf install -y expat && dnf clean all

# Install dependancies and add them to paths
COPY ./${QUETZAL_MODEL_NAME}/requirements.txt .
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
# need to force-reinstall nbconvert. as its not working anymore if not...
RUN pip install --no-cache-dir --force-reinstall nbconvert
ENV PATH="${PATH}:${LAMBDA_TASK_ROOT}/bin"
ENV PYTHONPATH="${PYTHONPATH}:${LAMBDA_TASK_ROOT}"

# Copy src code
COPY ./quetzal ${LAMBDA_TASK_ROOT}/quetzal
COPY ./quetzal-network-editor-backend/docker/main.py ${LAMBDA_TASK_ROOT}
COPY ./${QUETZAL_MODEL_NAME} ${LAMBDA_TASK_ROOT}

# Entrypoint
CMD ["main.handler"]