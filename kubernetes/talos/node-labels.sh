kubectl label nodes worker01 topology.kubernetes.io/region=TamLand
kubectl label nodes worker01 topology.kubernetes.io/zone=hype01
kubectl label nodes worker02 topology.kubernetes.io/region=TamLand
kubectl label nodes worker02 topology.kubernetes.io/zone=hype01
kubectl label nodes worker03 topology.kubernetes.io/region=TamLand
kubectl label nodes worker03 topology.kubernetes.io/zone=hype01
kubectl label nodes worker04 topology.kubernetes.io/region=TamLand
kubectl label nodes worker04 topology.kubernetes.io/zone=hype01
kubectl label nodes worker05 topology.kubernetes.io/region=TamLand
kubectl label nodes worker05 topology.kubernetes.io/zone=hype01
kubectl label nodes controlplane03 topology.kubernetes.io/region=TamLand
kubectl label nodes controlplane03 topology.kubernetes.io/zone=hype01

kubectl label nodes worker01 egress-gw-vpn=true
kubectl label nodes worker02 egress-gw-vpn=true
kubectl label nodes worker03 egress-gw-vpn=true
kubectl label nodes worker04 egress-gw-vpn=true
kubectl label nodes worker05 egress-gw-vpn=true
