"""First-order strategy adaptation: diagnose, propose an edit, accept or reject.

Only the first-order loop's interface and trivial rule-based components exist.
The second-order loop (revising the diagnoser and proposer) is not implemented.
"""

from adaptation_engine.first_order import (
    CandidateResult,
    Diagnoser,
    Diagnosis,
    DiagnosisGroup,
    FailureClass,
    Proposer,
    RoundRecord,
    RuleBasedDiagnoser,
    RuleBasedProposer,
    Score,
    aggregate,
    run_round,
)

__all__ = [
    "CandidateResult",
    "Diagnoser",
    "Diagnosis",
    "DiagnosisGroup",
    "FailureClass",
    "Proposer",
    "RoundRecord",
    "RuleBasedDiagnoser",
    "RuleBasedProposer",
    "Score",
    "aggregate",
    "run_round",
]
