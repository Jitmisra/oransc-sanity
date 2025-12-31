# SMO Deployment Guide
## O-RAN SC `it-dep/smo-install` (M-release)

**Purpose**: Step-by-step deployment guide for SMO installation on a single-node Kubernetes cluster.

---

## Prerequisites

### System Requirements
- **OS**: Ubuntu 22.04 or 24.04
- **Network**: Internet connectivity required
- **Access**: `sudo` privileges
- **Resources**: Minimum 8GB RAM, 4 CPU cores, 50GB disk space

### Pre-Deployment Checklist
- [ ] Ubuntu version verified (22.04 or 24.04)
- [ ] Internet connectivity confirmed
- [ ] `sudo` access available
- [ ] No existing Kubernetes cluster (or willing to remove it)

---

## Deployment Steps

### Step 1: Clone Repository and Switch to M-release Branch

```bash
cd ~
rm -rf it-dep
git clone https://github.com/o-ran-sc/it-dep.git
cd it-dep
git checkout m-release
```

**What this does**:
- Removes any existing `it-dep` directory
- Clones the O-RAN SC `it-dep` repository
- Switches to the `m-release` branch (stable release)

**Verification**:
```bash
cd ~/it-dep
git branch
# Expected output: * m-release
```

---

### Step 2: Initialize Git Submodules

**⚠️ CRITICAL**: This step is required for Helm plugins to install correctly.

```bash
git submodule update --init --recursive
```

**What this does**:
- Initializes all Git submodules
- Downloads `onap_oom` submodule (contains Helm `deploy` and `undeploy` plugins)
- Downloads other required submodules

**Why it's critical**:
- The `deploy` and `undeploy` Helm plugins come from `onap_oom/kubernetes/helm/plugins/`
- Without submodules, these plugins cannot be installed
- Step 4 will fail if submodules are not initialized

**Verification**:
```bash
ls -d ~/it-dep/smo-install/onap_oom
# Expected: Directory exists
```

---

### Step 3: Install Kubernetes

```bash
chmod +x tools/setup_k8s/scripts/setup_k8s.sh
SERVER_IP=$(hostname -I | awk '{print $1}')
echo "Server IP: $SERVER_IP"
sudo bash tools/setup_k8s/scripts/setup_k8s.sh --ip-address $SERVER_IP
```

**What this does**:
- Makes the setup script executable
- Detects the server's IP address automatically
- Installs Kubernetes cluster using `kubeadm`
- Installs Containerd container runtime
- Installs Helm (v3.18.6)
- Installs Calico CNI
- Configures kubectl for the current user

**Expected output**:
- Kubernetes cluster initialized
- 7 pods running in `kube-system` namespace
- Node status: `Ready`

**Verification**:
```bash
# Check node status
kubectl get nodes
# Expected: STATUS = Ready

# Check system pods
kubectl get pods -n kube-system
# Expected: 7 pods Running (etcd, kube-apiserver, kube-controller-manager, kube-scheduler, coredns x2, calico-kube-controllers, calico-node)
```

**Note**: The script will prompt to remove existing cluster if one exists. Answer `y` to proceed.

---

### Step 4: Setup Helm and Install Plugins

```bash
chmod +x smo-install/scripts/layer-0/0-setup-helm3.sh
bash smo-install/scripts/layer-0/0-setup-helm3.sh
```

**What this does**:
- Installs Helm (if not already installed)
- Installs Git (if missing)
- Installs Make (if missing)
- Installs Helm plugins:
  - `cm-push` (v0.10.3) - ChartMuseum push plugin
  - `deploy` - Custom deployment plugin (from `onap_oom`)
  - `undeploy` - Custom undeployment plugin (from `onap_oom`)
- Adds Helm repositories:
  - `oran-snapshot`
  - `oran-release`
  - `strimzi`
  - `openebs`
  - `mariadb-operator`
- Updates Helm repositories

**Expected output**:
- Helm version displayed
- Plugins installed successfully
- Repositories added and updated

**Verification**:
```bash
# Check Helm version
helm version
# Expected: v3.x (not v4)

# Check plugins
helm plugin list
# Expected output:
# NAME      VERSION DESCRIPTION
# cm-push   0.10.3  Push chart package to ChartMuseum
# deploy    ...     ...
# undeploy  ...     ...

# Check repositories
helm repo list
# Expected: 5 repositories listed (oran-snapshot, oran-release, strimzi, openebs, mariadb-operator)
```

---

### Step 5: Verify Helm Plugins and Repositories

```bash
helm plugin list
helm repo list
```

**What this does**:
- Lists all installed Helm plugins
- Lists all configured Helm repositories

**Expected output**:
- 3 plugins: `cm-push`, `deploy`, `undeploy`
- 5 repositories: `oran-snapshot`, `oran-release`, `strimzi`, `openebs`, `mariadb-operator`

**If plugins are missing**:
- Re-run Step 2 (submodule initialization)
- Re-run Step 4

---

### Step 6: Install SMO

```bash
cd smo-install/scripts/layer-2
chmod +x 2-install-oran.sh
bash 2-install-oran.sh default release
```

**What this does**:
- Installs `yq` (YAML processor) if missing
- Pre-configures SMO:
  - Installs OpenEBS (storage)
  - Creates storage class
  - Installs MariaDB operator (if enabled)
- Installs ONAP:
  - Installs Strimzi Kafka operator (if enabled)
  - Deploys ONAP chart using `helm deploy`
- Installs Non-RT-RIC:
  - Deploys Non-RT-RIC chart
  - Copies Kafka secrets from `onap` namespace
  - Waits for Kong deployment
- Installs SMO:
  - Deploys SMO chart
  - Copies Kafka secrets from `onap` namespace
- Post-configures SMO:
  - Preloads Service Manager (if enabled)

**Parameters**:
- `default`: Uses default Helm override configuration
- `release`: Uses release/snapshot Helm repositories (not local/dev)

**Expected duration**: 15-30 minutes (depending on system resources and network speed)

**Expected output**:
- Multiple namespaces created: `openebs`, `mariadb-operator`, `strimzi-system`, `onap`, `nonrtric`, `smo`
- Multiple Helm releases deployed
- Pods starting in each namespace

**Verification** (during installation):
```bash
# Check namespaces
kubectl get namespaces
# Expected: openebs, mariadb-operator, strimzi-system, onap, nonrtric, smo

# Check ONAP pods (takes longest)
kubectl get pods -n onap
# Expected: Many pods, some may be Pending/ContainerCreating initially

# Check Non-RT-RIC pods
kubectl get pods -n nonrtric
# Expected: Kong and other Non-RT-RIC components

# Check SMO pods
kubectl get pods -n smo
# Expected: SMO components
```

---

### Step 7: Final Status Check

```bash
kubectl get namespaces
helm list -A
kubectl get pods -A
```

**What this does**:
- Lists all namespaces (verifies all were created)
- Lists all Helm releases across all namespaces
- Lists all pods across all namespaces (shows deployment status)

**Expected output**:

**Namespaces**:
```
NAME                 STATUS   AGE
default              Active   ...
kube-system          Active   ...
kube-public          Active   ...
kube-node-lease      Active   ...
openebs              Active   ...
mariadb-operator     Active   ...
strimzi-system       Active   ...
onap                 Active   ...
nonrtric             Active   ...
smo                  Active   ...
```

**Helm releases**:
```
NAME                    NAMESPACE           REVISION    STATUS      CHART
openebs                 openebs             1           deployed    openebs-4.3.0
mariadb-operator        mariadb-operator    1           deployed    mariadb-operator-...
strimzi-kafka-operator strimzi-system      1           deployed    strimzi-kafka-operator-0.45.0
onap                    onap                1           deployed    onap-...
oran-nonrtric           nonrtric            1           deployed    nonrtric-...
oran-smo                smo                 1           deployed    smo-...
```

**Pods** (sample):
```
NAMESPACE          NAME                                      READY   STATUS    RESTARTS   AGE
kube-system        calico-kube-controllers-...              1/1     Running   0          ...
kube-system        calico-node-...                           1/1     Running   0          ...
kube-system        coredns-...                               1/1     Running   0          ...
onap               onap-strimzi-entity-operator-...          1/1     Running   0          ...
onap               dmeparticipant-ku-...                     1/1     Running   0          ...
nonrtric           oran-nonrtric-kong-...                     1/1     Running   0          ...
smo                ...                                        1/1     Running   0          ...
```

**Success criteria**:
- All namespaces exist
- All Helm releases show `STATUS = deployed`
- Critical pods show `STATUS = Running`:
  - `onap-strimzi-entity-operator-*` (in `onap` namespace)
  - `dmeparticipant-ku-*` (in `onap` namespace)
  - `oran-nonrtric-kong-*` (in `nonrtric` namespace)

---

## Post-Deployment Verification

### Check Critical Components

```bash
# Check ONAP Entity Operator (critical for Kafka)
kubectl get pods -n onap | grep entity-operator
# Expected: 1/1 Running

# Check DME Participant (required by Non-RT-RIC)
kubectl get pods -n onap | grep dmeparticipant
# Expected: 1/1 Running

# Check Kong (API Gateway)
kubectl get deployment oran-nonrtric-kong -n nonrtric
# Expected: AVAILABLE = 1

# Check SMO pods
kubectl get pods -n smo
# Expected: All pods Running (varies by configuration)
```

### Check Services

```bash
# Check services in each namespace
kubectl get services -n onap
kubectl get services -n nonrtric
kubectl get services -n smo
```

### Check Storage

```bash
# Check storage classes
kubectl get storageclass
# Expected: smo-storage exists

# Check persistent volumes
kubectl get pv

# Check persistent volume claims
kubectl get pvc -A
```

### Check Secrets

```bash
# Check Kafka secrets (critical)
kubectl get secrets -n onap | grep kafka
kubectl get secrets -n nonrtric | grep kafka
kubectl get secrets -n smo | grep kafka
# Expected: Kafka user secrets exist in all three namespaces
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Step 2 - Submodules Not Initialized
**Symptom**: Step 4 fails with "plugin not found" or "directory not found"

**Fix**:
```bash
cd ~/it-dep
git submodule update --init --recursive
# Re-run Step 4
```

#### Issue 2: Step 3 - Kubernetes Installation Fails
**Symptom**: Pods stuck in Pending, node NotReady

**Fix**:
- Check if swap is disabled: `swapon --show` (should be empty)
- Check kernel modules: `lsmod | grep br_netfilter`
- Restart containerd: `sudo systemctl restart containerd`
- Restart kubelet: `sudo systemctl restart kubelet`

#### Issue 3: Step 4 - Helm Plugins Not Installing
**Symptom**: `deploy` or `undeploy` plugin installation fails

**Fix**:
- Verify submodules: `ls -d ~/it-dep/smo-install/onap_oom`
- Re-run Step 2
- Re-run Step 4

#### Issue 4: Step 6 - Installation Hangs
**Symptom**: Script waits indefinitely for resources

**Fix**:
- Check what it's waiting for: `kubectl get pods -A`
- Check logs: `kubectl logs <pod-name> -n <namespace>`
- Check events: `kubectl get events -A --sort-by='.lastTimestamp'`

#### Issue 5: Step 6 - Pods in CrashLoopBackOff
**Symptom**: Pods restarting continuously

**Fix**:
- Check pod logs: `kubectl logs <pod-name> -n <namespace>`
- Check pod events: `kubectl describe pod <pod-name> -n <namespace>`
- Check resource constraints: `kubectl top nodes`

---

## Uninstallation

To completely remove SMO installation:

```bash
cd ~/it-dep/smo-install/scripts
./uninstall-all.sh
```

This will:
- Uninstall all SMO components
- Uninstall Non-RT-RIC
- Uninstall ONAP
- Clean up namespaces and resources

**Note**: This does NOT remove Kubernetes cluster. To remove Kubernetes:

```bash
sudo kubeadm reset -f
sudo rm -rf /etc/kubernetes /var/lib/kubelet /var/lib/etcd
sudo rm -rf ~/.kube
```

---

## Summary

This guide provides a step-by-step process for deploying SMO on a single-node Kubernetes cluster. Follow the steps in order, verify each step before proceeding, and refer to the troubleshooting section if issues arise.

**Key Points**:
1. Always initialize submodules (Step 2) before Helm setup (Step 4)
2. Verify Kubernetes cluster is healthy (Step 3) before SMO installation (Step 6)
3. Allow sufficient time for SMO installation (15-30 minutes)
4. Verify critical pods are Running before considering deployment complete

---

**End of Guide**

