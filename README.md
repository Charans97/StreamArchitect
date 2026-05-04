# StreamArchitect: Kafka Capacity Planner

## Overview

StreamArchitect - Kafka Capacity Planner is a constraint-driven sizing tool designed to estimate the required Kafka cluster infrastructure based on workload characteristics.

The tool evaluates multiple system dimensions—including network throughput, disk performance, storage capacity, and replication overhead—to determine the minimum number of brokers required for stable and scalable operation.

In addition to broker sizing, it provides infrastructure recommendations (CPU, RAM, disk) and generates a structured PDF report with architectural justification and future scaling considerations.

---

## Key Features

* Constraint-based Kafka cluster sizing (network, disk, replication)
* Identification of the **binding constraint** driving cluster size
* Infrastructure sizing per broker (CPU, RAM, disk)
* Clean, interactive UI built using Streamlit
* One-click generation of **client-ready PDF report**
* Built-in engineering explanations and optimization guidance

---

## Prerequisites

### System Requirements

* Python 3.8 or higher
* Minimum 4 GB RAM (for local execution)

### Python Dependencies

Install required packages using:

```bash
pip install streamlit reportlab
```

---

## How to Run

1. Clone the repository:

```bash
git clone <your-repo-url>
cd <repo-name>
```

2. Run the application:

```bash
streamlit run app.py
```

3. Open the browser (if not auto-opened):

```
http://localhost:8501
```

---

## How It Works

The tool uses a **constraint-based sizing model** where Kafka cluster size is determined by evaluating multiple independent constraints:

* Network Ingress (producer + replication traffic)
* Network Egress (consumer + replication traffic)
* Disk Write Throughput
* Disk Storage Capacity
* Replication Factor Requirements
* Replica Distribution Limits

Each constraint produces a minimum required broker count.
The **maximum of these values becomes the final recommended cluster size**.

---

## Output

The tool provides:

### 1. Cluster Recommendation

* Required number of Kafka brokers
* Binding constraint (primary limiting factor)

### 2. Infrastructure Sizing

* CPU (vCPU per broker)
* RAM (GB per broker)
* Disk capacity per broker

### 3. PDF Report

A downloadable report including:

* Architectural overview
* Constraint analysis
* Sizing justification
* Infrastructure recommendation
* Future scaling considerations
* Assumptions and risks

---

## Use Cases

* Kafka cluster planning for new deployments
* Capacity estimation for existing workloads
* Architecture discussions and client presentations
* Infrastructure justification (VM sizing, scaling decisions)

---

## Limitations

* Assumes uniform partition distribution
* Assumes steady workload (no burst modeling)
* Does not account for advanced workloads (e.g., Kafka Streams, ksqlDB)
* Cloud-specific pricing and instance mapping not included

---

## Future Enhancements

* Multi-topic workload modeling
* Cost estimation (Azure / AWS / Confluent Cloud)
* Dedicated vs Standard cluster recommendation
* Partition-level sizing and parallelism modeling
* Integration with deployment pipelines

---

## License

This project is intended for internal use and architectural evaluation. Customize as needed for production deployment.

---
