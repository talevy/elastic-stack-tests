$script = <<SCRIPT
  echo 'deb http://ubuntu.zerogw.com vagga-testing main' | sudo tee /etc/apt/sources.list.d/vagga.list
  sudo apt-get update
  sudo apt-get -y -f --allow-unauthenticated install vagga
  sudo mkdir -p /var/vagga
  mkdir -p /parent/.vagga
  sudo chown -R vagrant:vagrant /var/vagga
  sudo mount --bind /var/vagga /parent/.vagga
  sudo mkdir -p /var/vagga/cache/
  sudo chown -R vagrant:vagrant /var/vagga/cache
  #echo "cache-dir: /parent/vaggacache" > /home/vagrant/.vagga.yaml
  cd /parent
  vagga _create_netns
  sudo iptables "-t" "nat" "-A" "POSTROUTING" "-s" "172.18.255.0/30" "-j" "MASQUERADE"
  cat /parent/hosts > /etc/hosts
SCRIPT

Vagrant.configure(2) do |config|
  config.vm.provider "virtualbox" do |vb|
    vb.gui = false
    vb.name = "logstash-kafka-test"
    vb.memory = "4096"
    vb.cpus = 4
  end
  
  config.vm.box = "ubuntu/vivid64"
  config.vm.box_check_update = false

  config.vm.network "private_network", type: "dhcp"

  config.ssh.forward_agent = true

  config.vm.synced_folder ".", "/parent", type: "nfs", :linux__nfs_options => ['rw', 'no_root_squash']
  config.bindfs.bind_folder "/parent", "/parent"


  config.vm.provision "shell", inline: $script, privileged: false
end
