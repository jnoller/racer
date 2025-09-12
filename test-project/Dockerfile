FROM continuumio/miniconda3 as miniconda
### Install and configure miniconda
RUN conda install conda-forge::conda-project --yes && conda clean --all --yes

FROM miniconda as conda-project

COPY --from=miniconda /opt/conda /opt/conda

### Set timezone
ENV TZ=US/Central
RUN cp /usr/share/zoneinfo/${TZ} /etc/localtime \
    && echo ${TZ} > /etc/timezone

ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

ENV PATH=/opt/conda/bin:$PATH
ENV HOME=/project

COPY . /project
RUN chown -R 1001:1001 /project

USER 1001
WORKDIR /project
RUN ["conda", "project", "prepare", "--force"]

ENTRYPOINT ["conda", "project", "run"]
CMD []
