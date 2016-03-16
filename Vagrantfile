$script = <<SCRIPT
  echo 'deb http://ubuntu.zerogw.com vagga-testing main' | sudo tee /etc/apt/sources.list.d/vagga.list
  sudo apt-get update
  sudo apt-get -y -f --allow-unauthenticated install vagga
  mkdir -p /var/vagga
  mkdir -p /parent/.vagga
  chown -R vagrant:vagrant /var/vagga
  mount --bind /var/vagga /parent/.vagga
  echo "127.0.0.1 vagrant-ubuntu-vivid-64" >> /etc/hosts
  mkdir /home/vagrant/.cache/vagga
  mkdir /home/vagrant/.cache/vagga/cache
  echo "cache-dir: /home/vagrant/.cache/vagga/cache" > /home/vagrant/.config/vagga/settings.yaml
SCRIPT

Vagrant.configure(2) do |config|
  config.vm.provider "virtualbox" do |vb|
    vb.gui = false
    vb.name = "logstash-kafka-avro"
    vb.memory = "4096"
    vb.cpus = 1
  end
  
  config.vm.box = "ubuntu/vivid64"
  config.vm.box_check_update = false

  config.vm.network "private_network", type: "dhcp"

  config.ssh.forward_agent = true

  config.vm.synced_folder ".", "/parent", type: "nfs", :linux__nfs_options => ['rw', 'no_root_squash']
  config.bindfs.bind_folder "/parent", "/parent"

  config.vm.provision "shell", inline: $script
end