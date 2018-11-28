# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure("2") do |config|

    config.vm.define "4l-test" do |manager|
        manager.vm.box = "ubuntu/xenial64"
        manager.vm.network "private_network", ip: "192.168.33.160"
        manager.vm.hostname = "4l-test.dexter.com.br"

        config.vm.provider "virtualbox" do |vb|
            vb.memory = "2048"
        end

        manager.vm.provision "shell", inline: <<-SHELL
            echo "192.168.33.160 app1.dexter.com.br app2.dexter.com.br app3.dexter.com.br" >> /etc/hosts
        SHELL
    end
end
