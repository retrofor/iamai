# Rule-Driven Comprehensive AI Toolkit

Welcome to **iamai**, a powerful AI framework designed to support multimodal machine learning and cross-platform robot development. Unlike traditional event-driven systems, **iamai** adopts a **Rule-Driven Task-Driven Flow (RDTDF)** architecture, inspired by **Prolog** and **durable_rules**. This unique approach enables developers to focus on business logic while achieving high performance and scalability.

## 🌟 Key Features

1. **Rule-Driven Architecture**:
   - Simplify complex workflows with declarative rules.
   - Dynamically adapt task execution based on input data and context.

2. **Task-Driven Flow**:
   - Focus on achieving specific objectives without worrying about underlying protocol details.
   - Centralized task scheduling ensures efficient resource management.

3. **Multimodal & Cross-Platform**:
   - Seamless integration of multiple communication platforms.
   - Unified data schema (UDS) simplifies cross-protocol compatibility.

4. **Python & Rust Integration**:
   - High flexibility with Python for logic implementation.
   - Enhanced performance using Rust for core modules.

5. **Prolog-Inspired Logic Engine**:
   - Advanced decision-making capabilities with logic-driven workflows.
   - Support for complex conditions and dynamic task chaining.

## 🚀 Getting Started

### Install iamai

```bash
pip install iamai
```

### Define Your First Task

A task in **iamai** encapsulates a specific operation:

```python
from iamai import Task

class MyTask(Task):
    def process(self, data):
        result = data.upper()  # Example: Convert input to uppercase
        self.output(result)

# Run the task
task = MyTask()
task.run("hello")  # Output: HELLO
```

### Create a Task Flow

Task flows allow you to define sequences of tasks:

```python
from iamai import Task, Flow

class TaskA(Task):
    def process(self, data):
        self.output(data + " A")

class TaskB(Task):
    def process(self, data):
        self.output(data + " B")

class MyFlow(Flow):
    def define(self):
        self.add_task(TaskA())
        self.add_task(TaskB())

# Execute the flow
flow = MyFlow()
flow.run("Start ->")  # Output: Start -> A -> B
```

### Add Rule-Driven Logic

Integrate Prolog-like rules into your workflows for dynamic decision-making:

```python
from iamai.logic import Rule, LogicalFlow

rules = [
    Rule("user_role == 'admin' -> execute(AdminTask)"),
    Rule("user_request == 'help' -> execute(HelpTask)")
]

flow = LogicalFlow(rules=rules)

# Run with context
flow.run({"user_role": "admin", "user_request": "help"})
# Output: Executes AdminTask
```

## 🛠 Advanced Features

1. **Unified Data Schema (UDS)**:
   - Normalize data across platforms like Telegram, Slack, and custom protocols.
   - Example:
     ```python
     from iamai.tools import FieldMapper

     class TelegramFieldMapper(FieldMapper):
         def to_uds(self, data):
             return {
                 "sender_id": data["from"]["id"],
                 "content": data["text"],
                 "metadata": {"platform": "telegram"}
             }
     ```

2. **Rust Acceleration**:
   - Leverage Rust for performance-critical components.
   - Example: String processing via Rust tools:
     ```python
     from iamai.tools import process_string
     processed = process_string("hello world")
     print(processed)  # Output: HELLO_WORLD
     ```

3. **Dynamic Context Management**:
   - Access shared configuration and state seamlessly.
     ```python
     flow.context.set("config_key", "MyConfig")
     flow.run("Data")  # Accesses config dynamically
     ```

4. **Monitoring & Debugging**:
   - Enable debug mode for tasks to log execution details:
     ```python
     task = MyTask(debug=True)
     task.run("Test")  # Logs detailed execution flow
     ```

## 🧩 Architecture Highlights

### 1. **Task-Driven Flow**
   - Modular and reusable task components.
   - Centralized scheduling for optimized resource usage.

### 2. **Prolog-Inspired Logic Engine**
   - Rules evaluated dynamically to guide task execution.
   - Backtracking mechanism for complex decision-making.

### 3. **Rust-Powered Core**
   - Combines Python's ease of use with Rust's performance.

## 💡 Use Cases

- **Multimodal Chatbots**: Create intelligent agents that adapt to user behavior.
- **Business Workflow Automation**: Streamline processes with logic-driven task flows.
- **Protocol-Agnostic Systems**: Develop applications that work seamlessly across multiple communication platforms.

## 🛡 Contributing

We welcome contributions to enhance **iamai**! Please refer to our [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

For detailed documentation and examples, visit our [Wiki](https://github.com/your-repo/iamai/wiki).

Let’s redefine AI automation with logic-driven simplicity! 🌟