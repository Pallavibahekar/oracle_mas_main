# Oracle MAS - Multi-Agent System

A sophisticated **Multi-Agent System (MAS)** with agent-to-agent (A2A) communication enabling collaborative swarms with extensible data source integration. Built with Python, Oracle MAS demonstrates expertise in distributed systems, modular architecture design, and autonomous agent coordination.

## 🎯 Overview

Oracle MAS is a framework for building intelligent, collaborative multi-agent systems where agents can:
- **Communicate autonomously** with other agents in real-time
- **Collaborate** on complex tasks through coordinated swarms
- **Integrate seamlessly** with multiple data sources
- **Scale efficiently** with modular, distributed architecture
- **Adapt dynamically** to changing requirements and environments

## ✨ Key Features

### 🤝 Agent-to-Agent Communication
- Direct peer-to-peer messaging between agents
- Asynchronous event-driven architecture
- Message routing and protocol handling
- Request-response and publish-subscribe patterns

### 👥 Collaborative Swarms
- Coordinated multi-agent workflows
- Task delegation and load balancing
- Consensus mechanisms for distributed decision-making
- Hierarchical and flat agent topologies

### 🔌 Extensible Data Integration
- Support for multiple data sources (APIs, databases, files, streams)
- Pluggable data adapters and connectors
- Real-time data synchronization
- Flexible query and aggregation capabilities

### 🏗️ Modular Architecture
- Clean separation of concerns
- Reusable agent components and modules
- Configuration-driven setup
- Plugin-based extensibility

### 📊 Advanced Capabilities
- State management and persistence
- Monitoring and observability
- Error handling and recovery
- Performance optimization

## 🛠️ Technology Stack

- **Language**: Python 3.8+
- **Async Framework**: AsyncIO / aiohttp
- **Distributed Systems**: Message queues, event buses
- **Data Integration**: SQL, NoSQL, REST APIs
- **Jupyter Notebooks**: Interactive development and visualization (69.4% of repo)
- **Python Scripts**: Core system implementation (30.6% of repo)

## 📦 Project Structure

```
oracle_mas/
├── README.md                 # Project documentation
├── .gitignore               # Git ignore rules
├── agents/                  # Agent implementations
│   ├── base.py             # Base agent class
│   ├── coordinator.py      # Coordinator agent
│   └── worker.py           # Worker agents
├── communication/          # A2A communication module
│   ├── message.py         # Message definitions
│   ├── protocol.py        # Communication protocols
│   └── router.py          # Message routing
├── data/                  # Data integration layer
│   ├── adapters/         # Data source adapters
│   ├── connectors/       # Connection managers
│   └── schema.py         # Data schema definitions
├── swarm/                # Collaborative swarm module
│   ├── coordinator.py    # Swarm coordination
│   ├── tasks.py         # Task definitions
│   └── consensus.py     # Consensus mechanisms
├── notebooks/           # Jupyter notebooks for demos
│   ├── example_*.ipynb  # Usage examples
│   └── demo_*.ipynb     # System demonstrations
├── tests/              # Unit and integration tests
├── config/            # Configuration files
├── requirements.txt   # Python dependencies
└── utils/            # Utility functions
```

## 🚀 Quick Start

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Pallavibahekar/oracle_mas.git
   cd oracle_mas
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Basic Usage

```python
from oracle_mas.agents import Agent
from oracle_mas.swarm import Swarm

# Create agents
agent1 = Agent(name="Worker1", role="processor")
agent2 = Agent(name="Worker2", role="processor")
coordinator = Agent(name="Coordinator", role="coordinator")

# Form a swarm
swarm = Swarm([agent1, agent2, coordinator])

# Execute collaborative task
result = swarm.execute_task(task_definition)
print(result)
```

### Running Examples

Explore Jupyter notebooks for interactive examples:

```bash
jupyter notebook notebooks/
```

## 📚 Documentation

### Agent Communication

Agents communicate through a message-passing protocol:

```python
# Send message
await agent.send_message(
    recipient="target_agent",
    message_type="query",
    payload={"data": "request"}
)

# Receive and handle messages
@agent.on_message("query")
async def handle_query(message):
    return await process_query(message.payload)
```

### Data Integration

Connect multiple data sources:

```python
from oracle_mas.data import DataAdapter

# Register data sources
adapter = DataAdapter()
adapter.register_source("database", db_connector)
adapter.register_source("api", api_connector)

# Query aggregated data
data = await adapter.query("SELECT * FROM ...")
```

### Swarm Coordination

Orchestrate complex multi-agent workflows:

```python
from oracle_mas.swarm import Swarm

swarm = Swarm(agents=[agent1, agent2, agent3])
results = await swarm.execute_workflow(
    workflow_config,
    consensus_required=True
)
```

## 🔧 Configuration

Configure system behavior through `config/` files:

```yaml
# config/agents.yaml
agents:
  - name: Worker1
    role: processor
    max_concurrent_tasks: 5
    
  - name: Coordinator
    role: coordinator
    decision_timeout: 30s

# config/communication.yaml
communication:
  protocol: "event_driven"
  message_queue: "redis"
  timeout: 10s
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=oracle_mas tests/

# Run specific test file
pytest tests/test_agents.py -v
```

## 📊 Features in Detail

### Distributed Agent Coordination
- Fault-tolerant agent orchestration
- Service discovery and registration
- Load balancing across agents
- Health monitoring and auto-recovery

### Scalable Communication
- High-throughput message passing
- Low-latency inter-agent communication
- Support for millions of concurrent messages
- Message prioritization and queuing

### Extensible Data Layer
- Plugin architecture for custom adapters
- Support for heterogeneous data sources
- Data transformation and normalization
- Caching and query optimization

## 🎓 Use Cases

- **Distributed Task Processing**: Parallelize complex computations across agent swarms
- **Real-time Data Aggregation**: Collect and correlate data from multiple sources
- **Autonomous Decision Systems**: Enable agents to make collaborative decisions
- **Monitoring & Analytics**: Build observability systems with intelligent agents
- **IoT Coordination**: Orchestrate distributed IoT devices as collaborative agents

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and commit (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📬 Contact & Support

For questions, issues, or suggestions:
- **GitHub Issues**: [Report issues](https://github.com/Pallavibahekar/oracle_mas/issues)
- **Discussions**: [Start a discussion](https://github.com/Pallavibahekar/oracle_mas/discussions)

## 🙏 Acknowledgments

Built with expertise in:
- Distributed systems and agent architectures
- Modular design patterns
- Autonomous agent coordination
- Collaborative swarm intelligence

## 📖 Additional Resources

- [Distributed Systems Concepts](https://en.wikipedia.org/wiki/Distributed_computing)
- [Multi-Agent Systems](https://en.wikipedia.org/wiki/Multi-agent_system)
- [Agent Communication Protocols](https://en.wikipedia.org/wiki/Agent_communication_language)
- [Swarm Intelligence](https://en.wikipedia.org/wiki/Swarm_intelligence)

---

**Built with ❤️ for collaborative intelligence**

⭐ If you find this project useful, consider giving it a star!
