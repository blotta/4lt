#!/usr/bin/env python3

import subprocess as sp
import shlex
import os
import sys
import logging
from urllib import request
import json

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')


def install_package(name):
    sp.call('apt update'.split())
    base_cmd = 'apt install'
    cmd = base_cmd + ' ' + str(name) + ' ' + '-y'
    logging.info("Instalando {}".format(name))
    if sp.check_call(cmd.split()) != 0:
        logging.error("Instalação do pacote {} falhou".format(name))
        sys.exit(2)

def proxy_pass_nginx_config(fqdn, port):
    """Gera configuração de proxy de um domínio de entrada para uma porta no localhost"""
    cfg = "\nserver {\n" + \
    "\tlisten 80;\n" + \
    "\tserver_name {};\n".format(fqdn) + \
    "\tlocation / {\n" + \
    "\t\tproxy_pass http://localhost:{};\n".format(port) + \
    "\t}\n" + \
    "}\n"
    return cfg

def install_docker():
    if sp.call("which docker", shell=True, stdout=sp.DEVNULL) == 0:
        logging.info("Docker já está instalado")
        return

    url = 'https://get.docker.com'
    filepath = "get-docker.sh"
    request.urlretrieve(url, filename=filepath)
    if sp.check_call('sh {}'.format(filepath).split()) != 0:
        logging.error("Instalação do Docker falhou")
        sys.exit(2)

def get_container_info(cont):
    out = sp.check_output('docker inspect {}'.format(cont), shell=True).decode('utf-8')
    return json.loads(out)[0]

def get_container_host_port(cont):
    c = get_container_info(cont)
    return c["NetworkSettings"]["Ports"]["80/tcp"][0]["HostPort"]

def build_image(img_name):
    # # Criar diretorio para o Dockerfile
    builddir = "/tmp/{}".format(img_name)
    try:
        os.makedirs(builddir)
    except FileExistsError:
        pass
    os.chdir(builddir)

    # Criar Dockerfile e seu conteudo
    dockerfilepath = os.path.join(builddir, "Dockerfile")
    with open(dockerfilepath, 'w+') as dockerfile_fd:
        dockerfile_fd.write(DOCKERFILE)

    # Criar start.sh e seu conteudo
    startsh_path = os.path.join(builddir, "start.sh")
    with open(startsh_path, 'w+') as startfile_fd:
        startfile_fd.write(STARTSH)

    # Executar docker build
    sp.call('docker build -t {} .'.format(img_name).split())

def run_instance(cont, img, args=None):
    if sp.call("docker inspect {}".format(cont), shell=True, stdout=sp.DEVNULL, stderr=sp.DEVNULL) == 0:
        logging.info("Container {} já está criado")
        return

    if args != None:
        args_str = ' '.join(args)
    sp.check_call('docker run --name {} -d -p 80 {} {}'.format(cont, img, args_str), shell=True)


# Instalar pacotes
pkgs = ['nginx']

DOCKERFILE = """
FROM debian

RUN apt update -y && apt install apache2 lynx -y

COPY start.sh /start.sh
RUN chmod +x /start.sh

ENTRYPOINT ["/start.sh"]

#CMD ["generico"]

EXPOSE 80
"""

STARTSH = """#!/bin/bash

echo "${1:-$(hostname)}" > /var/www/html/index.html

exec apache2ctl -DFOREGROUND
"""

IMAGE_NAME = '4l-test'
CONTAINER_NAMES = ['app1', 'app2', 'app3']
DOMAIN = 'dexter.com.br'

if __name__ == "__main__":
    # Confirmar root
    if os.geteuid() != 0:
        logging.error("Usuário precisa ser root")
        sys.exit(1)

    #Instalar servicos
    logging.info("Instalando Docker")
    install_docker()
    for p in pkgs:
        logging.info("Instalando {}".format(p))
        install_package(p)

    # Criar imagem
    logging.info("Criando imagem Docker")
    build_image(IMAGE_NAME)

    nginx_cfg = ''

    # Instanciar containers (app1-3)
    for cont in CONTAINER_NAMES:
        logging.info("Criando container {}".format(cont))
        run_instance(cont, IMAGE_NAME, args=[cont])

        fqdn = '{}.{}'.format(cont, DOMAIN)

        # Descobrir portas de acesso aos containers
        port = get_container_host_port(cont)

        # Gerar configuracao nginx com base nas portas dos containers
        nginx_cfg = nginx_cfg + proxy_pass_nginx_config(fqdn, port)

    # Gerar configuracao nginx com base nas portas dos containers
    logging.info("Gerando configuração para o Nginx")
    with open('/etc/nginx/sites-available/4l-docker', 'w+') as f:
        f.write(nginx_cfg)

    # symlink
    logging.info("Criando symlink da configuração do Nginx")
    try:
        os.symlink('/etc/nginx/sites-available/4l-docker', '/etc/nginx/sites-enabled/4l-docker')
    except FileExistsError:
        pass

    # restart service
    logging.info("Reiniciando Nginx")
    sp.call('systemctl restart nginx'.split())
