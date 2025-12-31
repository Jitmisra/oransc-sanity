# Workflow Diagram

## Provisioning Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        PHASE 1: One-Time Setup                           │
└──────────────────────────────────────────────────────────────────────────┘

                        ./mgmt.sh
                            │
                            ▼
              ┌──────────────────────────────┐
              │  Management Cluster Ready    │
              │  - CAPI + BYOH installed     │
              │  - O2IMS Operator running    │
              │  - FOCOM Operator running    │
              └──────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────┐
│                   PHASE 2: Create Cluster (On-Demand)                    │
└──────────────────────────────────────────────────────────────────────────┘

   USER CHOOSES ONE OF THESE APPROACHES:

   ┌─────────────────────────────────────────────────────────────────────┐
   │ OPTION A: Batch Provisioning (Recommended)                          │
   │                                                                     │
   │   kubectl apply -f examples/focom-all-clusters.yaml                 │
   │   # Uses: allClusters: true                                         │
   │   # Creates ALL clusters from input.json                            │
   │                                                                     │
   │   OR                                                                │
   │                                                                     │
   │   kubectl apply -f examples/focom-selected-clusters.yaml            │
   │   # Uses: clusterNames: ["smo", "ran"]                              │
   │   # Creates SELECTED clusters from input.json                       │
   └─────────────────────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────────────────────┐
   │ OPTION B: Template-based Provisioning                               │
   │                                                                     │
   │   kubectl apply -f examples/focom-provisioning-request.yaml         │
   │   # Uses: templateName + templateParameters                         │
   │   # Full control over cluster configuration                         │
   └─────────────────────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────────────────────┐
   │ OPTION C: Direct O2IMS (Skip FOCOM)                                 │
   │                                                                     │
   │   kubectl apply -f examples/o2ims-provisioning-request.yaml         │
   │   # Directly creates ProvisioningRequest                            │
   │   # No FOCOM abstraction                                            │
   └─────────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────┐
│                     INTERNAL FLOW (Automated)                            │
└──────────────────────────────────────────────────────────────────────────┘

    FocomProvisioningRequest
              │
              │  FOCOM Operator
              ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  1. Validates cluster configuration                                 │
    │  2. Checks host availability (feasibility)                          │
    │  3. Creates ProvisioningRequest(s)                                  │
    └──────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                      O2IMS Operator                                 │
    │                                                                     │
    │  4. Creates Kubernetes Job → Runs ansible-playbook site.yaml        │
    │     (Prepares hosts: containerd, kubelet, BYOH agent)               │
    │                                                                     │
    │  5. Waits for ByoHosts to register                                  │
    │                                                                     │
    │  6. Generates CAPI resources:                                       │
    │     - Cluster                                                       │
    │     - ByoCluster                                                    │
    │     - KubeadmControlPlane                                           │
    │     - MachineDeployment                                             │
    │                                                                     │
    │  7. Monitors until cluster is Provisioned                           │
    │  8. Updates status → "fulfilled"                                    │
    └──────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
              ┌──────────────────────────────┐
              │    Workload Cluster Ready    │
              │    - Control plane running   │
              │    - Workers joined          │
              │    - CNI installed (Calico)  │
              └──────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────┐
│                      PHASE 3: Day-2 Operations                           │
└──────────────────────────────────────────────────────────────────────────┘

   SCALING (requires new hosts registered)
   
   kubectl apply -f examples/focom-scale-cluster.yaml
   # Uses: operation: scale, targetWorkerCount: 3
   
   DELETION
   
   kubectl delete fpr <name>
   # CAPI cascades: deletes Cluster, Machines
   # ByoHosts remain for reuse
```