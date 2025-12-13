# E2SIM Connection Guide - Near-RT-RIC

**Purpose:** Configure and connect E2SIM (E2 Simulator) to Near-RT-RIC  
**Date:** December 13, 2025

---

## Prerequisites

- Near-RT-RIC deployed and running
- Docker installed
- Access to Near-RT-RIC Kubernetes cluster
- `kubectl` configured with access to the cluster

---

## Step 1: Find E2Term Connection Details

**You need to discover these values for your environment:**

### Find E2Term Service and NodePort
```bash
export KUBECONFIG=<your-kubeconfig-path>
kubectl get svc -n ricplt | grep e2term
```

**Look for the NodePort value** (e.g., `32222/TCP` in the output)

### Find Node IP Address
```bash
kubectl get nodes -o wide
```

**Find the INTERNAL-IP** of the node where Near-RT-RIC is running

### Get NodePort Programmatically
```bash
E2TERM_NODEPORT=$(kubectl get svc -n ricplt -l app=ricplt-e2term -o jsonpath='{.items[0].spec.ports[?(@.name=="sctp")].nodePort}')
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
echo "E2Term NodePort: $E2TERM_NODEPORT"
echo "Node IP: $NODE_IP"
```

**Configuration Values You Need:**
- **E2Term NodePort:** Port exposed on the node (e.g., `32222`)
- **Node IP:** IP address of the Kubernetes node running Near-RT-RIC (e.g., `10.200.105.57`)
- **RAN Function ID:** `2` for KPM (this is standard)

---

## Step 2: Clone and Build E2SIM

```bash
# Clone the correct repository (m-release)
git clone https://github.com/o-ran-sc/sim-e2-interface.git
cd sim-e2-interface
git checkout m-release

# Build Docker image
cd e2sim
docker build -t e2-simulator:latest -f Dockerfile_kpm .
```

---

## Step 3: Start E2SIM Container

**Replace `<NODE_IP>` and `<NODEPORT>` with values from Step 1:**

```bash
docker run -d \
  --name e2sim \
  --hostname e2sim \
  --network host \
  --cap-add=NET_RAW \
  --cap-add=NET_ADMIN \
  --restart=unless-stopped \
  -e RAN_FUNC_ID=2 \
  e2-simulator:latest \
  kpm_sim <NODE_IP> <NODEPORT>
```

**Example (with actual values):**
```bash
docker run -d \
  --name e2sim \
  --hostname e2sim \
  --network host \
  --cap-add=NET_RAW \
  --cap-add=NET_ADMIN \
  --restart=unless-stopped \
  -e RAN_FUNC_ID=2 \
  e2-simulator:latest \
  kpm_sim 10.200.105.57 32222
```

**Parameters Explained:**
- `--network host`: Required for SCTP communication (uses host network stack)
- `--cap-add=NET_RAW --cap-add=NET_ADMIN`: Required for SCTP socket binding
- `--restart=unless-stopped`: Auto-restart container if it crashes
- `RAN_FUNC_ID=2`: KPM (Key Performance Measurement) RAN Function (standard value)
- `kpm_sim <NODE_IP> <NODEPORT>`: Entrypoint command
  - `<NODE_IP>`: IP address of Kubernetes node (from Step 1)
  - `<NODEPORT>`: E2Term NodePort (from Step 1)

---

## Step 4: Verify Connection

### Check E2SIM Container
```bash
docker ps | grep e2sim
docker logs e2sim --tail=20
```

**Expected Logs:**
```
[SCTP] Binding client socket to source port 36422
[SCTP] Connecting to server at <NODE_IP>:<NODEPORT> ...
[SCTP] Connection established
Sent E2-SETUP-REQUEST as E2AP message
```

**Note:** The IP and port in logs will match your configured values.

### Check Connection Status via E2 Manager API
```bash
export KUBECONFIG=<your-kubeconfig-path>
E2MGR_POD=$(kubectl get pods -n ricplt -l app=ricplt-e2mgr -o jsonpath="{.items[0].metadata.name}")
kubectl exec -n ricplt $E2MGR_POD -- curl -s http://localhost:3800/v1/nodeb/states | grep -o '"connectionStatus":"[^"]*"'
```

**Expected Output:**
```
"connectionStatus":"CONNECTED"
```

### Check Full Node Details
```bash
kubectl exec -n ricplt $E2MGR_POD -- curl -s http://localhost:3800/v1/nodeb/states
```

**Expected Response:**
```json
[
  {
    "inventoryName": "gnb_734_373_16b8cef1",
    "globalNbId": {
      "plmnId": "373437",
      "nbId": "10110101110001100111011110001"
    },
    "connectionStatus": "CONNECTED"
  }
]
```

---

## Troubleshooting

### Connection Status Shows DISCONNECTED

1. **Check E2SIM container is running:**
   ```bash
   docker ps | grep e2sim
   ```

2. **Check E2SIM logs for errors:**
   ```bash
   docker logs e2sim --tail=50
   ```

3. **Restart E2SIM:**
   ```bash
   docker restart e2sim
   ```

4. **Check E2 Term pod:**
   ```bash
   kubectl get pods -n ricplt | grep e2term
   kubectl logs -n ricplt <e2term-pod-name> --tail=50
   ```

### E2SIM Container Keeps Restarting

- Verify E2Term NodePort is correct (check with `kubectl get svc -n ricplt | grep e2term`)
- Check network connectivity: `ping <NODE_IP>` (replace with your node IP)
- Ensure `--network host` is used
- Verify capabilities: `--cap-add=NET_RAW --cap-add=NET_ADMIN`
- Check E2SIM logs: `docker logs e2sim --tail=50`

---
