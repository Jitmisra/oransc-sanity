# Cluster Configuration Guide

This guide explains how to configure the `FocomProvisioningRequest` or `ProvisioningRequest` to create clusters with your desired settings.

---

## Quick Reference

| Configuration | Field | Example |
|---------------|-------|---------|
| Cluster name | `templateParameters.clusterName` | `edge`, `production` |
| Kubernetes version | `templateParameters.k8sVersion` | `v1.32.0` |
| Master nodes | `templateParameters.hosts.masters` | Array of host entries |
| Worker nodes | `templateParameters.hosts.workers` | Array of host entries |

---

> [!IMPORTANT]
> ## Matching Host Details
> 
> The `input.json` (for Ansible) and `focom-provisioning-request.yaml` (for CAPI) **must have matching host details**:
> 
> **input.json** (Ansible will use this to prepare hosts):
> ```json
> {
>   "hosts": [
>     {
>       "host_id": 1,
>       "host_name": "byoh-1",
>       "host_ip": "10.204.86.147",
>       "host_user": "ubuntu"
>     }
>   ]
> }
> ```
> 
> **focom-provisioning-request.yaml** (O2IMS will use this for cluster creation):
> ```yaml
> templateParameters:
>   hosts:
>     masters:
>       - hostId: 1
>         hostName: byoh-1
>         hostIp: "10.204.86.147"
> ```
> 
> **Key fields that must match:**
> | Field | input.json | focom-provisioning-request.yaml |
> |-------|------------|--------------------------------|
> | Host ID | `host_id: 1` | `hostId: 1` |
> | Host Name | `host_name: "byoh-1"` | `hostName: "byoh-1"` |
> | Host IP | `host_ip: "10.x.x.x"` | `hostIp: "10.x.x.x"` |

---

## Supported Kubernetes Versions

| Version | Status |
|---------|--------|
| v1.34.0 | ✅ Supported |
| v1.33.0 | ✅ Supported |
| v1.32.0 | ✅ Supported (Default) |
| v1.31.0 | ✅ Supported |
| v1.30.0 | ✅ Supported |
| v1.29.0 | ✅ Supported |
| v1.28.0 | ✅ Supported |
| v1.27.0 | ✅ Supported |
| v1.26.0 | ✅ Supported |

---

## Template Structure

```yaml
apiVersion: focom.nephio.org/v1alpha1
kind: FocomProvisioningRequest
metadata:
  name: my-cluster-request        # Unique request name
  namespace: default
spec:
  oCloudId: "management-cluster"
  oCloudNamespace: "default"
  templateName: "byoh-workload-cluster"
  templateVersion: "v1.0.0"
  
  templateParameters:
    #--------------------------------------------------
    # CLUSTER NAME (Required)
    #--------------------------------------------------
    # Must be lowercase, valid DNS name (a-z, 0-9, -)
    clusterName: my-cluster
    
    #--------------------------------------------------
    # KUBERNETES VERSION (Optional, default: v1.32.0)
    #--------------------------------------------------
    k8sVersion: "v1.32.0"
    
    #--------------------------------------------------
    # CLUSTER PROVISIONER (Required)
    #--------------------------------------------------
    clusterProvisioner: byoh
    
    #--------------------------------------------------
    # HOST ASSIGNMENTS (Required)
    #--------------------------------------------------
    hosts:
      masters:
        - hostId: 1
          hostName: host1
          hostIp: "192.168.1.10"
      workers:
        - hostId: 2
          hostName: host2
          hostIp: "192.168.1.11"
```

---

## Configuration Examples

### 1. Development Cluster (1 node)

Single-node cluster for development/testing:

```yaml
templateParameters:
  clusterName: dev
  k8sVersion: "v1.32.0"
  clusterProvisioner: byoh
  hosts:
    masters:
      - hostId: 1
        hostName: dev-node
        hostIp: "192.168.1.10"
    workers: []
```

### 2. Small Cluster (1 master, 2 workers)

Minimal production setup:

```yaml
templateParameters:
  clusterName: small-prod
  k8sVersion: "v1.31.0"
  clusterProvisioner: byoh
  hosts:
    masters:
      - hostId: 1
        hostName: master1
        hostIp: "192.168.1.10"
    workers:
      - hostId: 2
        hostName: worker1
        hostIp: "192.168.1.11"
      - hostId: 3
        hostName: worker2
        hostIp: "192.168.1.12"
```

### 3. HA Cluster (3 masters, 3 workers)

High-availability production setup:

```yaml
templateParameters:
  clusterName: ha-production
  k8sVersion: "v1.30.0"
  clusterProvisioner: byoh
  hosts:
    masters:
      - hostId: 1
        hostName: m1
        hostIp: "192.168.1.10"
      - hostId: 2
        hostName: m2
        hostIp: "192.168.1.11"
      - hostId: 3
        hostName: m3
        hostIp: "192.168.1.12"
    workers:
      - hostId: 4
        hostName: w1
        hostIp: "192.168.1.20"
      - hostId: 5
        hostName: w2
        hostIp: "192.168.1.21"
      - hostId: 6
        hostName: w3
        hostIp: "192.168.1.22"
```

### 4. Edge Cluster with Custom Version

```yaml
templateParameters:
  clusterName: edge-site-01
  k8sVersion: "v1.28.0"
  clusterProvisioner: byoh
  hosts:
    masters:
      - hostId: 10
        hostName: edge-master
        hostIp: "10.0.0.10"
    workers:
      - hostId: 11
        hostName: edge-worker1
        hostIp: "10.0.0.11"
      - hostId: 12
        hostName: edge-worker2
        hostIp: "10.0.0.12"
```

---

## Field Reference

### clusterName

| Property | Value |
|----------|-------|
| Required | Yes |
| Type | String |
| Format | Lowercase letters, numbers, hyphens only |
| Example | `edge`, `production`, `site-01` |

### k8sVersion

| Property | Value |
|----------|-------|
| Required | No (default: v1.32.0) |
| Type | String |
| Format | `v<major>.<minor>.<patch>` |
| Range | v1.26.0 to v1.34.0 |

### hosts.masters

| Property | Value |
|----------|-------|
| Required | Yes (at least 1) |
| Type | Array |
| Recommended | 1 for dev, 3 for HA |

### hosts.workers

| Property | Value |
|----------|-------|
| Required | No |
| Type | Array |
| Note | 0 workers = control-plane-only cluster |

### Host Entry Fields

| Field | Required | Description |
|-------|----------|-------------|
| `hostId` | Yes | Unique integer ID for the host |
| `hostName` | Yes | Name matching ByoHost resource |
| `hostIp` | Yes | IP address or hostname |

---

## Validation Rules

1. **clusterName** must be unique across all clusters
2. **hostId** must be unique within a single cluster
3. **hostName** must match the registered ByoHost name
4. At least **1 master** is required
5. For HA, use **3 masters** (odd number for etcd quorum)

---

## How to Create Multiple Clusters

Create separate files for each cluster:

```
examples/
├── cluster-dev.yaml        # clusterName: dev
├── cluster-staging.yaml    # clusterName: staging
└── cluster-production.yaml # clusterName: production
```

Apply each one:
```bash
kubectl apply -f examples/cluster-dev.yaml
kubectl apply -f examples/cluster-staging.yaml
kubectl apply -f examples/cluster-production.yaml
```
