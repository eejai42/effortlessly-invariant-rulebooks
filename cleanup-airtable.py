#!/usr/bin/env python3
"""
Airtable Cleanup Script for Jessica Talisman ADVANCED Ontology
Based on PLAN-to-cleanup-ADVANCED-table.md

This script:
1. Deletes all existing generic filler records
2. Creates article-backed sample data for the Production Deployment Workflow

Usage:
  python cleanup-airtable.py           # Dry run (preview changes)
  python cleanup-airtable.py --execute # Actually make changes
"""

import os
import sys
import time
import argparse
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Parse arguments
parser = argparse.ArgumentParser(description="Cleanup Airtable to article-backed sample data")
parser.add_argument("--execute", action="store_true", help="Actually execute changes (default is dry-run)")
args = parser.parse_args()

DRY_RUN = not args.execute

# Configuration
BASE_ID = "appwN9EAp8IeIxM23"
API_KEY = os.getenv("AIRTABLE_API_KEY")

if not API_KEY:
    print("ERROR: AIRTABLE_API_KEY not found in environment")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

BASE_URL = f"https://api.airtable.com/v0/{BASE_ID}"

# Rate limiting helper
def rate_limit():
    time.sleep(0.25)  # Airtable rate limit: 5 requests/sec

def get_all_records(table_name):
    """Fetch all records from a table"""
    records = []
    offset = None

    while True:
        url = f"{BASE_URL}/{table_name}"
        params = {}
        if offset:
            params["offset"] = offset

        response = requests.get(url, headers=HEADERS, params=params)
        rate_limit()

        if response.status_code != 200:
            print(f"  ERROR fetching {table_name}: {response.status_code} - {response.text}")
            return []

        data = response.json()
        records.extend(data.get("records", []))

        offset = data.get("offset")
        if not offset:
            break

    return records

def delete_records(table_name, record_ids):
    """Delete records in batches of 10 (Airtable limit)"""
    if DRY_RUN:
        print(f"  [DRY RUN] Would delete {len(record_ids)} records")
        return

    for i in range(0, len(record_ids), 10):
        batch = record_ids[i:i+10]
        url = f"{BASE_URL}/{table_name}"
        params = {"records[]": batch}

        response = requests.delete(url, headers=HEADERS, params=params)
        rate_limit()

        if response.status_code != 200:
            print(f"  ERROR deleting from {table_name}: {response.status_code} - {response.text}")
        else:
            print(f"  Deleted {len(batch)} records")

def create_records(table_name, records):
    """Create records in batches of 10 (Airtable limit)"""
    if DRY_RUN:
        print(f"  [DRY RUN] Would create {len(records)} records:")
        for r in records:
            name = r.get("Name") or r.get("DisplayName") or str(r)[:50]
            print(f"    - {name}")
        return

    for i in range(0, len(records), 10):
        batch = records[i:i+10]
        url = f"{BASE_URL}/{table_name}"
        payload = {"records": [{"fields": r} for r in batch]}

        response = requests.post(url, headers=HEADERS, json=payload)
        rate_limit()

        if response.status_code != 200:
            print(f"  ERROR creating in {table_name}: {response.status_code} - {response.text}")
        else:
            print(f"  Created {len(batch)} records")

def update_record(table_name, record_id, fields):
    """Update a single record"""
    if DRY_RUN:
        print(f"  [DRY RUN] Would update {record_id}")
        return True

    url = f"{BASE_URL}/{table_name}/{record_id}"
    payload = {"fields": fields}

    response = requests.patch(url, headers=HEADERS, json=payload)
    rate_limit()

    if response.status_code != 200:
        print(f"  ERROR updating {record_id}: {response.status_code} - {response.text}")
        return False
    return True

def find_record_id(table_name, display_name):
    """Find a record ID by DisplayName or Name"""
    records = get_all_records(table_name)
    for r in records:
        fields = r.get("fields", {})
        if fields.get("DisplayName") == display_name or fields.get("Name") == display_name:
            return r["id"]
    return None

# ============================================================================
# Article-backed sample data
# Field names match actual Airtable schema (Name is computed in some tables)
# ============================================================================

# 1. Workflows - Production Deployment Workflow
# Name is computed from DisplayName, so don't set it
WORKFLOWS = [
    {
        "DisplayName": "Production Deployment",
        "Title": "Production Deployment Workflow",
        "Description": "End-to-end workflow for deploying software releases to production, including risk analysis, legal clearance, and executive approval gates.",
        "Identifier": "ss:workflow-production-deployment",
        "Modified": "2026-01-15"
    }
]

# 2. Workflow Steps - 5 steps for Production Deployment
# Name is computed, use SequencePosition instead of StepNumber
WORKFLOW_STEPS = [
    {
        "DisplayName": "Risk Analysis",
        "SequencePosition": 1,
        "RequiresHumanApproval": False
    },
    {
        "DisplayName": "Legal Clearance",
        "SequencePosition": 2,
        "RequiresHumanApproval": True
    },
    {
        "DisplayName": "Release Approval Gate",
        "SequencePosition": 3,
        "RequiresHumanApproval": True
    },
    {
        "DisplayName": "Deployment Execution",
        "SequencePosition": 4,
        "RequiresHumanApproval": False
    },
    {
        "DisplayName": "Post-Deployment Review",
        "SequencePosition": 5,
        "RequiresHumanApproval": True
    }
]

# 3. Approvals - Release Approval Gate
# Name is computed, only has DisplayName and EscalationThresholdHours
APPROVALS = [
    {
        "DisplayName": "Release Approval Gate",
        "EscalationThresholdHours": 24
    }
]

# 4. Roles - 6 article-backed roles
# Name is computed, use DisplayName, Label, Comment
ROLES = [
    {
        "DisplayName": "Release Manager",
        "Label": "Release Manager",
        "Comment": "Primary role responsible for coordinating production releases. First in delegation chain for Release Approval Gate."
    },
    {
        "DisplayName": "VP Engineering",
        "Label": "VP Engineering",
        "Comment": "Vice President of Engineering. Second in delegation chain for Release Approval Gate."
    },
    {
        "DisplayName": "CTO",
        "Label": "CTO",
        "Comment": "Chief Technology Officer. Final authority in delegation chain for Release Approval Gate."
    },
    {
        "DisplayName": "Legal Compliance Reviewer",
        "Label": "Legal Compliance Reviewer",
        "Comment": "Role responsible for legal and compliance review of releases."
    },
    {
        "DisplayName": "Risk Analysis Agent",
        "Label": "Risk Analysis Agent",
        "Comment": "Role assigned to AI systems performing automated risk assessment."
    },
    {
        "DisplayName": "Deployment Engineer",
        "Label": "Deployment Engineer",
        "Comment": "Role responsible for executing and monitoring production deployments."
    }
]

# 5. Departments - Engineering and Legal
# Name is computed, use DisplayName and Title
DEPARTMENTS = [
    {
        "DisplayName": "Engineering",
        "Title": "Engineering department responsible for software development and deployment."
    },
    {
        "DisplayName": "Legal",
        "Title": "Legal department responsible for compliance review."
    }
]

# 6. Human Agents - Maria Gonzalez, James Okafor, plus one more
# Name is NOT computed here, Mbox for email
HUMAN_AGENTS = [
    {
        "Name": "maria-gonzalez",
        "DisplayName": "Maria Gonzalez",
        "Mbox": "mailto:maria.gonzalez@specialsolutions.example"
    },
    {
        "Name": "james-okafor",
        "DisplayName": "James Okafor",
        "Mbox": "mailto:james.okafor@specialsolutions.example"
    },
    {
        "Name": "chen-wei",
        "DisplayName": "Chen Wei",
        "Mbox": "mailto:chen.wei@specialsolutions.example"
    }
]

# 7. AI Agents - RiskAnalysis-AI
# Name is NOT computed, Title for description
AI_AGENTS = [
    {
        "Name": "risk-analysis-ai",
        "DisplayName": "RiskAnalysis-AI",
        "Title": "AI agent that processes Q1 2026 Risk Metrics dataset for automated risk assessment.",
        "ModelVersion": "risk-classifier-v2.4.1"
    }
]

# 8. Automated Pipelines - CI Pipeline
# Name is NOT computed, Description field exists
AUTOMATED_PIPELINES = [
    {
        "Name": "ci-pipeline",
        "DisplayName": "CI Pipeline",
        "Description": "Continuous Integration pipeline that executes production deployments."
    }
]

# 9. PrecedesSteps - ordering chain for 5 steps
# StepNumber is computed in Airtable, just use Name
PRECEDES_STEPS = [
    {"Name": "step-1"},
    {"Name": "step-2"},
    {"Name": "step-3"},
    {"Name": "step-4"},
    {"Name": "step-5"}
]

# Tables to process (in order for foreign key relationships)
TABLES = [
    ("PrecedesSteps", PRECEDES_STEPS),
    ("Approvals", APPROVALS),
    ("WorkflowSteps", WORKFLOW_STEPS),
    ("Workflows", WORKFLOWS),
    ("Roles", ROLES),
    ("Departments", DEPARTMENTS),
    ("HumanAgents", HUMAN_AGENTS),
    ("AIAgents", AI_AGENTS),
    ("AutomatedPipelines", AUTOMATED_PIPELINES),
]

def main():
    print("=" * 60)
    print("Airtable Cleanup for Jessica Talisman ADVANCED Ontology")
    print("=" * 60)
    print(f"Base ID: {BASE_ID}")
    if DRY_RUN:
        print()
        print("*** DRY RUN MODE - No changes will be made ***")
        print("Run with --execute to apply changes")
    print()

    # Phase 1: Delete all existing records
    print("PHASE 1: Deleting existing records")
    print("-" * 40)

    for table_name, _ in TABLES:
        print(f"\n{table_name}:")
        records = get_all_records(table_name)
        if records:
            record_ids = [r["id"] for r in records]
            print(f"  Found {len(record_ids)} records to delete")
            delete_records(table_name, record_ids)
        else:
            print("  No records found")

    print()
    print("PHASE 2: Creating article-backed sample data")
    print("-" * 40)

    # Phase 2: Create new records (reverse order for FK relationships)
    for table_name, data in reversed(TABLES):
        print(f"\n{table_name}:")
        if data:
            print(f"  Creating {len(data)} records")
            create_records(table_name, data)
        else:
            print("  No records to create")

    # Phase 3: Set up relationships
    print()
    print("PHASE 3: Setting up relationships")
    print("-" * 40)

    # Get record IDs we need
    workflow_id = find_record_id("Workflows", "Production Deployment")
    approval_id = find_record_id("Approvals", "Release Approval Gate")

    # Role IDs for delegation chain
    release_mgr_id = find_record_id("Roles", "Release Manager")
    vp_eng_id = find_record_id("Roles", "VP Engineering")
    cto_id = find_record_id("Roles", "CTO")
    legal_reviewer_id = find_record_id("Roles", "Legal Compliance Reviewer")
    risk_agent_role_id = find_record_id("Roles", "Risk Analysis Agent")
    deploy_eng_id = find_record_id("Roles", "Deployment Engineer")

    # Department IDs
    eng_dept_id = find_record_id("Departments", "Engineering")
    legal_dept_id = find_record_id("Departments", "Legal")

    # Agent IDs
    maria_id = find_record_id("HumanAgents", "Maria Gonzalez")
    james_id = find_record_id("HumanAgents", "James Okafor")
    chen_id = find_record_id("HumanAgents", "Chen Wei")
    risk_ai_id = find_record_id("AIAgents", "RiskAnalysis-AI")
    ci_pipeline_id = find_record_id("AutomatedPipelines", "CI Pipeline")

    # WorkflowStep IDs
    step_risk = find_record_id("WorkflowSteps", "Risk Analysis")
    step_legal = find_record_id("WorkflowSteps", "Legal Clearance")
    step_approval = find_record_id("WorkflowSteps", "Release Approval Gate")
    step_deploy = find_record_id("WorkflowSteps", "Deployment Execution")
    step_review = find_record_id("WorkflowSteps", "Post-Deployment Review")

    print("\n1. Linking WorkflowSteps to Workflow...")
    if workflow_id:
        for step_id in [step_risk, step_legal, step_approval, step_deploy, step_review]:
            if step_id:
                update_record("WorkflowSteps", step_id, {"Workflow": [workflow_id]})
        print("  Done")
    else:
        print("  ERROR: Could not find Workflow")

    print("\n2. Linking Release Approval Gate step to Approval...")
    if step_approval and approval_id:
        update_record("WorkflowSteps", step_approval, {"ApprovalGate": [approval_id]})
        print("  Done")
    else:
        print("  ERROR: Could not find step or approval")

    print("\n3. Setting up role delegation chain (Release Manager -> VP Eng -> CTO)...")
    if release_mgr_id and vp_eng_id:
        update_record("Roles", release_mgr_id, {"DelegatesTo": [vp_eng_id]})
    if vp_eng_id and cto_id:
        update_record("Roles", vp_eng_id, {"DelegatesTo": [cto_id]})
    print("  Done")

    print("\n4. Assigning roles to departments...")
    if eng_dept_id:
        # Engineering roles
        for role_id in [release_mgr_id, vp_eng_id, cto_id, risk_agent_role_id, deploy_eng_id]:
            if role_id:
                update_record("Roles", role_id, {"OwnedBy": [eng_dept_id]})
    if legal_dept_id and legal_reviewer_id:
        update_record("Roles", legal_reviewer_id, {"OwnedBy": [legal_dept_id]})
    print("  Done")

    print("\n5. Assigning agents to roles...")
    # Release Manager filled by Maria
    if release_mgr_id and maria_id:
        update_record("Roles", release_mgr_id, {"FilledByHumanAgent": [maria_id]})
    # VP Engineering filled by James
    if vp_eng_id and james_id:
        update_record("Roles", vp_eng_id, {"FilledByHumanAgent": [james_id]})
    # CTO filled by Chen
    if cto_id and chen_id:
        update_record("Roles", cto_id, {"FilledByHumanAgent": [chen_id]})
    # Risk Analysis Agent filled by AI
    if risk_agent_role_id and risk_ai_id:
        update_record("Roles", risk_agent_role_id, {"FilledByAIAgent": [risk_ai_id]})
    # Deployment Engineer filled by CI Pipeline
    if deploy_eng_id and ci_pipeline_id:
        update_record("Roles", deploy_eng_id, {"FilledByAutomatedPipeline": [ci_pipeline_id]})
    print("  Done")

    print("\n6. Assigning roles to workflow steps...")
    # Step 1: Risk Analysis -> Risk Analysis Agent role
    if step_risk and risk_agent_role_id:
        update_record("WorkflowSteps", step_risk, {"AssignedRole": [risk_agent_role_id]})
    # Step 2: Legal Clearance -> Legal Compliance Reviewer
    if step_legal and legal_reviewer_id:
        update_record("WorkflowSteps", step_legal, {"AssignedRole": [legal_reviewer_id]})
    # Step 3: Release Approval Gate -> Release Manager
    if step_approval and release_mgr_id:
        update_record("WorkflowSteps", step_approval, {"AssignedRole": [release_mgr_id]})
    # Step 4: Deployment Execution -> Deployment Engineer
    if step_deploy and deploy_eng_id:
        update_record("WorkflowSteps", step_deploy, {"AssignedRole": [deploy_eng_id]})
    # Step 5: Post-Deployment Review -> Release Manager
    if step_review and release_mgr_id:
        update_record("WorkflowSteps", step_review, {"AssignedRole": [release_mgr_id]})
    print("  Done")

    print("\n7. Linking PrecedesSteps to WorkflowSteps...")
    # Get PrecedesStep records
    precedes_records = get_all_records("PrecedesSteps")
    step_mapping = {
        "step-1": step_risk,
        "step-2": step_legal,
        "step-3": step_approval,
        "step-4": step_deploy,
        "step-5": step_review
    }
    for pr in precedes_records:
        name = pr.get("fields", {}).get("Name")
        if name in step_mapping and step_mapping[name]:
            update_record("PrecedesSteps", pr["id"], {"WorkflowStep": [step_mapping[name]]})
    print("  Done")

    print("\n8. Setting step ordering (PrecededBySteps links to PrecedesSteps)...")
    # PrecededBySteps links to PrecedesSteps table, not WorkflowSteps
    # Get PrecedesStep record IDs
    precedes_id_map = {}
    for pr in precedes_records:
        name = pr.get("fields", {}).get("Name")
        precedes_id_map[name] = pr["id"]

    # Step 1 (Risk Analysis) has no predecessor - clear any auto-created links
    if step_risk:
        update_record("WorkflowSteps", step_risk, {"PrecededBySteps": []})
    # Step 2 (Legal) is preceded by PrecedesStep "step-1"
    if step_legal and "step-1" in precedes_id_map:
        update_record("WorkflowSteps", step_legal, {"PrecededBySteps": [precedes_id_map["step-1"]]})
    # Step 3 (Approval) is preceded by PrecedesStep "step-2"
    if step_approval and "step-2" in precedes_id_map:
        update_record("WorkflowSteps", step_approval, {"PrecededBySteps": [precedes_id_map["step-2"]]})
    # Step 4 (Deploy) is preceded by PrecedesStep "step-3"
    if step_deploy and "step-3" in precedes_id_map:
        update_record("WorkflowSteps", step_deploy, {"PrecededBySteps": [precedes_id_map["step-3"]]})
    # Step 5 (Review) is preceded by PrecedesStep "step-4"
    if step_review and "step-4" in precedes_id_map:
        update_record("WorkflowSteps", step_review, {"PrecededBySteps": [precedes_id_map["step-4"]]})
    print("  Done")

    print()
    print("=" * 60)
    if DRY_RUN:
        print("DRY RUN COMPLETE - No changes were made")
        print()
        print("To apply these changes, run:")
        print("  python cleanup-airtable.py --execute")
    else:
        print("Cleanup complete!")
    print()
    print("Summary of article-backed sample data:")
    print("  - 1 Workflow: Production Deployment Workflow")
    print("  - 5 Workflow Steps")
    print("  - 1 Approval Gate: Release Approval Gate")
    print("  - 6 Roles")
    print("  - 2 Departments: Engineering, Legal")
    print("  - 3 Human Agents")
    print("  - 1 AI Agent: RiskAnalysis-AI")
    print("  - 1 Automated Pipeline: CI Pipeline")
    print("  - 4 PrecedesSteps (ordering chain)")
    print()
    print("NOTE: Artifacts and Datasets tables were not found in the schema.")
    print("You may need to add these tables to Airtable if required.")
    print("=" * 60)

if __name__ == "__main__":
    main()
