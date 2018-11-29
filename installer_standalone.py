#!/usr/bin/env python3

import subprocess as sp
import shlex
import os
import sys
import logging
from urllib import request
import json

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')


def execute_command(cmd):
    if type(cmd) == type([]):
        cmd = ' '.join(cmd)

    if type(cmd) != type(''):
        raise TypeError

    split_cmd = shlex.split(cmd)

    print(split_cmd)
    logging.debug("Executando comando '{}'".format(cmd))
    proc = sp.Popen(split_cmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)

    while proc.poll() == None:
        out = proc.stdout.readline().decode('utf-8')
        if out != '':
            logging.info(out.rstrip("\n\r"))
            sys.stdout.flush()
        err = proc.stderr.readline().decode('utf-8')
        if err != '':
            logging.info(err.rstrip("\n\r"))
            sys.stderr.flush()

    stdout, stderr = proc.communicate()
    stdout = stdout.decode('utf-8').rstrip("\n\r")
    stderr = stderr.decode('utf-8').rstrip("\n\r")

    if proc.returncode != 0:
        logging.error("Comando '{}' retornou erro: '{}'".format(cmd, stderr))
        return False
    else:
        logging.debug("Comando '{}' executado com sucesso".format(cmd))
        return True


def install_package(name):
    sp.call('apt update'.split())
    base_cmd = 'apt install'
    cmd = base_cmd + ' ' + str(name) + ' ' + '-y'
    logging.info("Instalando {}".format(name))
    # execute_command(cmd)
    if sp.check_call(cmd.split()) != 0:
        logging.error("Instalação do Nginx falhou")
        sys.exit(2)

def proxy_pass_nginx_config(fqdn, port):
    """Gera configuração de proxy de um domínio de entrada para uma porta no localhost"""
    cfg = "server {\n" + \
    "\tlisten 80;\n" + \
    "\tserver_name {};\n".format(fqdn) + \
    "\tlocation / {\n" + \
    "\t\tproxy_pass http://localhost:{};\n".format(port) + \
    "\t}\n" + \
    "}\n"
    return cfg

def install_docker():
    url = 'https://get.docker.com'
    filepath = "get-docker.sh"
    request.urlretrieve(url, filename=filepath)
    # execute_command('/bin/sh {}'.format(filepath))
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
    # execute_command('docker build -t {} .'.format(img_name))
    sp.call('docker build -t {} .'.format(img_name).split())

def run_instance(cont, img, args=None):
    if args != None:
        args_str = ' '.join(args)
    # execute_command('docker run -d --name {} -p 80 {} {}'.format(cont, img, args_str))
    sp.call('docker run --name {} -d -p 80 {} {}'.format(cont, img, args_str), shell=True)


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
    # execute_command('./wait.sh')
    # execute_command('./reterr.sh')
    # Confirmar root
    if os.geteuid() != 0:
        logging.error("Usuário precisa ser root")
        sys.exit(1)

    #Instalar Docker
    install_docker()

    # Instalar Nginx
    install_package('nginx')

    # # Criar imagem
    build_image(IMAGE_NAME)

    ports = {}
    nginx_cfg = ''

    # # Instanciar 3 containers diferentes (app1-3)
    for cont in CONTAINER_NAMES:
        run_instance(cont, IMAGE_NAME, args=[cont])

        # Descobrir portas de acesso aos containers
        ports[cont] = get_container_host_port(cont)
        logging.info("Container {} tem porta {} no host".format(cont, ports[cont]))

        # Gerar configuracao nginx com base nas portas dos containers
        nginx_cfg = nginx_cfg + "\n" + proxy_pass_nginx_config('{}.{}'.format(cont, DOMAIN), ports[cont])

    # Gerar configuracao nginx com base nas portas dos containers
    with open('/etc/nginx/sites-available/4l-docker', 'w+') as f:
        f.write(nginx_cfg)

    # symlink
    os.symlink('/etc/nginx/sites-available/4l-docker', '/etc/nginx/sites-enabled/4l-docker')

    # restart service
    sp.call('systemctl restart nginx'.split())


