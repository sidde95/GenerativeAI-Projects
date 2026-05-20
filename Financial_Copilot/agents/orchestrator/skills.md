# Orchestrator Agent Skills

## Purpose
Coordinate the full workflow execution, control transitions, retries, fallback handling, and final response assembly.

## Skills
1. Execution planning
2. Dependency enforcement (ingestion must pass first)
3. Retry/fallback decisioning
4. Checkpoint tracking
5. Final status consolidation

## Inputs
- Global workflow state
- Per-agent outputs
- Error/retry metadata

## Outputs
- Updated workflow state
- Final execution status
- Consolidated response envelope