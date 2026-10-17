"""AI-specific model extensions for Kyro (P2 ownership).

P1 provides core models in models/:
- hospital.py (hospitals, users, hospital_systems)
- requirements.py (requirement_catalogue, hospital_requirements)
- vendor.py (vendors, products)
- document.py (documents, document_chunks)
- investigation.py (investigations, agent_runs, timeline_events, steering_commands)
- evidence.py (evidence, findings, finding_evidence, debate_messages)
- scoring.py (dimension_scores, integration_checks, integration_blueprints)
- reports.py (reports, reviews)
- monitoring.py (monitoring_watches, alerts)
- audit.py (audit_log)

Per Bible convention, P2 may add models in models/ai_*.py only.
"""

# Placeholder ready for P2 specific model extensions (e.g., prompt injection detection logs or agent checkpoints)
