FROM dockerfile/python

MAINTAINER keyz182@gmail.com

# Add the PostgreSQL PGP key to verify their Debian packages.
# It should be the same key as https://www.postgresql.org/media/keys/ACCC4CF8.asc
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8

# Add PostgreSQL's repository. It contains the most recent stable release
#     of PostgreSQL, ``9.3``.
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ precise-pgdg main" > /etc/apt/sources.list.d/pgdg.list

# Update the Ubuntu and PostgreSQL repository indexes
RUN apt-get update

# Install postgres libs for psycopg2
RUN apt-get install -y libpq-dev

RUN pip install psycopg2
RUN pip install ppygis
RUN pip install simplejson
RUN pip install twython

RUN apt-get install -y supervisor
RUN mkdir -p /var/run/postwycker

ADD supervisord.conf /etc/supervisor/conf.d/supervisord.conf

ADD src/ /opt/postwycker

CMD ["/usr/bin/supervisord"]

