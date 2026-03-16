#!/usr/bin/env python3
"""
Airtable Cleanup for NTWF Workflow Ontology - Role-Agent Separation Demo

4-Table Schema (simplified from Jessica Talisman's article):
  - Workflows: Title, Description, Created, Modified, Identifier
  - WorkflowSteps: Label, SequencePosition, RequiresHumanApproval, IsStepOf, AssignedRole
  - Roles: Label, Comment, FilledBy
  - HumanAgents: Name, Mbox

Article Reference: Jessica Talisman "Ontology Parts 1-3"
  - Production Deployment Workflow with 3 steps
  - Role-Agent separation demonstration
  - Key demo: Change FilledBy on Release Manager from Maria to James - zero steps change

Usage:
  python cleanup-airtable.py           # Dry run
  python cleanup-airtable.py --execute # Apply changes
"""

import os
import sys
import time
import argparse
import requests
from dotenv import load_dotenv

load_dotenv()

parser = argparse.ArgumentParser()
parser.add_argument("--execute", action="store_true")
args = parser.parse_args()

DRY_RUN = not args.execute

# 4-table Airtable base
BASE_ID = "app6afUqa0zBTiMzM"
API_KEY = os.getenv("AIRTABLE_API_KEY")

if not API_KEY:
    print("ERROR: AIRTABLE_API_KEY not found")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
BASE_URL = f"https://api.airtable.com/v0/{BASE_ID}"

def rate_limit():
    time.sleep(0.25)

def get_all_records(table):
    records = []
    offset = None
    while True:
        url = f"{BASE_URL}/{table}"
        params = {"offset": offset} if offset else {}
        try:
            resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
        except requests.exceptions.Timeout:
            print(f"  TIMEOUT - retrying...")
            time.sleep(2)
            resp = requests.get(url, headers=HEADERS, params=params, timeout=60)
        rate_limit()
        if resp.status_code != 200:
            print(f"  ERROR: {resp.status_code}")
            return []
        data = resp.json()
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    return records

def delete_records(table, record_ids):
    if DRY_RUN:
        print(f"  [DRY RUN] Would delete {len(record_ids)} records")
        return
    for i in range(0, len(record_ids), 10):
        batch = record_ids[i:i+10]
        params = {"records[]": batch}
        resp = requests.delete(f"{BASE_URL}/{table}", headers=HEADERS, params=params, timeout=30)
        rate_limit()
        if resp.status_code == 200:
            print(f"  Deleted {len(batch)} records")
        else:
            print(f"  ERROR: {resp.status_code} - {resp.text}")

def create_records(table, records):
    if DRY_RUN:
        print(f"  [DRY RUN] Would create {len(records)} records")
        return []
    created_ids = []
    for i in range(0, len(records), 10):
        batch = records[i:i+10]
        payload = {"records": [{"fields": r} for r in batch]}
        resp = requests.post(f"{BASE_URL}/{table}", headers=HEADERS, json=payload, timeout=30)
        rate_limit()
        if resp.status_code == 200:
            for rec in resp.json().get("records", []):
                created_ids.append(rec["id"])
            print(f"  Created {len(batch)} records")
        else:
            print(f"  ERROR: {resp.status_code} - {resp.text}")
    return created_ids

def update_record(table, record_id, fields):
    if DRY_RUN:
        return True
    resp = requests.patch(f"{BASE_URL}/{table}/{record_id}", headers=HEADERS, json={"fields": fields}, timeout=30)
    rate_limit()
    return resp.status_code == 200

# ============================================================================
# ARTICLE-BACKED DATA (Jessica Talisman Ontology Parts 1-3)
# ============================================================================

# From article Part III: "ss:agent-maria-gonzalez and ss:agent-james-okafor
# are ntwf:HumanAgent individuals carrying foaf:name and foaf:mbox"
HUMAN_AGENTS = [
    {
        "Name": "Maria Gonzalez",
        "Mbox": "maria.gonzalez@specialsolutions.example"
    },
    {
        "Name": "James Okafor",
        "Mbox": "james.okafor@specialsolutions.example"
    }
]

# From article - roles in the Production Deployment workflow
# Only the human-fillable roles for this simplified schema
ROLES = [
    {
        "Label": "Release Manager",
        "Comment": "Primary role responsible for coordinating production releases. First in delegation chain. Article CQ2: 'filled by Maria Gonzalez'"
    },
    {
        "Label": "Legal Compliance Reviewer",
        "Comment": "Role responsible for legal and compliance review of releases."
    },
    {
        "Label": "Risk Analyst",
        "Comment": "Role responsible for risk assessment. In full ontology, filled by AI agent."
    }
]

# From article - Production Deployment Workflow with 3 key steps
# Simplified from 5 steps to demonstrate role-agent separation
WORKFLOW_STEPS = [
    {
        "Label": "Risk Assessment",
        "SequencePosition": 1,
        "RequiresHumanApproval": False
    },
    {
        "Label": "Legal Review",
        "SequencePosition": 2,
        "RequiresHumanApproval": True
    },
    {
        "Label": "Release Approval",
        "SequencePosition": 3,
        "RequiresHumanApproval": True
    }
]

# From article - the Production Deployment Workflow
WORKFLOWS = [
    {
        "Title": "Production Deployment Workflow",
        "Description": "End-to-end workflow for deploying software releases to production, including risk analysis, legal clearance, and release approval. From Jessica Talisman's NTWF ontology article.",
        "Created": "2026-01-15",
        "Modified": "2026-01-15",
        "Identifier": "WF-PROD-001"
    }
]

def main():
    print("=" * 60)
    print("NTWF Workflow Ontology - Role-Agent Separation Demo")
    print("=" * 60)
    print(f"Base: {BASE_ID}")
    if DRY_RUN:
        print("\n*** DRY RUN - No changes ***\n")

    # Phase 1: Delete all garbage
    print("\nPHASE 1: Deleting existing records")
    print("-" * 40)

    for table in ["WorkflowSteps", "Workflows", "Roles", "HumanAgents"]:
        print(f"\n{table}:")
        records = get_all_records(table)
        if records:
            delete_records(table, [r["id"] for r in records])
        else:
            print("  (empty)")

    # Phase 2: Create article-backed data
    print("\n\nPHASE 2: Creating article-backed data")
    print("-" * 40)

    # Create in order: HumanAgents -> Roles -> Workflows -> WorkflowSteps
    print("\nHumanAgents:")
    agent_ids = create_records("HumanAgents", HUMAN_AGENTS)

    print("\nRoles:")
    role_ids = create_records("Roles", ROLES)

    print("\nWorkflows:")
    workflow_ids = create_records("Workflows", WORKFLOWS)

    print("\nWorkflowSteps:")
    step_ids = create_records("WorkflowSteps", WORKFLOW_STEPS)

    if DRY_RUN:
        print("\n\nPHASE 3: Would set up relationships")
        print("-" * 40)
        print("  - Link steps to workflow")
        print("  - Assign roles to steps")
        print("  - Assign Maria Gonzalez to Release Manager role")
    else:
        print("\n\nPHASE 3: Setting up relationships")
        print("-" * 40)

        # Get fresh records to find IDs by name
        agents = {r["fields"]["Name"]: r["id"] for r in get_all_records("HumanAgents")}
        roles = {r["fields"]["Label"]: r["id"] for r in get_all_records("Roles")}
        workflows = get_all_records("Workflows")
        steps = {r["fields"]["Label"]: r["id"] for r in get_all_records("WorkflowSteps")}

        workflow_id = workflows[0]["id"] if workflows else None

        # Link steps to workflow
        print("\n1. Linking steps to workflow...")
        for step_id in steps.values():
            update_record("WorkflowSteps", step_id, {"IsStepOf": [workflow_id]})
        print("  Done")

        # Assign roles to steps
        print("\n2. Assigning roles to steps...")
        if "Risk Assessment" in steps and "Risk Analyst" in roles:
            update_record("WorkflowSteps", steps["Risk Assessment"], {"AssignedRole": [roles["Risk Analyst"]]})
        if "Legal Review" in steps and "Legal Compliance Reviewer" in roles:
            update_record("WorkflowSteps", steps["Legal Review"], {"AssignedRole": [roles["Legal Compliance Reviewer"]]})
        if "Release Approval" in steps and "Release Manager" in roles:
            update_record("WorkflowSteps", steps["Release Approval"], {"AssignedRole": [roles["Release Manager"]]})
        print("  Done")

        # Assign Maria Gonzalez to Release Manager (the key article example)
        print("\n3. Assigning Maria Gonzalez to Release Manager role...")
        if "Release Manager" in roles and "Maria Gonzalez" in agents:
            update_record("Roles", roles["Release Manager"], {"FilledBy": [agents["Maria Gonzalez"]]})
        print("  Done")

    print("\n" + "=" * 60)
    if DRY_RUN:
        print("DRY RUN COMPLETE")
        print("\nRun with --execute to apply changes")
    else:
        print("CLEANUP COMPLETE!")

    print("\nArticle-backed data summary:")
    print("  - 1 Workflow: Production Deployment Workflow")
    print("  - 3 WorkflowSteps: Risk Assessment, Legal Review, Release Approval")
    print("  - 3 Roles: Release Manager, Legal Compliance Reviewer, Risk Analyst")
    print("  - 2 HumanAgents: Maria Gonzalez, James Okafor")
    print("\nDemo: Change FilledBy on Release Manager from Maria to James")
    print("      -> Zero steps change. That's role-agent separation!")
    print("=" * 60)

if __name__ == "__main__":
    main()
