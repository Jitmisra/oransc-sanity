# BYOH-O2IMS-FOCOM Feature Matrix

## Overview

**Kubernetes Lifecycle Management (LCM) with O2IMS support** for bare-metal cluster provisioning using BYOH CAPI provider.

---

## Core Features

### 1. Batch Cluster Provisioning

Create multiple Kubernetes clusters with a single command.

| Mode | Field | Description |
|------|-------|-------------|
| **All Clusters** | `allClusters: true` | All clusters from input.json |
| **Selected** | `clusterNames: [...]` | Specific clusters |
| **Single** | `clusterName: "smo"` | One cluster |

**Example:**
```yaml
spec:
  allClusters: true
```

---

### 2. Template-based Provisioning

Full control with explicit cluster configuration.

```yaml
spec:
  templateName: "byoh-workload-cluster"
  templateParameters:
    clusterName: myCluster
    k8sVersion: "v1.32.0"
    hosts:
      masters:
        - hostId: 1
          hostName: byoh-1
          hostIp: "10.0.0.1"
      workers:
        - hostId: 2
          hostName: byoh-2
          hostIp: "10.0.0.2"
```

---

### 3. Direct O2IMS Provisioning

Skip FOCOM abstraction, create clusters directly via O2IMS.

```yaml
apiVersion: o2ims.provisioning.oran.org/v1alpha1
kind: ProvisioningRequest
spec:
  templateParameters:
    clusterName: directCluster
    hosts: {...}
```

---

### 4. Validation & Feasibility

Automatic checks before provisioning:

| Check | Description |
|-------|-------------|
| Cluster name | Valid DNS naming |
| Host availability | ByoHosts not already in use |
| Master count | Must be odd (1, 3, 5) |
| K8s version | Supported versions only |

---

### 5. Cluster Scaling

Add workers with new hosts.

```yaml
spec:
  operation: scale
  clusterName: "smo"
  targetWorkerCount: 3
```

> Requires new ByoHosts registered before scaling.

---

### 6. Cluster Deletion

Delete with cascade cleanup.

```bash
kubectl delete fpr <name>
# → ProvisioningRequest deleted
# → Cluster deleted
# → Machines deleted
# → ByoHosts remain (reusable)
```

---

## Operators

| Operator | Purpose |
|----------|---------|
| **FOCOM** | SMO interface, batch provisioning, validation |
| **O2IMS** | O-RAN compliant API, CAPI resource creation |

---

## CRDs

| CRD | Purpose |
|-----|---------|
| `FocomProvisioningRequest` | User entry point |
| `ProvisioningRequest` | O2IMS provisioning |
| `ClusterTemplate` | Pre-defined configs |

---

## Example Files

| File | Purpose |
|------|---------|
| `focom-all-clusters.yaml` | Batch all |
| `focom-selected-clusters.yaml` | Batch selected |
| `focom-provisioning-request.yaml` | Template-based |
| `focom-scale-cluster.yaml` | Scaling |
| `o2ims-provisioning-request.yaml` | Direct O2IMS |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER                                    │
│                           │                                     │
│              kubectl apply FocomProvisioningRequest             │
│                           ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ FOCOM Operator                                           │   │
│  │  → Validates config                                      │   │ 
│  │  → Checks feasibility                                    │   │
│  │  → Creates ProvisioningRequest                           │   │
│  └─────────────────────────┬────────────────────────────────┘   │
│                            ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ O2IMS Operator                                           │   │
│  │  → Runs Ansible (host prep)                              │   │
│  │  → Creates CAPI resources                                │   │
│  │  → Monitors cluster status                               │   │
│  └─────────────────────────┬────────────────────────────────┘   │
│                            ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ BYOH + CAPI                                              │   │
│  │  → Claims hosts                                          │   │
│  │  → Bootstraps Kubernetes                                 │   │
│  │  → Installs CNI (Calico)                                 │   │
│  └─────────────────────────┬────────────────────────────────┘   │
│                            ▼                                    │
│              ┌──────────────────────────┐                       │
│              │   Workload Cluster Ready │                       │
│              └──────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# 1. Configure hosts
vim input.json

# 2. Deploy operators
./mgmt.sh deploy-o2ims-operator
./mgmt.sh deploy-focom-operator

# 3. Provision all clusters
kubectl apply -f examples/focom-all-clusters.yaml

# 4. Watch
kubectl get fpr -w
kubectl get clusters -w
kubectl get machines -w
```

---

## Files

```
BYOH-O2IMS-FOCOM/
├── input.json                    # Host/cluster config
├── mgmt.sh                       # Setup script
├── site.yaml                     # Ansible playbook
├── focom-operator/
│   ├── focom_controller.py
│   └── focomprovisioningrequest-crd.yaml
├── o2ims-operator/
│   ├── controllers/
│   └── crds/
└── examples/
    ├── focom-all-clusters.yaml
    ├── focom-selected-clusters.yaml
    ├── focom-provisioning-request.yaml
    ├── focom-scale-cluster.yaml
    └── o2ims-provisioning-request.yaml
```
