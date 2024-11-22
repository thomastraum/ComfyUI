#!/bin/bash
sudo mkdir -p /mnt/L
sudo mount -t cifs //TRAUM-SERVER/library /mnt/L -o username=ttserv,password='Pa55word!',vers=3.0
python main.py --extra-model-paths-config extra_model_paths-network.yaml
