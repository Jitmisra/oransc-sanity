# Multi-Cluster LCM with O2IMS Support

A Kubernetes-native Multi-Cluster Lifecycle Management (LCM) system with O-RAN O2 IMS support for provisioning bare-metal Kubernetes clusters.

## 📋 Project Overview

This project implements automated provisioning of Kubernetes clusters on Linux servers using:

- **CAPI BYOH** (Cluster API - Bring Your Own Host) for bare-metal cluster provisioning
- **O2IMS Operator** for O-RAN O2 Infrastructure Management Service compliant cluster lifecycle
- **FOCOM Operator** for SMO/Orchestrator integration interface

### Key Features

- ✅ Multi-cluster lifecycle management from a single management plane
- ✅ O2IMS-style ProvisioningRequest API for cluster creation
- ✅ FOCOM interface for SMO/Orchestrator integration
- ✅ Bare-metal Kubernetes provisioning (no cloud dependency)
- ✅ Host pinning for deterministic cluster placement
- ✅ Status reporting through the provisioning chain

---

## 🏗️ Architecture

```
                           SMO / Orchestrator
                                   │
                                   │ FocomProvisioningRequest
                                   ▼
┌──────────────────────────────────────────────────────────────┐
│                    BYOH Management Cluster                   │
│                                                              │
│   ┌─────────────────┐       ┌─────────────────┐              │
│   │  FOCOM Operator │──────▶│  O2IMS Operator │              │
│   │ (focom-system)  │       │ (o2ims-system)  │              │
│   └─────────────────┘       └────────┬────────┘              │
│           │                          │                       │
│           │                          │ Creates CAPI Resources│
│           │                          ▼                       │
│           │                 ┌─────────────────┐              │
│           │                 │ BYOH Controller │              │
│           │                 │  (byoh-system)  │              │
│           │                 └────────┬────────┘              │
└───────────┼──────────────────────────┼───────────────────────┘
            │                          │
            │                          │ Provisions on bare-metal
            │                          ▼
            │              ┌───────────────────────┐
            │              │   Workload Clusters   │
            │              │  ┌─────┐   ┌─────┐    │
            │              │  │core │   │edge │    │
            │              │  └─────┘   └─────┘    │
            │              └───────────────────────┘
            │
     Creates ProvisioningRequest
```

### Component Roles

| Component | Role | Input | Output |
|-----------|------|-------|--------|
| **FOCOM Operator** | SMO-facing interface | `FocomProvisioningRequest` | Creates `ProvisioningRequest` |
| **O2IMS Operator** | Cluster lifecycle manager | `ProvisioningRequest` | Creates BYOH CAPI resources |
| **BYOH Controller** | Bare-metal provisioner | CAPI resources | Kubernetes cluster on hosts |

---

## 🔄 Workflow

### Fully Automated Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AUTOMATED PROVISIONING FLOW                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Clone Repo          2. Run mgmt.sh         3. Edit Configs              │
│  ─────────────          ─────────────          ─────────────                │
│  git clone ...    ──▶   ./mgmt.sh        ──▶   vi input.json                │
│                         (~30 mins)              vi examples/focom-...yaml   │
│                                                                             │
│  4. Apply Request       5. Watch Magic         6. Cluster Ready!            │
│  ───────────────        ─────────────          ──────────────               │
│  kubectl apply    ──▶   Auto-Ansible     ──▶   kubectl get clusters         │
│  -f focom-...yaml       Auto-CAPI              ✅ edge: Ready               |
│                         (~5-10 mins)                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Management Cluster Setup (One-time, ~30 mins)

```bash
./mgmt.sh
```

This installs:
- Kubernetes management cluster
- CAPI + BYOH provider
- O2IMS Operator
- FOCOM Operator
- Ansible Runner Image (for automation)

### Phase 2: Configure Host Details

Edit `input.json` with your worker host information:
```json
{
  "hosts": [
    {
      "host_id": 1,
      "host_name": "byoh-1",
      "host_ip": "10.x.x.x",
      "host_user": "ubuntu"
    }
  ]
}
```

Edit `examples/focom-provisioning-request.yaml` with matching host details:
```yaml
templateParameters:
  clusterName: edge
  hosts:
    masters:
      - hostId: 1
        hostName: byoh-1
        hostIp: "10.x.x.x"
```

> [!IMPORTANT]
> Host details in `input.json` and `focom-provisioning-request.yaml` **must match**. See [CLUSTER-CONFIGURATION.md](CLUSTER-CONFIGURATION.md) for details.

### Phase 3: Create Cluster (Fully Automated!)

```bash
kubectl apply -f examples/focom-provisioning-request.yaml
```

**What happens automatically:**
1. FOCOM creates ProvisioningRequest
2. O2IMS checks if hosts are registered
3. If not → **Ansible Job runs automatically** to prepare hosts
4. BYOH CAPI resources are created
5. Cluster is provisioned

### Phase 4: Monitor & Access

```bash
# Watch provisioning status
kubectl get focomprovisioningrequests -w
kubectl get provisioningrequests -w
kubectl get clusters -w

# Access workload cluster
kubectl get secret <cluster>-kubeconfig -o jsonpath='{.data.value}' | base64 -d > cluster.kubeconfig
kubectl --kubeconfig=cluster.kubeconfig get nodes
```

---

## 🎯 How This Completes the LCM O2IMS Objective

### Objective: Multi-Cluster LCM with O2IMS Support

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| **Multi-Cluster Management** | Single management plane provisions multiple workload clusters | ✅ |
| **Lifecycle Management** | Create, monitor, delete clusters via ProvisioningRequest | ✅ |
| **O2IMS Interface** | `ProvisioningRequest` CRD with status reporting | ✅ |
| **Bare-Metal Support** | CAPI BYOH provisions on Linux servers | ✅ |
| **Orchestrator Integration** | FOCOM provides SMO-facing interface | ✅ |
| **Automated Host Registration** | Ansible runs automatically if hosts not registered | ✅ |

### O2IMS ProvisioningRequest Lifecycle

```
                    ProvisioningRequest Created
                              │
                              ▼
                     ┌─────────────────┐
                     │    PENDING      │
                     └────────┬────────┘
                              │
               O2IMS checks if hosts registered
                              │
         ┌────────────────────┴────────────────────┐
         │                                         │
    Not Registered                            Registered
         │                                         │
         ▼                                         │
┌─────────────────┐                                │
│  PROGRESSING    │                                │
│ (Ansible Job)   │                                │
└────────┬────────┘                                │
         │                                         │
         └────────────────────┬────────────────────┘
                              │
                     BYOH provisions cluster
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     │                     ▼
┌─────────────┐               │            ┌─────────────┐
│  FULFILLED  │               │            │   FAILED    │
└─────────────┘               │            └─────────────┘
                              │
                     On delete request
                              │
                              ▼
                     ┌─────────────────┐
                     │   DELETING      │
                     └─────────────────┘
```

---

## 📁 Project Structure

```
BYOH-O2IMS-FOCOM/
├── mgmt.sh                   # Management cluster setup script
├── site.yaml                 # Ansible playbook for host registration
├── input.json                # Host inventory (for Ansible)
├── o2ims-operator/           # O2IMS Operator
│   ├── controllers/          # Python controller logic
│   │   ├── provisioning_request_controller.py
│   │   └── ansible_job_manager.py    # Automated Ansible execution
│   ├── ansible-runner/       # Custom Ansible container
│   │   └── Dockerfile
│   ├── crds/                 # ProvisioningRequest CRD
│   ├── deploy/               # Kubernetes deployment
│   └── Dockerfile
├── focom-operator/           # FOCOM Operator
│   ├── focom_controller.py   # Controller logic
│   ├── deployment.yaml       # Kubernetes deployment
│   └── Dockerfile
├── examples/                 # Sample CRs
│   ├── o2ims-provisioning-request.yaml
│   └── focom-provisioning-request.yaml
├── CLUSTER-CONFIGURATION.md  # Configuration guide
├── FEATURE-MATRIX.md         # Roadmap
└── templates/                # Cluster templates
```

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone <repo-url>
cd BYOH-O2IMS-FOCOM

# 2. Setup management cluster (~30 mins)
./mgmt.sh

# 3. Configure hosts
vi input.json                              # Add your host details
vi examples/focom-provisioning-request.yaml # Add matching host details

# 4. Create cluster (FULLY AUTOMATED!)
kubectl apply -f examples/focom-provisioning-request.yaml

# 5. Monitor
kubectl get focomprovisioningrequests -w
kubectl get clusters -w

# 6. Access workload cluster
kubectl get secret edge-kubeconfig -o jsonpath='{.data.value}' | base64 -d > edge.kubeconfig
kubectl --kubeconfig=edge.kubeconfig get nodes
```

---

## ✅ Tested Results

| Test | Result |
|------|--------|
| O2IMS Operator deployment | ✅ Running |
| FOCOM Operator deployment | ✅ Running |
| Host registration (4 hosts) | ✅ Registered |
| O2IMS → Cluster creation | ✅ `core` cluster provisioned |
| FOCOM → O2IMS → Cluster creation | ✅ `edge` cluster provisioned |
| Workload cluster access | ✅ Nodes Ready |

---

## 📄 License

Apache License 2.0
