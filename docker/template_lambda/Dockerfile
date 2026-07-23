# libexpat.so.1 is needed but not present in lambda striped image.
FROM amazonlinux:2 AS build
# copy libexpat.so.1 in lambda runtime image
FROM public.ecr.aws/lambda/python:3.12 AS runtime
COPY --from=build /usr/lib64/libexpat.so.1 /lib64/

# docker env variable inject in build
ARG QUETZAL_MODEL_NAME
ENV QUETZAL_MODEL_NAME=$QUETZAL_MODEL_NAME
ARG IMAGE_TAG
ENV IMAGE_TAG=$IMAGE_TAG

# Install dependancies and add them to paths
COPY ./${QUETZAL_MODEL_NAME}/requirements.txt .
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
# need to force-reinstall nbconvert. as its not working anymore if not...
RUN pip install --no-cache-dir --force-reinstall nbconvert

ENV PATH="${PATH}:${LAMBDA_TASK_ROOT}/bin"
ENV PYTHONPATH="${PYTHONPATH}:${LAMBDA_TASK_ROOT}"

# Copy src code if quetzal-transport is not in requirements.txt. need to copy local quetzal in docker
#COPY ./quetzal ${LAMBDA_TASK_ROOT}/quetzal
COPY ./quetzal-network-editor-backend/docker/main.py ${LAMBDA_TASK_ROOT}
COPY ./${QUETZAL_MODEL_NAME} ${LAMBDA_TASK_ROOT}

# Entrypoint
CMD ["main.handler"]