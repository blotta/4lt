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

    logging.debug("Executando comando '{}'".format(cmd))
    proc = sp.Popen(split_cmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
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
    base_cmd = 'apt install'
    cmd = base_cmd + ' ' + str(name) + ' ' + '-y'
    logging.info("Instalando {}".format(name))
    execute_command(cmd)

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
    filepath = "/tmp/get-docker.sh"
    request.urlretrieve(url, filename=filepath)
    execute_command(['sh', filepath])

def build_image():
    # # Criar diretorio para o Dockerfile
    builddir = "/tmp/4linuxapp"
    try:
        os.makedirs(builddir)
    except FileExistsError:
        pass
    # os.chdir(builddir)

    # Criar Dockerfile e seu conteudo
    dockerfilepath = os.path.join(builddir, "Dockerfile")
    with open(dockerfilepath, 'w+') as dockerfile_fd:
        dockerfile_fd.write(DOCKERFILE)

    # Criar start.sh e seu conteudo
    startsh_path = os.path.join(builddir, "start.sh")
    with open(dockerfilepath, 'w+') as dockerfile_fd:
        dockerfile_fd.write(DOCKERFILE)

    # Executar docker build

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

STARTSH = """
#!/bin/bash

echo "${1:-$(hostname)}" > /var/www/html/index.html

exec apache2ctl -DFOREGROUND
"""

if __name__ == "__main__":
    # # Confirmar root
    # if os.geteuid() != 0:
    #     logging.error("Usuário precisa ser root")
    #     sys.exit(1)

    # Instalar Docker
    # install_docker()

    # Criar imagem
    build_image()


    # Instanciar 3 containers diferentes (app1-3)

    # Descobrir portas de acesso aos containers

    # Instalar Nginx

    # Gerar configuracao nginx com base nas portas dos containers


