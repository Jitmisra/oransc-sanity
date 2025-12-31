# Testing Guide

## Prerequisites

```bash
# 1. Management cluster running with CAPI + BYOH
kubectl get pods -A | grep -E "capi|byoh"

# 2. Operators deployed
kubectl get pods -n o2ims-system
kubectl get pods -n focom-system

# 3. CRDs installed
kubectl get crd | grep -E "provisioning|focom"

# 4. ByoHosts registered
kubectl get byohosts
```

---

## Test 1: Operator Health

```bash
# O2IMS operator running
kubectl get pods -n o2ims-system
# Expected: o2ims-controller-xxx Running

# FOCOM operator running
kubectl get pods -n focom-system
# Expected: focom-controller-xxx Running
```

✅ **Pass if:** Both operators running

---

## Test 2: Batch Provisioning - All Clusters

```bash
# Apply all clusters
kubectl apply -f examples/focom-all-clusters.yaml

# Watch FPR status
kubectl get fpr -w
# Expected: Phase → Synced

# Check ProvisioningRequests created
kubectl get provisioningrequests
# Expected: One per cluster in input.json

# Watch clusters
kubectl get clusters -w
kubectl get machines -w
```

✅ **Pass if:** FPR Synced, clusters Provisioned

---

## Test 3: Batch Provisioning - Selected Clusters

```bash
kubectl apply -f examples/focom-selected-clusters.yaml

# Verify only specified clusters created
kubectl get provisioningrequests -l focom.nephio.org/source=create-selected-clusters
```

✅ **Pass if:** Only selected clusters created

---

## Test 4: Template-based Provisioning

```bash
# Apply template-based request
kubectl apply -f examples/focom-provisioning-request.yaml

# Watch
kubectl get fpr -w
kubectl get provisioningrequests
kubectl get clusters
```

✅ **Pass if:** Cluster created with specified parameters

---

## Test 5: Direct O2IMS Provisioning

```bash
# Skip FOCOM, apply directly to O2IMS
kubectl apply -f examples/o2ims-provisioning-request.yaml

# Watch
kubectl get provisioningrequests -w
kubectl get clusters
```

✅ **Pass if:** Cluster created without FPR

---

## Test 6: Validation - Invalid Template

```bash
cat <<EOF | kubectl apply -f -
apiVersion: focom.nephio.org/v1alpha1
kind: FocomProvisioningRequest
metadata:
  name: test-invalid-template
spec:
  templateName: "does-not-exist"
  templateParameters:
    clusterName: test
EOF

# Check status
kubectl get fpr test-invalid-template -o jsonpath='{.status.phase}'
# Expected: Failed

kubectl delete fpr test-invalid-template
```

✅ **Pass if:** Status = Failed

---

## Test 7: Validation - Even Masters

```bash
cat <<EOF | kubectl apply -f -
apiVersion: focom.nephio.org/v1alpha1
kind: FocomProvisioningRequest
metadata:
  name: test-even-masters
spec:
  templateName: "byoh-workload-cluster"
  templateParameters:
    clusterName: test
    hosts:
      masters:
        - hostName: m1
          hostIp: "10.0.0.1"
        - hostName: m2
          hostIp: "10.0.0.2"
      workers: []
EOF

kubectl get fpr test-even-masters -o jsonpath='{.status.message}'
# Expected: Contains "odd"

kubectl delete fpr test-even-masters
```

✅ **Pass if:** Fails with "odd" in message

---

## Test 8: Scaling

```bash
# Ensure new hosts are registered first
kubectl get byohosts

# Apply scale request
kubectl apply -f examples/focom-scale-cluster.yaml

# Watch
kubectl get fpr -w
kubectl get machines -w
```

✅ **Pass if:** Worker count increases

---

## Test 9: Workload Cluster Access

```bash
# Get cluster name
CLUSTER=$(kubectl get clusters -o jsonpath='{.items[0].metadata.name}')

# Get kubeconfig
kubectl get secret ${CLUSTER}-kubeconfig -o jsonpath='{.data.value}' | base64 -d > workload.kubeconfig

# Test
kubectl --kubeconfig=workload.kubeconfig get nodes
kubectl --kubeconfig=workload.kubeconfig get pods -A
```

✅ **Pass if:** Nodes Ready, system pods Running

---

## Test 10: Cleanup - Delete Flow

```bash
# Delete FPR
kubectl delete fpr <name>

# Verify cascade delete
kubectl get provisioningrequests  # Should be deleted
kubectl get clusters              # Should be deleting

# ByoHosts remain
kubectl get byohosts
```

✅ **Pass if:** Resources deleted, ByoHosts remain

---

## Quick Validation Script

```bash
#!/bin/bash
echo "=== BYOH-O2IMS-FOCOM Test Suite ==="

echo -e "\n[1/5] Checking Operators..."
kubectl get pods -n o2ims-system -o name 2>/dev/null | grep -q pod && echo "✅ O2IMS: Running" || echo "❌ O2IMS: Not running"
kubectl get pods -n focom-system -o name 2>/dev/null | grep -q pod && echo "✅ FOCOM: Running" || echo "❌ FOCOM: Not running"

echo -e "\n[2/5] Checking CRDs..."
kubectl get crd provisioningrequests.o2ims.provisioning.oran.org &>/dev/null && echo "✅ O2IMS CRD" || echo "❌ O2IMS CRD"
kubectl get crd focomprovisioningrequests.focom.nephio.org &>/dev/null && echo "✅ FOCOM CRD" || echo "❌ FOCOM CRD"

echo -e "\n[3/5] ByoHosts..."
HOSTS=$(kubectl get byohosts --no-headers 2>/dev/null | wc -l)
echo "📦 Registered: $HOSTS"

echo -e "\n[4/5] FocomProvisioningRequests..."
kubectl get fpr 2>/dev/null || echo "(none)"

echo -e "\n[5/5] Clusters..."
kubectl get clusters 2>/dev/null || echo "(none)"

echo -e "\n=== Done ==="
```

---

## Test Summary

| # | Test | Example File | Expected |
|---|------|--------------|----------|
| 1 | Operators | - | Both Running |
| 2 | Batch All | `focom-all-clusters.yaml` | All clusters created |
| 3 | Batch Selected | `focom-selected-clusters.yaml` | Only specified |
| 4 | Template-based | `focom-provisioning-request.yaml` | Custom config |
| 5 | Direct O2IMS | `o2ims-provisioning-request.yaml` | Skip FOCOM |
| 6 | Invalid Template | - | Failed status |
| 7 | Even Masters | - | Failed status |
| 8 | Scaling | `focom-scale-cluster.yaml` | Workers increase |
| 9 | Cluster Access | - | Nodes Ready |
| 10 | Delete | - | Cascade delete |
