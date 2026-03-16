Yes. If you want the base to match the **worked sample data in the article**, then it should be pared down very aggressively.

The key rule is:

* keep the **single fully worked ABox example** from the article
* remove the generic demo/business-process filler that is only in the Airtable export

The article is explicit that the worked sample data is the **Production Deployment Workflow** at Special Solutions, and that this one workflow exercises the model with **five steps, three agent types, six roles, five artifacts, one dataset, and one approval gate**. 
Your current rulebook instead contains **15 unrelated sample workflows** like Employee Onboarding, Invoice Approval, Content Publishing, Contract Review, Asset Management, Recruitment, and Change Management. 

## Sample data that should be included

This is the sample data the article actually supports.

### 1. Workflow

Keep:

* **Production Deployment Workflow**
  The article explicitly names `ss:workflow-production-deployment` / “Production Deployment Workflow” as the worked workflow instance. 

### 2. Workflow steps

Keep:

* **5 workflow steps total** for the Production Deployment Workflow
* one of them explicitly named as the **Release Approval Gate**
* it is explicitly **step 3** and is double-typed as both `ApprovalGate` and `WorkflowStep` in the worked example. 

What is fully supported by the visible article text:

* the workflow has **five steps**
* **step 3 = Release Approval Gate**
* the steps form an ordering chain
* the steps produce the five named artifacts below. 

What is **not fully exposed in the visible article text**:

* the exact labels of all five step names are not all spelled out in one accessible section of the uploaded article text. So those four non-gate step labels should either be pulled from the full NTWF ontology file/PDF, or temporarily rebuilt from the artifact chain later. 

### 3. Approval gate

Keep:

* **Release Approval Gate**
  The article explicitly describes one approval gate in the worked ABox, and step 3 is that gate. 

### 4. Roles

Keep the roles that are actually named or directly implied by the worked example:

Definitely supported:

* **Release Manager**
* **VP Engineering**
* **CTO**
  These are explicitly part of the delegation chain in the article. 

Also clearly supported by the worked example / competency question framing:

* **Legal Compliance Reviewer**
  This role name is explicitly used in the role discussion. 
* **Risk Analysis Agent** as a role concept
  The article explicitly uses “Risk Analysis Agent” as the example of a role distinct from the AI system filling it. 

And the article says the worked ABox has **6 roles total**. So at minimum the base should contain:

* those named roles above
* plus the remaining article-backed roles from the full NTWF instance file, not generic placeholder roles. 

### 5. Human agents

Keep:

* **Maria Gonzalez**
* **James Okafor**
  These are explicitly named as human agent individuals in the worked ABox. 

Also note:

* the article says there are **three human agent individuals** in the reasoning/validation discussion
* but in the visible uploaded text, only **Maria Gonzalez** and **James Okafor** are explicitly named. So one additional human agent exists in the worked data, but its name is not exposed in the visible excerpt you uploaded. 

### 6. AI agent

Keep:

* **RiskAnalysis-AI** / `agent-risk-ai`
* model version: **risk-classifier-v2.4.1** 

### 7. Automated pipeline

Keep:

* **CI Pipeline** / `agent-ci-pipeline` 

### 8. Dataset

Keep:

* **Q1 2026 Risk Metrics dataset** / `dataset-risk-metrics-q1-2026`
  The article explicitly says CQ8 returns this dataset and that it is processed by the RiskAnalysis-AI agent. 

### 9. Artifacts

Keep these **five artifacts exactly**, because the article explicitly names the provenance chain:

* **Risk Report**
* **Legal Clearance**
* **Release Authorization**
* **Deployment Log**
* **Post-Deployment Report** 

### 10. Departments

Keep only departments actually needed by the worked example.

Definitely supported:

* **Engineering**
* **Legal**
  The article explicitly says the worked data includes one workflow involving both Engineering and Legal, and exactly one Legal-owned step. 

Potentially others may exist in the full ABox, but from the visible article text, **Engineering** and **Legal** are the only departments you can justify with confidence for the sample instance set. 

### 11. Workflow metadata

Keep metadata fields and article-backed values for the worked workflow:

* **Title** = Production Deployment Workflow
* **Modified** = 2026-01-15
* **Identifier** = present in the worked example, though the visible text does not expose the exact identifier value
* **Description**
* **Created** 

---

## All items that are not mentioned as worked sample data and should be removed

This is the strict cleanup list based on the article’s **worked ABox sample**, not on every background/example phrase in the essays.

## Remove these workflows

All current workflow records should be removed, because none of them is the article’s worked workflow:

* Employee Onboarding
* Invoice Approval Workflow
* Content Publishing Process
* Leave Request Workflow
* IT Support Ticketing
* Expense Reimbursement Process
* Annual Performance Review
* Procurement Workflow
* Customer Feedback Collection
* Project Kickoff Process
* Contract Review Workflow
* Asset Management Process
* Recruitment Workflow
* Incident Reporting Process
* Change Management Workflow 

Reason: the article’s worked ABox is **Production Deployment Workflow**, and that workflow is not present in the current base.

## Remove these workflow steps

All current step records should be removed, because they are generic filler and not the article’s worked production-deployment steps:

* submit-request
* manager-review
* automated-eligibility-check
* finance-approval
* document-verification
* quality-assurance-review
* system-notification-sent
* final-approval
* archive-request
* customer-feedback-collection
* legal-compliance-check
* assign-task-to-team
* some-new-task
* team-lead-review
* generate-report
* close-workflow 

## Remove these approval records

All current approval records should be removed and replaced by the article-backed approval gate structure:

* initial-review
* manager-approval
* compliance-check
* final-authorization
* executive-sign-off
* quality-assurance
* legal-review
* finance-approval
* it-security-gate
* customer-confirmation 

## Remove these role records

All current generic role records should be removed, because they do not match the article’s worked sample roles:

* administrator
* editor
* viewer
* moderator
* contributor
* manager
* support
* analyst
* developer
* tester
* hr
* finance
* guest
* trainer
* owner 

These should be replaced with the specific article-backed roles such as Release Manager, VP Engineering, CTO, Legal Compliance Reviewer, and the rest of the worked six-role set.

## Remove these department records

If you are cleaning to the worked sample only, remove the current generic department set:

* human-resources
* finance
* information-technology
* marketing
* sales
* customer-service
* research-and-development
* legal
* procurement
* operations
* administration
* public-relations
* quality-assurance
* facilities-management
* training-and-development 

Why remove even `legal`? Because the current department table is part of the generic filler dataset, not the article’s worked ABox. In practice, you would **recreate** article-backed departments like:

* Engineering
* Legal

rather than keeping the current filler department set as-is. 

## Remove these human agent records

All current human-agent sample records should be removed:

* Alice Johnson
* Brian Smith
* Catherine Lee
* David Kim
* Emily Chen
* Frank Miller
* Grace Park
* Henry Adams
* Isabella Martinez
* Jack Wilson
* Karen Patel
* Liam Nguyen
* Monica Rivera
* Nathan Brown
* Olivia Clark 

Replace them with the article-backed human agents:

* Maria Gonzalez
* James Okafor
* plus the third human agent individual from the full NTWF ABox. 

## Remove these AI agent records

All current AI-agent sample records should be removed:

* Ava
* Leo
* Maya
* Eli
* Zara
* Owen
* Nina
* Kai
* Sophie
* Max
* Liam
* Jade
* Mila
* Noah
* Ella 

Replace with the article-backed AI agent:

* RiskAnalysis-AI / `agent-risk-ai` 

## Remove these automated pipeline records

All current automated pipeline records should be removed:

* lead-notification-pipeline
* e-commerce-order-sync
* issue-tracking-bridge
* newsletter-signup-sync
* support-ticket-automation
* devops-integration
* finance-automation
* project-intake-pipeline
* crm-data-sync
* calendar-integration
* survey-data-pipeline
* task-management-sync
* cloud-storage-sync
* email-notification-pipeline
* survey-data-export 

Replace with the article-backed pipeline:

* CI Pipeline / `agent-ci-pipeline` 

## Remove the current PrecedesSteps sample rows

These are generic helper rows and do not represent the article’s worked five-step production deployment sequence:

* step-1 through step-15
* assign-task-to-team (as a precedence helper row) 

They should be replaced with precedence data for the **five production deployment steps only**. 

---

## Bottom line

If you want the base to reflect the article faithfully, then the sample data should be reduced to:

* **1 workflow**: Production Deployment Workflow
* **5 steps**
* **1 approval gate**: Release Approval Gate
* **6 roles**
* **3 agent types**
* **3 human-agent individuals total**
* **1 AI agent**: RiskAnalysis-AI
* **1 automated pipeline**: CI Pipeline
* **1 dataset**: Q1 2026 Risk Metrics
* **5 artifacts**: Risk Report, Legal Clearance, Release Authorization, Deployment Log, Post-Deployment Report
* **article-backed departments**, especially Engineering and Legal. 

Everything else in the current Airtable export is generic sample filler and should be removed if your goal is “sample data based on the article.” 

The one place I need to be careful is this: the uploaded article text clearly gives the **counts** and many of the **names**, but not every single remaining role/step/human-agent label is visible in the accessible text. So I can give you a **strict keep/remove list now**, but to reconstruct the last few missing names exactly, you’d want the full NTWF ontology PDF/TTL that the article references. 

I can turn this into a **table-by-table delete/keep checklist for Omni** in the next message.
