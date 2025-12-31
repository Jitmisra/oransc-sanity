# Cluster Configuration Guide

## Provisioning Options

| Approach | Best For | Example File |
|----------|----------|--------------|
| **Batch (all)** | Deploy all clusters | `focom-all-clusters.yaml` |
| **Batch (selected)** | Deploy specific clusters | `focom-selected-clusters.yaml` |
| **Template-based** | Custom configuration | `focom-provisioning-request.yaml` |
| **Direct O2IMS** | Skip FOCOM abstraction | `o2ims-provisioning-request.yaml` |

---

## Batch Provisioning (Recommended)

Uses `input.json` for cluster definitions.

### All Clusters
```yaml
apiVersion: focom.nephio.org/v1alpha1
kind: FocomProvisioningRequest
metadata:
  name: provision-all
spec:
  allClusters: true
```

### Selected Clusters
```yaml
spec:
  clusterNames: ["smo", "ran", "core"]
```

---

## Template-based Configuration

Full control over cluster parameters.

```yaml
apiVersion: focom.nephio.org/v1alpha1
kind: FocomProvisioningRequest
metadata:
  name: my-cluster-request
spec:
  templateName: "byoh-workload-cluster"
  templateParameters:
    clusterName: myCluster
    k8sVersion: "v1.32.0"
    clusterProvisioner: byoh
    hosts:
      masters:
        - hostId: 1
          hostName: byoh-1
          hostIp: "10.204.86.147"
      workers:
        - hostId: 2
          hostName: byoh-2
          hostIp: "10.204.86.148"
```

---

## Host Configuration

> [!IMPORTANT]
> The `input.json` and YAML files **must have matching host details**.

### input.json (for Ansible)
```json
{
  "hosts": [
    {
      "host_id": 1,
      "host_name": "byoh-1",
      "host_ip": "10.204.86.147",
      "host_user": "ubuntu"
    }
  ]
}
```

### YAML (for O2IMS)
```yaml
hosts:
  masters:
    - hostId: 1
      hostName: byoh-1
      hostIp: "10.204.86.147"
```

### Field Mapping

| input.json | YAML | Must Match |
|------------|------|------------|
| `host_id: 1` | `hostId: 1` | ✅ |
| `host_name: "byoh-1"` | `hostName: "byoh-1"` | ✅ |
| `host_ip: "10.x.x.x"` | `hostIp: "10.x.x.x"` | ✅ |

---

## Supported Kubernetes Versions

| Version | Status |
|---------|--------|
| v1.34.0 | ✅ Supported |
| v1.33.0 | ✅ Supported |
| v1.32.0 | ✅ Supported (Default) |
| v1.31.0 | ✅ Supported |
| v1.30.0 | ✅ Supported |

---

## Cluster Topologies

### Single Node (Dev)
```yaml
hosts:
  masters:
    - hostId: 1
      hostName: dev-node
      hostIp: "192.168.1.10"
  workers: []
```

### 1 Master + 2 Workers
```yaml
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

### HA (3 Masters + 3 Workers)
```yaml
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

---

## Validation Rules

1. **clusterName** - Must be unique, valid DNS name
2. **hostId** - Must be unique within cluster
3. **hostName** - Must match registered ByoHost
4. **Masters** - At least 1 required, use 3 for HA
5. **Workers** - Optional, 0 = control-plane only

---

## Scaling

Add workers to existing cluster (requires new hosts):

```yaml
apiVersion: focom.nephio.org/v1alpha1
kind: FocomProvisioningRequest
metadata:
  name: scale-cluster
spec:
  operation: scale
  clusterName: "smo"
  targetWorkerCount: 3
```