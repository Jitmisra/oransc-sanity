# Testing Guide

## Prerequisites

- Management cluster running (after `./mgmt.sh`)
- At least 2 physical Linux servers with SSH access
- Hosts defined in `input.json`

---

## Test 1: Verify Operator Deployment

```bash
# Check O2IMS operator
kubectl get pods -n o2ims-system
# Expected: o2ims-controller-xxx  Running

# Check FOCOM operator  
kubectl get pods -n focom-system
# Expected: focom-controller-xxx  Running

# Verify CRDs installed
kubectl get crd | grep -E "provisioning|focom"
```

✅ **Pass if:** Both operators running, CRDs exist

---

## Test 2: Batch Provisioning (Recommended)

```bash
# Provision ALL clusters from input.json
kubectl apply -f examples/focom-all-clusters.yaml

# Watch status
kubectl get fpr -w

# Verify ProvisioningRequests created
kubectl get provisioningrequests

# Watch cluster creation
kubectl get clusters -w
kubectl get machines -w
```

✅ **Pass if:** FPR shows `Synced`, Clusters show `Provisioned`

---

## Test 3: Selected Clusters

```bash
# Provision specific clusters
kubectl apply -f examples/focom-selected-clusters.yaml

# Watch
kubectl get fpr -w
kubectl get clusters
```

---

## Test 4: Template-based Provisioning

```bash
# Clean up previous
kubectl delete fpr --all

# Apply template-based request
kubectl apply -f examples/focom-provisioning-request.yaml

# Watch
kubectl get fpr -w
kubectl get provisioningrequests
kubectl get clusters
```

---

## Test 5: Direct O2IMS (Skip FOCOM)

```bash
# Apply directly to O2IMS
kubectl apply -f examples/o2ims-provisioning-request.yaml

# Watch
kubectl get provisioningrequests -w
kubectl get clusters
```

---

## Test 6: Workload Cluster Access

```bash
# Get cluster name
CLUSTER_NAME=$(kubectl get clusters -o jsonpath='{.items[0].metadata.name}')

# Get kubeconfig
kubectl get secret ${CLUSTER_NAME}-kubeconfig -o jsonpath='{.data.value}' | base64 -d > workload.kubeconfig

# Test workload cluster
kubectl --kubeconfig=workload.kubeconfig get nodes
kubectl --kubeconfig=workload.kubeconfig get pods -A
```

✅ **Pass if:** Nodes show Ready, system pods running

---

## Test 7: Scaling

```bash
# Ensure new host is registered first
kubectl get byohosts

# Apply scale request
kubectl apply -f examples/focom-scale-cluster.yaml

# Watch
kubectl get fpr -w
kubectl get machines -w
```

---

## Test 8: Cleanup (Delete Flow)

```bash
# Delete via FOCOM
kubectl delete fpr <name>

# Verify cascading delete
kubectl get provisioningrequests  # Should be deleted
kubectl get clusters              # Should be deleting

# ByoHosts remain for reuse
kubectl get byohosts
```

---

## Quick Validation Script

```bash
#!/bin/bash
echo "=== Integration Test Suite ==="

echo -e "\n[1/5] Checking Operators..."
kubectl get pods -n o2ims-system -o name 2>/dev/null | grep -q pod && echo "✅ O2IMS: Running" || echo "❌ O2IMS: Not running"
kubectl get pods -n focom-system -o name 2>/dev/null | grep -q pod && echo "✅ FOCOM: Running" || echo "❌ FOCOM: Not running"

echo -e "\n[2/5] Checking CRDs..."
kubectl get crd provisioningrequests.o2ims.provisioning.oran.org &>/dev/null && echo "✅ O2IMS CRD" || echo "❌ O2IMS CRD"
kubectl get crd focomprovisioningrequests.focom.nephio.org &>/dev/null && echo "✅ FOCOM CRD" || echo "❌ FOCOM CRD"

echo -e "\n[3/5] Checking ByoHosts..."
HOSTS=$(kubectl get byohosts --no-headers 2>/dev/null | wc -l)
echo "📦 Registered ByoHosts: $HOSTS"

echo -e "\n[4/5] FocomProvisioningRequests..."
kubectl get fpr 2>/dev/null || echo "(none)"

echo -e "\n[5/5] Clusters..."
kubectl get clusters 2>/dev/null || echo "(none)"

echo -e "\n=== Test Complete ==="
```

---

## Expected End State

| Component | Status |
|-----------|--------|
| O2IMS Operator | Running |
| FOCOM Operator | Running |
| ByoHosts | Registered |
| FocomProvisioningRequest | Synced |
| ProvisioningRequest | fulfilled |
| Cluster | Provisioned |