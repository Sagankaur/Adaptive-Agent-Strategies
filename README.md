# Adaptive Intelligence: Self-Adapting Problem-Solving Strategies for AI Agents

This repository contains the implementation for **Project 2**. The goal is to investigate whether AI agents can learn from their own task history to improve their problem-solving procedures (planning, tool use, verification) on future tasks, without altering the underlying foundation model.

## Directory Structure
* `/baselines` - Implementations of fixed-strategy agents (ReAct, best-of-N, Reflexion).
* `/strategy_schema` - Pydantic models and configurations representing the versioned agent strategies.
* `/adaptation_engine` - The first-order and second-order loops for diagnosing failures and mutating strategies.
* `/evaluation` - Integration with benchmarks (e.g., SWE-bench Lite, WebArena) and scoring scripts.

## Tech Stack
* **Agent Orchestration:** LangGraph
* **Tracking & Logging:** MLflow / LangSmith
* **Evaluation Benchmarks:** SWE-bench / WebArena
