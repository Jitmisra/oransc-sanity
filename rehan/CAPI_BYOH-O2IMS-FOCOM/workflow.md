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

    1. Create ProvisioningRequest (or FocomProvisioningRequest)
    
       kubectl apply -f examples/focom-provisioning-request.yaml
                            │
                            ▼
    ┌────────────────────────────────────────────────────────────────────┐
    │                     FOCOM Operator                                 │
    │   - Receives FocomProvisioningRequest                              │
    │   - Creates O2IMS ProvisioningRequest                              │
    └──────────────────────────┬─────────────────────────────────────────┘
                               │
                               ▼
    ┌────────────────────────────────────────────────────────────────────┐
    │                      O2IMS Operator                                │
    │                                                                    │
    │   2. Check: Are hosts registered as ByoHosts?                      │
    │            │                                                       │
    │      ┌─────┴─────┐                                                 │
    │      │           │                                                 │
    │      ▼           ▼                                                 │
    │     YES          NO                                                │
    │      │           │                                                 │
    │      │     3. Create Kubernetes Job                                │
    │      │        └── Runs: ansible-playbook site.yaml  ◀── AUTOMATED  │
    │      │                │                                            │
    │      │                ▼                                            │
    │      │        4. Hosts registered as ByoHosts                      │
    │      │                │                                            │
    │      └────────────────┘                                            │
    │                       │                                            │
    │                       ▼                                            │
    │   5. Generate BYOH CAPI resources                                  │
    │   6. Apply Cluster, ByoCluster, KubeadmControlPlane, etc.          │
    │   7. Monitor until Provisioned                                     │
    │   8. Update status → "fulfilled"                                   │
    └──────────────────────────┬─────────────────────────────────────────┘
                               │
                               ▼
              ┌──────────────────────────────┐
              │    Workload Cluster Ready    │
              │    - Control plane running   │
              │    - Workers joined          │
              │    - CNI installed           │
              └──────────────────────────────┘