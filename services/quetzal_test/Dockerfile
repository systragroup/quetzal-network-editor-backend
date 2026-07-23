# libexpat.so.1 is needed but not present in lambda striped image.
FROM amazonlinux:2 AS build
# copy libexpat.so.1 in lambda runtime image
FROM python:3.12 AS runtime
COPY --from=build /usr/lib64/libexpat.so.1 /lib64/

# docker env variable inject in build
ARG QUETZAL_MODEL_NAME
ENV QUETZAL_MODEL_NAME=$QUETZAL_MODEL_NAME
ARG IMAGE_TAG
ENV IMAGE_TAG=$IMAGE_TAG
# Install dependancies and add them to paths
COPY ./${QUETZAL_MODEL_NAME}/requirements.txt .
RUN pip install -r requirements.txt 
# need to force-reinstall nbconvert. as its not working anymore if not...
RUN pip install --no-cache-dir --force-reinstall nbconvert


# Copy src code
COPY ./quetzal-network-editor-backend/docker/main_ecs.py .
COPY ./${QUETZAL_MODEL_NAME} .

# Entrypoint
CMD ["python", "main_ecs.py"]