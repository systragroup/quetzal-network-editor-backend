# docker build need to be run from folder containing model and quetzal library
FROM public.ecr.aws/lambda/python:3.12

ARG QUETZAL_MODEL_NAME='./'
ENV QUETZAL_MODEL_NAME=$QUETZAL_MODEL_NAME

# Install dependancies and add them to paths
COPY ./${QUETZAL_MODEL_NAME}/requirements.txt .
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
ENV PATH="${PATH}:${LAMBDA_TASK_ROOT}/bin"
ENV PYTHONPATH="${PYTHONPATH}:${LAMBDA_TASK_ROOT}"

# Copy src code
COPY ./quetzal ${LAMBDA_TASK_ROOT}/quetzal
COPY ./quetzal-network-editor-backend/docker/main.py ${LAMBDA_TASK_ROOT}
COPY ./${QUETZAL_MODEL_NAME} ${LAMBDA_TASK_ROOT}

# there is no .git as we are in a subfolder:
# so copy yhe one in quetzal. (therre is dockerignore that delete large file too.)
# the ipynb to py conversion doesnt work if there is no .git.
COPY ./quetzal/.git ${LAMBDA_TASK_ROOT}/.git

# Entrypoint
CMD ["main.handler"]