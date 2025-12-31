# Helm Image Update Strategy – Design & Evaluation

## Objective

The goal is to systematically manage and update container image references across a large set of Helm charts used in Near-RT-RIC and SMO deployments, without manually editing dozens of charts for every release.


## Proposed Core Approach (Helm-Native)

### 1. Use `helm template` for Image Discovery

`helm template` renders Helm charts into Kubernetes YAML **without deploying**.

This allows us to:

- See the final rendered manifests
- Extract actual image references, regardless of where they are defined

**Example:**

```bash
helm template mychart ./chart-path
```

This output includes:

```yaml
image: nexus3.onap.org:10001/onap/policy-pap:4.2.0
```

**Why this works:**

- Handles multiple containers per pod
- Handles indirect image references
- Independent of chart structure

---

### 2. Image Inventory Generation

Using rendered manifests, we can:

- Parse all `image:` fields
- Build a complete inventory:

```
chart → template → container → image → tag
```

This provides:

- **Visibility**
- **Validation** against expected versions
- **Input** for automated updates

---

### 3. Image Update Strategy (Pre-Deployment)

Instead of editing templates manually:

- **Maintain a central image mapping file**, for example:

```yaml
policy-pap:
  repository: nexus3.onap.org:10001/onap/policy-pap
  tag: 4.2.1

sdnc:
  repository: nexus3.onap.org:10001/onap/sdnc
  tag: 2.6.0
```

Then:

- Programmatically update corresponding values or template references
- Re-render using `helm template`
- Validate updated output

This keeps:

- Charts reusable
- Customization external
- Upstream sync manageable

---

## Helm Overrides – Where They Help (and Where They Don't)

### What Helm overrides are good for

- Enabling/disabling components
- Feature flags
- Resource tuning
- Application logic configuration

### Limitations for image updates

- Overrides must exactly match `values.yaml` structure
- Fails when:
  - Image is hardcoded
  - Multiple images exist in one chart
  - Image keys differ across charts

➡️ **Overrides alone are not sufficient for large-scale image lifecycle management.**

---

## Chart Serving Strategy (Local vs Upstream)

### Option A: Use Upstream Helm Repos

- ✅ Simple
- ✅ Always latest charts
- ❌ Less control

### Option B: Serve Locally (ChartMuseum)

- ✅ Full control
- ✅ Enables customization
- ✅ Required for:
  - Air-gapped environments
  - CI/CD pipelines
  - Image version enforcement

**ChartMuseum allows:**

```bash
helm repo add local http://localhost:8879
helm install myapp local/mychart
```

---

## Keeping Charts in Sync with Upstream

**Recommended approach:**

- Track upstream repos via Git submodules or periodic sync
- Apply non-invasive customization layers
- Avoid direct fork divergence

**Workflow:**

```
Upstream Charts
     ↓
Local Copy
     ↓
Image Update Tool
     ↓
Local Chart Repo
     ↓
Deployment
```

---

## Evaluation of Other Tools

### Helmfile

**What it is:**

- Declarative wrapper for Helm
- Manages multiple charts + values

**Pros:**

- ✅ Centralized configuration
- ✅ Good for environments with fixed chart structure

**Cons:**

- ❌ Does not solve image discovery
- ❌ Still depends on chart structure correctness
- ❌ Limited for deeply nested / hardcoded images

**Verdict:**

- ✔ Useful for orchestration
- ✖ Not sufficient alone for image update problem

---

### Flux / ArgoCD (GitOps)

**What they are:**

- Continuous deployment controllers
- Sync cluster state from Git

**Pros:**

- ✅ Excellent for runtime drift control
- ✅ Versioned deployments

**Cons:**

- ❌ Operate after charts are prepared
- ❌ Do not modify Helm charts
- ❌ Require image update logic upstream

**Verdict:**

- ✔ Great for deployment enforcement
- ✖ Not designed for Helm chart preprocessing

---

## Recommended Architecture

```
           Upstream Helm Charts
                    |
                    v
           Local Helm Chart Workspace
                    |
         (helm template + image scan)
                    |
           Image Mapping / Policy
                    |
         Automated Image Update Tool
                    |
            Local Chart Repository
               (ChartMuseum)
                    |
             SMO / Near-RT-RIC
                  Deployment
```

---

## Conclusion

- **Helm-native rendering (`helm template`)** is the key enabler
- **Image updates must be handled pre-deployment**
- **Helm overrides help, but are insufficient alone**
- **Helmfile and GitOps tools complement—but do not replace—this approach**
- **A structured image update workflow enables:**
  - Scalability
  - Repeatability
  - Release independence


**Document Version:** 1.0  
**Date:** December 2025  
**Status:** Design & Evaluation Document

