# Architecture & Tooling Plan: Adaptive Intelligence (Project 2)

## 1. Core Framework: LangGraph
To establish the "fixed-strategy" baselines and later build the "adaptation mechanism," we need a framework that treats agent workflows as state graphs. 
* **Why LangGraph:** Unlike standard LangChain or AutoGen, LangGraph allows us to explicitly define cyclical graphs (perfect for reflection, retries, and backtracking). This makes the agent's strategy an explicit, modifiable graph rather than just hidden prompt logic.

## 2. Strategy Representation (Schema)
The agent's strategy will be represented as a configurable JSON/Pydantic object.
* **Parameters:** `max_retries`, `planning_depth`, `tools_allowed`, `verification_required` (boolean).
* **Adaptation:** When the agent fails, the first-order adaptation loop will mutate this JSON object for the next run (e.g., flipping `verification_required` to `true`).

## 3. Evaluation Benchmarks
To prove the adaptation works on long-horizon tasks, we need environments where mistakes happen and trajectories matter.
* **SWE-bench Lite:** For software engineering tasks.
* **WebArena:** For web navigation and reasoning tasks.
Both environments provide clear success/failure signals and require complex tool use, making them perfect for testing strategy adaptation.

## 4. Tracking & Telemetry: MLflow / LangSmith
Since the core research question asks *which* specific strategy changes account for the gains, we need rigorous tracking.
* **MLflow:** We will log each agent's strategy configuration (as hyperparameters) and its success rate/cost (as metrics) across episodes. 
* **LangSmith:** To trace the exact sequence of tool calls and identify where the unadapted agent made its critical error.
