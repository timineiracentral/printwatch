FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    cups \
    cups-client \
    cups-filters \
    gettext-base \
    hp-ppd \
    printer-driver-splix \
    openprinting-ppds \
    printer-driver-cups-pdf \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY cupsd.conf.template cups-files.conf /etc/cups/
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 631

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
