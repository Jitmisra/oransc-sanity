# FOCOM and O2IMS Integration Guide

## Overview

This project integrates **FOCOM** and **O2IMS** operators to enable O-RAN-compliant Kubernetes cluster provisioning on bare-metal servers using BYOH CAPI provider.

---

## Complete Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE PROVISIONING FLOW                                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐    │
│   │                         USER / SMO                                  │    │
│   │                                                                     │    │
│   │   Edits: input.json (hosts, clusters)                               │    │
│   │   Runs:  kubectl apply -f examples/focom-all-clusters.yaml          │    │
│   │                                                                     │    │
│   └────────────────────────────────┬────────────────────────────────────┘    │
│                                    │                                         │
│                                    │ Creates FocomProvisioningRequest CR     │
│                                    ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐    │
│   │                      FOCOM OPERATOR                                 │    │
│   │                   (focom-system namespace)                          │    │
│   ├─────────────────────────────────────────────────────────────────────┤    │
│   │                                                                     │    │
│   │   1. Watches FocomProvisioningRequest                               │    │
│   │   2. Reads input.json (mounted via hostPath)                        │    │
│   │   3. Validates cluster configuration                                │    │
│   │   4. Checks host availability (feasibility)                         │    │
│   │   5. Creates ProvisioningRequest(s) for each cluster                │    │
│   │   6. Updates FPR status → "Synced"                                  │    │
│   │                                                                     │    │
│   │   Supports:                                                         │    │
│   │     - allClusters: true       → All clusters from input.json        │    │
│   │     - clusterNames: [...]     → Selected clusters                   │    │
│   │     - templateParameters      → Full custom configuration           │    │
│   │                                                                     │    │
│   └────────────────────────────────┬────────────────────────────────────┘    │
│                                    │                                         │
│                                    │ Creates ProvisioningRequest CR          │
│                                    ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐    │
│   │                      O2IMS OPERATOR                                 │    │
│   │                   (o2ims-system namespace)                          │    │
│   ├─────────────────────────────────────────────────────────────────────┤    │
│   │                                                                     │    │
│   │   7. Watches ProvisioningRequest                                    │    │
│   │   8. Status → "progressing"                                         │    │
│   │                                                                     │    │
│   │   ┌──────────────────────────────────────────────────────────────┐  │    │
│   │   │            STEP A: HOST PREPARATION (Ansible)                │  │    │
│   │   ├──────────────────────────────────────────────────────────────┤  │    │
│   │   │                                                              │  │    │
│   │   │   9. Creates Kubernetes Job with Ansible container           │  │    │
│   │   │  10. Runs: ansible-playbook site.yaml                        │  │    │
│   │   │                                                              │  │    │
│   │   │      On each target host (via SSH):                          │  │    │
│   │   │      ├── Install containerd                                  │  │    │
│   │   │      ├── Install kubelet, kubeadm, kubectl                   │  │    │
│   │   │      ├── Start BYOH agent                                    │  │    │
│   │   │      └── Agent registers as ByoHost CR                       │  │    │
│   │   │                                                              │  │    │
│   │   │  11. Wait for ByoHosts to register                           │  │    │
│   │   │                                                              │  │    │
│   │   └──────────────────────────────────────────────────────────────┘  │    │
│   │                                                                     │    │
│   │   ┌──────────────────────────────────────────────────────────────┐  │    │
│   │   │            STEP B: CAPI RESOURCE CREATION                    │  │    │
│   │   ├──────────────────────────────────────────────────────────────┤  │    │
│   │   │                                                              │  │    │
│   │   │  12. Generates BYOH CAPI resources:                          │  │    │
│   │   │                                                              │  │    │
│   │   │      ┌─────────────────┐    ┌─────────────────────────────┐  │  │    │
│   │   │      │    Cluster      │───▶│       ByoCluster            │  │  │    │
│   │   │      └────────┬────────┘    │   (controlPlaneEndpoint)    │  │  │    │
│   │   │               │             └─────────────────────────────┘  │  │    │
│   │   │               │                                              │  │    │
│   │   │               ▼                                              │  │    │
│   │   │      ┌─────────────────────────────────────────────────────┐ │  │    │
│   │   │      │        KubeadmControlPlane                          │ │  │    │
│   │   │      │   (replicas, version, kubeadmConfigSpec)            │ │  │    │
│   │   │      └────────┬────────────────────────────────────────────┘ │  │    │
│   │   │               │                                              │  │    │
│   │   │               ▼                                              │  │    │
│   │   │      ┌─────────────────────────────────────────────────────┐ │  │    │
│   │   │      │        ByoMachineTemplate (control-plane)           │ │  │    │
│   │   │      │   selector: host-id=1  (pins to specific host)      │ │  │    │
│   │   │      └─────────────────────────────────────────────────────┘ │  │    │
│   │   │                                                              │  │    │
│   │   │               ▼                                              │  │    │
│   │   │      ┌─────────────────────────────────────────────────────┐ │  │    │
│   │   │      │        MachineDeployment (workers)                  │ │  │    │
│   │   │      │   replicas: N, version, infrastructureRef           │ │  │    │
│   │   │      └────────┬────────────────────────────────────────────┘ │  │    │
│   │   │               │                                              │  │    │
│   │   │               ▼                                              │  │    │
│   │   │      ┌─────────────────────────────────────────────────────┐ │  │    │
│   │   │      │        ByoMachineTemplate (workers)                 │ │  │    │
│   │   │      │   selector: host-id=2,3,... (pins to hosts)         │ │  │    │
│   │   │      └─────────────────────────────────────────────────────┘ │  │    │
│   │   │                                                              │  │    │
│   │   │  13. Applies all resources to cluster                       │  │    │
│   │   │                                                              │  │    │
│   │   └──────────────────────────────────────────────────────────────┘  │    │
│   │                                                                     │    │
│   └────────────────────────────────┬────────────────────────────────────┘    │
│                                    │                                         │
│                                    │ CAPI Resources Applied                  │
│                                    ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐    │
│   │                   BYOH + CAPI CONTROLLERS                           │    │
│   │                   (capi-system namespace)                           │    │
│   ├─────────────────────────────────────────────────────────────────────┤    │
│   │                                                                     │    │
│   │  14. BYOH Controller watches ByoMachineTemplate                     │    │
│   │  15. Matches ByoHost by selector (host-id label)                    │    │
│   │  16. Claims ByoHost → Status changes to "in-use"                    │    │
│   │                                                                     │    │
│   │  17. CAPI Controllers orchestrate:                                  │    │
│   │      ├── Control plane bootstrap (kubeadm init)                     │    │
│   │      ├── Certificate generation                                     │    │
│   │      ├── etcd initialization                                        │    │
│   │      └── Worker node join (kubeadm join)                            │    │
│   │                                                                     │    │
│   │  18. CNI installed (Calico) on workload cluster                     │    │
│   │                                                                     │    │
│   │  19. Machine status → "Running"                                     │    │
│   │  20. Cluster status → "Provisioned"                                 │    │
│   │                                                                     │    │
│   └────────────────────────────────┬────────────────────────────────────┘    │
│                                    │                                         │
│                                    │ Status Propagation                      │
│                                    ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐    │
│   │                      STATUS UPDATES                                 │    │
│   ├─────────────────────────────────────────────────────────────────────┤    │
│   │                                                                     │    │
│   │  21. Cluster → "Provisioned"                                        │    │
│   │                   │                                                 │    │
│   │                   ▼                                                 │    │
│   │  22. ProvisioningRequest.status → "fulfilled"                       │    │
│   │                   │                                                 │    │
│   │                   ▼                                                 │    │
│   │  23. FocomProvisioningRequest.status → "Synced"                     │    │
│   │                                                                     │    │
│   └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│                                    │                                         │
│                                    ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐    │
│   │                    WORKLOAD CLUSTER READY                           │    │
│   ├─────────────────────────────────────────────────────────────────────┤    │
│   │                                                                     │    │
│   │   ✅ Control plane nodes: Running                                   │    │
│   │   ✅ Worker nodes: Running                                          │    │
│   │   ✅ CNI (Calico): Installed                                        │    │
│   │   ✅ CoreDNS: Running                                               │    │
│   │   ✅ kubeconfig secret: Available                                   │    │
│   │                                                                     │    │
│   │   Access:                                                           │    │
│   │   kubectl get secret <cluster>-kubeconfig -o jsonpath=...           │    │
│   │                                                                     │    │
│   └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## What is O2IMS?

**O2IMS** (O-RAN O2 Infrastructure Management Service) provides a standardized interface for managing O-Cloud infrastructure.

| Function | Description |
|----------|-------------|
| Provisioning | Create/manage workload clusters |
| Lifecycle | Create, update, delete infrastructure |

---

## What is FOCOM?

**FOCOM** (Front-Office Component) is the SMO-facing interface that translates external requests to O2IMS format.

| Function | Description |
|----------|-------------|
| Abstraction | Simplified cluster provisioning API |
| Batch support | Create multiple clusters at once |
| Status sync | Report provisioning status |

---

## CRDs

### FocomProvisioningRequest

| Field | Purpose |
|-------|---------|
| `allClusters` | Create all clusters from input.json |
| `clusterNames` | Create selected clusters |
| `templateParameters` | Full cluster configuration |
| `operation` | create / scale / delete |

### ProvisioningRequest

| Field | Purpose |
|-------|---------|
| `templateParameters.clusterName` | Cluster name |
| `templateParameters.hosts` | Host assignments |
| `status.provisioningState` | pending/progressing/fulfilled |

---

## Provisioning Options

### Option A: Batch All
```yaml
spec:
  allClusters: true
```

### Option B: Batch Selected
```yaml
spec:
  clusterNames: ["smo", "ran"]
```

### Option C: Template-based
```yaml
spec:
  templateName: "byoh-workload-cluster"
  templateParameters:
    clusterName: myCluster
    hosts: {...}
```

---

## Status Flow

```
Cluster          →    O2IMS              →    FOCOM
─────────             ─────────               ─────────
Provisioning          progressing             Creating
Provisioned           fulfilled               Synced
Failed                failed                  Failed
```