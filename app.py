import streamlit as st
import math
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="Kafka Capacity Planner", layout="wide")

# =========================
# TITLE
# =========================
st.title("StreamArchitect")

st.markdown(
    "This tool estimates Kafka cluster sizing using a constraint-based model.\n\n"
    "It evaluates network, disk, and replication constraints to recommend broker count and infrastructure."
)

# =========================
# SESSION
# =========================
if "result" not in st.session_state:
    st.session_state.result = None

# =========================
# INPUT HELPER
# =========================
def input_with_info(label, default, help_text, key):
    col1, col2 = st.columns([4,1])
    with col1:
        val = st.number_input(label, value=default, help=help_text, key=key)
    with col2:
        with st.popover("ℹ️"):
            st.write(help_text)
    return val

# =========================
# INPUT UI
# =========================
st.divider()
#st.header("Inputs")

outer1, outer2, outer3 = st.columns([1,2,1])

with outer2:

    col_left, col_right = st.columns(2)

    # Workload
    with col_left:
        st.subheader("Workload")

        ingress = input_with_info("Ingress (MB/s)", 50.0, "Producer throughput", "ingress")
        retention = input_with_info("Retention (hrs)", 72.0, "Data retention duration", "retention")
        rf = input_with_info("Replication Factor", 3, "Number of copies of data", "rf")
        cg = input_with_info("Consumer Groups", 2, "Independent consumers", "cg")

        if rf < 3:
            st.warning("Replication factor < 3 is not recommended for production")

    # Infra
    with col_right:
        st.subheader("Infrastructure")

        nic = input_with_info("NIC (Gbps)", 10.0, "Network capacity per broker", "nic")
        disk_tb = input_with_info("Disk (TB)", 8.0, "Disk per broker", "disk_tb")
        disk_write = input_with_info("Disk Write (MB/s)", 500.0, "Disk throughput", "disk_write")
        replicas = input_with_info("Total Replicas", 3000, "Partitions × RF", "replicas")
        replicas_limit = input_with_info("Replica Limit", 4000, "Per broker limit", "replicas_limit")

    st.divider()

    colA, colB, colC = st.columns([1,1,1])
    with colB:
        calc_btn = st.button("🚀 Calculate")

# =========================
# CALCULATION
# =========================
def calculate():
    retention_sec = retention * 3600
    nic_MBps = nic * 125
    disk_MB = disk_tb * 1024 * 1024

    nic_cap = nic_MBps * 0.8
    disk_write_cap = disk_write * 0.65
    disk_cap = disk_MB * 0.65

    n1 = (ingress * rf) / nic_cap
    n2 = (ingress * (rf - 1 + cg)) / nic_cap
    n3 = (ingress * rf) / disk_write_cap
    total_storage = ingress * retention_sec * rf
    n4 = total_storage / disk_cap
    n5 = rf
    n6 = replicas / replicas_limit

    constraints = {
        "Network In": n1,
        "Network Out": n2,
        "Disk Write": n3,
        "Disk Capacity": n4,
        "RF Floor": n5,
        "Replica Limit": n6
    }

    binding = max(constraints, key=constraints.get)
    brokers = math.ceil(constraints[binding])

    ingress_per_broker = ingress / brokers

    cpu = max(4, math.ceil(ingress_per_broker / 75))
    ram = max(16, int(8 + ingress_per_broker / 50))
    disk_used = (total_storage / brokers) / (1024 * 1024)

    suggestions = {
        "Network In": "Increase NIC capacity or reduce ingress.",
        "Network Out": "Reduce consumer groups.",
        "Disk Write": "Use faster disks or add brokers.",
        "Disk Capacity": "Reduce retention or enable tiered storage.",
        "RF Floor": "Lower RF if acceptable.",
        "Replica Limit": "Reduce partitions or scale brokers."
    }

    return {
        "constraints": constraints,
        "binding": binding,
        "brokers": brokers,
        "cpu": cpu,
        "ram": ram,
        "disk": disk_used,
        "suggestion": suggestions[binding]
    }

# =========================
# PDF GENERATION
# =========================
def generate_pdf(data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    content = []

    # =========================
    # TITLE
    # =========================
    content.append(Paragraph("Kafka Capacity Planning & Architecture Report", styles["Title"]))
    content.append(Spacer(1, 10))

    # =========================
    # OVERVIEW
    # =========================
    content.append(Paragraph("<b>1. Overview</b>", styles["Heading2"]))
    content.append(Paragraph(
        "Apache Kafka is a distributed event streaming platform where system performance is governed by multiple "
        "dimensions including network throughput, disk I/O, storage capacity, and replication overhead. "
        "This assessment uses a constraint-based sizing approach to determine the minimum number of brokers "
        "required to sustain the given workload reliably.",
        styles["Normal"]
    ))
    content.append(Spacer(1, 10))

    # =========================
    # WORKLOAD INTERPRETATION
    # =========================
    content.append(Paragraph("<b>2. Workload Interpretation</b>", styles["Heading2"]))
    content.append(Paragraph(
        "The workload is characterized by producer ingress rate, data retention period, replication factor, "
        "and number of consumer groups. Higher ingress increases both network and disk pressure, while retention "
        "directly impacts storage requirements. Consumer groups introduce read amplification, increasing outbound "
        "network traffic. Replication further multiplies the load across brokers.",
        styles["Normal"]
    ))
    content.append(Spacer(1, 10))

    # =========================
    # CONSTRAINT EXPLANATION
    # =========================
    content.append(Paragraph("<b>3. Constraint-Based Analysis</b>", styles["Heading2"]))
    content.append(Paragraph(
        "Kafka cluster sizing is determined by evaluating key constraints:\n"
        "- Network Ingress: ability to absorb producer traffic and replication inflow\n"
        "- Network Egress: ability to serve consumers and replication outflow\n"
        "- Disk Throughput: sustained write capacity for incoming data\n"
        "- Disk Capacity: ability to store retained data\n"
        "- Replication Requirements: minimum brokers required for redundancy\n"
        "- Replica Distribution: limits based on partition scaling\n"
        "Each constraint is evaluated independently, and the maximum requirement determines the final broker count.",
        styles["Normal"]
    ))
    content.append(Spacer(1, 10))

    # =========================
    # TABLE
    # =========================
    table_data = [["Constraint", "Required Brokers"]]
    for k, v in data["constraints"].items():
        table_data.append([k, f"{v:.2f}"])

    table = Table(table_data)
    table.setStyle([
        ("GRID",(0,0),(-1,-1),0.5,colors.black),
        ("BACKGROUND",(0,0),(-1,0),colors.grey),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white)
    ])

    content.append(table)
    content.append(Spacer(1, 10))

    # =========================
    # RECOMMENDATION
    # =========================
    content.append(Paragraph("<b>4. Cluster Recommendation</b>", styles["Heading2"]))
    content.append(Paragraph(
        f"Based on the evaluated constraints, the Kafka cluster requires <b>{data['brokers']} brokers</b>. "
        f"The sizing is primarily driven by the <b>{data['binding']}</b> constraint, which represents the "
        f"dominant bottleneck under the current workload conditions. Other constraints are satisfied within "
        f"acceptable utilization thresholds.",
        styles["Normal"]
    ))
    content.append(Spacer(1, 10))

    # =========================
    # INFRA
    # =========================
    content.append(Paragraph("<b>5. Infrastructure Recommendation</b>", styles["Heading2"]))
    content.append(Paragraph(
        f"Each broker should be provisioned with approximately <b>{data['cpu']} vCPU</b>, "
        f"<b>{data['ram']} GB RAM</b>, and <b>{data['disk']:.2f} TB disk</b>. "
        "SSD-based storage is recommended to sustain high write throughput, and sufficient memory should be "
        "allocated to leverage OS page cache for efficient read performance.",
        styles["Normal"]
    ))
    content.append(Spacer(1, 10))

    # =========================
    # FUTURE
    # =========================
    content.append(Paragraph("<b>6. Future Scaling Considerations</b>", styles["Heading2"]))
    content.append(Paragraph(
        "Kafka workloads typically grow over time. Increases in data ingestion, additional consumer applications, "
        "and longer retention periods will significantly impact cluster load. It is recommended to monitor key "
        "metrics such as network utilization, disk I/O, and partition distribution. Horizontal scaling by adding "
        "brokers should be planned proactively to maintain performance and avoid bottlenecks.",
        styles["Normal"]
    ))
    content.append(Spacer(1, 10))

    # =========================
    # RISKS
    # =========================
    content.append(Paragraph("<b>7. Assumptions & Risks</b>", styles["Heading2"]))
    content.append(Paragraph(
        "This sizing assumes uniform partition distribution and steady workload patterns. In real-world scenarios, "
        "traffic bursts, uneven leader distribution, and consumer spikes can introduce localized bottlenecks. "
        "It is recommended to maintain operational headroom and continuously monitor cluster health.",
        styles["Normal"]
    ))
    content.append(Spacer(1, 10))

    # =========================
    # OPTIMIZATION
    # =========================
    content.append(Paragraph("<b>8. Optimization Guidance</b>", styles["Heading2"]))
    content.append(Paragraph(
        data["suggestion"],
        styles["Normal"]
    ))

    doc.build(content)
    buffer.seek(0)
    return buffer

# =========================
# RESULTS
# =========================
if calc_btn:
    st.session_state.result = calculate()

if st.session_state.result:

    r = st.session_state.result

    st.divider()
    st.header("Results")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Constraints")
        for k, v in r["constraints"].items():
            st.write(f"{k}: {v:.2f}")

    with col2:
        st.subheader("Recommendation")
        st.success(f"{r['brokers']} Brokers Required")
        st.warning(f"Binding Constraint: {r['binding']}")

        st.write(f"CPU: {r['cpu']} vCPU")
        st.write(f"RAM: {r['ram']} GB")
        st.write(f"Disk: {r['disk']:.2f} TB")

    st.divider()

    pdf = generate_pdf(r)

    st.download_button(
        "📄 Download Report",
        data=pdf,
        file_name="Kafka_Report.pdf",
        mime="application/pdf"
    )
