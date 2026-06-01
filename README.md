<p>
<img src="https://raw.githubusercontent.com/cisco-atx/blueprint-netaudit/refs/heads/main/static/img/netaudit.ico" width="64">
</p>

# NetAudit
>Network Auditing and Compliance

## Overview

NetAudit is a network auditing and compliance validation module within the ATX (Automation Tooling) platform.

It is designed to automate device audits, compliance checks, operational validation, and migration readiness assessments across enterprise network environments.

NetAudit enables network engineers to create reusable audit checks, organize devices into logical audit groups, execute validations at scale, and generate actionable compliance reports.

By automating repetitive audit activities, NetAudit helps reduce migration risk, improve consistency, and accelerate network transformation projects.

---

## Why NetAudit?

Network migrations and infrastructure changes often require engineers to answer critical questions before and after implementation:

* Are devices configured according to standards?
* Are migration prerequisites satisfied?
* Are security controls compliant?
* Are routing and infrastructure services configured correctly?
* Which devices require remediation before migration?
* Which audit findings require follow-up actions?
* Can migration readiness be validated consistently across all devices?

Traditionally these activities require engineers to manually connect to devices, execute commands, review outputs, and document findings.

NetAudit automates this process by executing reusable audit checks, collecting device facts, evaluating compliance conditions, and generating structured audit results.

---

## NetAudit in ATX

NetAudit is implemented as a Flask Blueprint and integrates directly into the ATX platform.

### Blueprint Metadata

| Property    | Value                           |
| ----------- | ------------------------------- |
| Name        | NetAudit                        |
| Version     | 1.0.0                           |
| URL Prefix  | `/netaudit`                     |
| Description | Network Auditing and Compliance |

---

## Core Capabilities

### Audit Check Framework

NetAudit uses a modular Python-based audit framework that allows engineers to develop reusable compliance and validation checks.

Each check can:

* Execute one or more device commands
* Parse command output
* Evaluate compliance conditions
* Generate observations
* Record audit findings
* Return standardized status codes

Checks are dynamically loaded during runtime and can be updated without modifying the core platform.

---

### Device Management

NetAudit maintains an inventory of managed network devices.

Features include:

* Device onboarding
* Bulk device management
* Connector assignment
* View-based organization
* Audit result persistence

Devices can participate in multiple audit workflows throughout a migration lifecycle.

---

### Views-Based Organization

Devices and checks are organized using Views.

A View represents a logical audit group and defines:

* Associated devices
* Applicable audit checks
* Reporting scope
* Audit visibility

Example Views:

* Core Network
* WAN Infrastructure
* Campus Access
* Data Center
* Migration Wave 1
* Migration Wave 2

This allows different audit policies to be applied to different device groups.

---

### Connector Management

NetAudit supports reusable connection profiles called Connectors.

Connector profiles contain:

* Network credentials
* Jump host information
* Authentication parameters

Features include:

* Secure credential storage
* Password encryption
* Jump host support
* Reusable connectivity profiles

This simplifies audit execution across large environments.

---

### Fact Gathering Framework

NetAudit supports dynamic fact collection through Fact Gatherers.

Fact gatherers execute independently of audit checks and collect reusable device information.

Examples include:

* Platform information
* Software versions
* Hardware inventory
* Interface statistics
* System characteristics
* Device metadata

Collected facts are made available to audit checks through the audit context.

---

### Parallel Audit Execution

NetAudit executes audits concurrently using a ThreadPoolExecutor.

Benefits include:

* Faster audit completion
* Reduced maintenance windows
* Improved scalability
* Better support for large migration projects

Multiple devices can be audited simultaneously while sharing reusable command outputs where applicable.

---

## Audit Execution Workflow

### Step 1 – Create Audit Checks

Engineers create or import audit checks.

Checks define:

* Commands to execute
* Parsing logic
* Compliance rules
* Result handling

---

### Step 2 – Define Views

Create Views that represent audit groups.

Examples:

* Branch Routers
* Core Switches
* Firewall Estate
* Migration Candidates

Views determine which checks are executed against which devices.

---

### Step 3 – Register Devices

Devices are added to NetAudit and associated with:

* Views
* Connectors
* Audit policies

---

### Step 4 – Execute Audit

NetAudit:

1. Establishes connectivity
2. Collects facts
3. Executes audit checks
4. Evaluates compliance
5. Stores results

Audits can be executed against:

* Individual devices
* Entire views
* Migration-specific device groups

---

### Step 5 – Review Findings

Results are presented through the NetAudit reporting interface.

Engineers can:

* Review findings
* Record remediation actions
* Add comments
* Track exceptions
* Accept risks

---

## Quick Audit

NetAudit includes a Quick Audit capability designed for rapid validation activities.

Quick Audit allows engineers to:

* Select devices
* Select checks
* Provide credentials
* Execute audits immediately

Without requiring device onboarding or view configuration.

Typical use cases include:

* Pre-change validation
* Emergency troubleshooting
* Pilot migrations
* One-time compliance reviews

---

## Audit Status Model

Each audit check returns a standardized status.

| Status       | Description                                |
| ------------ | ------------------------------------------ |
| NOT RUN      | Check has not been executed                |
| PASS         | Compliance requirement satisfied           |
| FAIL         | Compliance violation detected              |
| WARN         | Best-practice deviation or risk identified |
| INFO         | Informational observation                  |
| ERROR        | Execution or parsing failure               |
| INCONCLUSIVE | Insufficient information available         |

These statuses are used consistently throughout reporting and exports.

---

## Results Management

NetAudit stores audit results per device.

Stored information includes:

* Audit timestamp
* Login status
* Hostname
* Raw command outputs
* Gathered facts
* Individual check results
* Overall device status
* User actions
* User comments

This enables both operational review and long-term audit tracking.

---

## Reporting and Evidence Collection

### Results Dashboard

NetAudit provides centralized reporting for:

* View-level summaries
* Device-level drill-down
* Audit status visibility
* Compliance tracking

---

### Device Audit Reports

Engineers can review detailed audit results including:

* Check status
* Observations
* Findings
* Comments
* Device facts

---

### Snapshot Reports

Audit results can be exported as standalone HTML reports.

Typical use cases include:

* CAB submissions
* Migration evidence
* Compliance reviews
* Customer deliverables
* Audit archives

---

### Excel Export

Audit results can also be exported to Excel.

Reports include:

* Device status
* Login status
* Check outcomes
* Compliance summaries

This provides an easy format for project tracking and management reporting.

---

## AI-Assisted Check Development

NetAudit integrates with Azure OpenAI services to accelerate audit check development.

Engineers can provide:

* Audit requirements
* Validation objectives
* Sample command output

The AI engine generates a NetAudit-compatible check template that can be reviewed and customized.

Benefits include:

* Faster check creation
* Reduced development effort
* Standardized implementation patterns
* Accelerated onboarding of new audit requirements

---

## Audit Architecture

### High-Level Structure

```text
NetAudit
├── Views
│   ├── Devices
│   └── Checks
│
├── Connectors
│   ├── Network Credentials
│   └── Jump Hosts
│
├── Fact Gatherers
│
├── Audit Engine
│   ├── Device Connectivity
│   ├── Command Execution
│   ├── Check Processing
│   └── Result Aggregation
│
└── Reporting Engine
    ├── Dashboard
    ├── Device Reports
    ├── HTML Snapshots
    └── Excel Exports
```

---

## Benefits

### Reduced Migration Risk

Identifies compliance issues before migration activities begin.

### Standardized Validation

Ensures all devices are evaluated using consistent audit criteria.

### Faster Audits

Parallel execution significantly reduces audit duration.

### Improved Governance

Provides documented evidence of audit outcomes and remediation actions.

### Enhanced Visibility

Offers centralized reporting across large device estates.

### Extensible Framework

Supports custom checks, custom fact gatherers, and future audit modules.

---

## Typical Use Cases

* Migration Readiness Assessments
* Pre-Change Validation
* Post-Change Verification
* Security Compliance Audits
* Network Standardization Programs
* Data Center Migrations
* WAN Transformation Projects
* Firewall Compliance Reviews
* Operational Health Checks
* Continuous Compliance Monitoring

---

## Future Enhancements

Potential future enhancements include:

* Scheduled Audits
* Historical Trend Analysis
* Compliance Scoring
* Risk-Based Prioritization
* Role-Based Audit Policies
* Audit Workflow Automation
* ServiceNow Integration
* Remediation Recommendations
* Multi-Vendor Compliance Libraries
* Compliance Benchmark Templates

---

## Summary

NetAudit provides an extensible framework for automated network auditing, compliance validation, and migration readiness assessment within the ATX platform. By combining reusable audit checks, dynamic fact gathering, parallel execution, AI-assisted development, and comprehensive reporting, NetAudit helps organizations perform network migrations and operational audits with greater consistency, efficiency, and confidence.
