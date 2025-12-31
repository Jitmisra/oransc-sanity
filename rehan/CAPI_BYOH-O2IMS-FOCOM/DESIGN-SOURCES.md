# Design Sources & References

## O-RAN Alliance Specifications

### O2IMS Interface (O-RAN.WG6.TS.O2IMS-INTERFACE)

| Used For | Reference |
|----------|-----------|
| ProvisioningRequest structure | Clause 3.4 - O2ims_InfrastructureProvisioning |
| Status states | Clause 3.4.4 - Data Types |
| templateParameters | Clause 3.4.4.2 - ProvisioningRequestInfo |

**Fields Derived:**
```yaml
spec:
  templateName: "..."            # O2IMS spec
  templateVersion: "..."         # O2IMS spec
  templateParameters: {...}      # O2IMS spec
status:
  provisioningState: "..."       # O2IMS spec
```

---

### FOCOM NBI (O-RAN.WG6.TR.FOCOM-NFO-SMOS-NBI)

| Used For | Reference |
|----------|-----------|
| FocomProvisioningRequest structure | Use Case 4.2.3 |
| Batch provisioning | Extended for allClusters/clusterNames |

---

## Cluster API (CAPI)

### Core Resources (cluster.x-k8s.io/v1beta1)

| Resource | Purpose |
|----------|---------|
| `Cluster` | Cluster definition |
| `MachineDeployment` | Worker node group |
| `KubeadmControlPlane` | Control plane |

---

### BYOH Provider (infrastructure.cluster.x-k8s.io/v1beta1)

| Resource | Purpose |
|----------|---------|
| `ByoCluster` | BYOH cluster infrastructure |
| `ByoHost` | Registered bare-metal host |
| `ByoMachineTemplate` | Machine template for BYOH |

**Source:** [BYOH Provider](https://github.com/vmware-tanzu/cluster-api-provider-bringyourownhost)

---

## Field Mapping

| ProvisioningRequest Field | Source |
|---------------------------|--------|
| `templateParameters.clusterName` | CAPI |
| `templateParameters.k8sVersion` | input.json |
| `templateParameters.hosts.masters` | input.json |
| `templateParameters.hosts.workers` | input.json |
| `templateParameters.hosts[].hostId` | input.json |
| `templateParameters.hosts[].hostName` | input.json (maps to ByoHost) |

---

## External Links

- [O-RAN Alliance Specifications](https://www.o-ran.org/specifications)
- [Cluster API Documentation](https://cluster-api.sigs.k8s.io/)
- [BYOH Provider](https://github.com/vmware-tanzu/cluster-api-provider-bringyourownhost)
- [Nephio Project](https://nephio.org/)