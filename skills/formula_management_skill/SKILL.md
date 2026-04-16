---
name: formula-management
version: 1.7.0
description: Create, update, delete, and list private feed formulas. North American customers - all responses in English.
triggers:
  - create my formula
  - create a formula
  - add formula
  - my formula
  - list my formulas
  - delete my formula
  - update my formula
  - modify my formula
---

# Formula Management Skill

Manage private feed formulas for North American customers.

## Capabilities

- Create private formulas with ingredients
- Update existing private formulas
- Delete private formulas
- List all private formulas
- Support ingredient codes for precise pricing

## Usage

### Create Formula
Input: "create my [formula name] formula"
Example: "create my Nursery Diet formula"
Follow-up: Provide ingredients and stages

### List Formulas
Input: "list my formulas"
Example: "show my formulas"
Example: "list all my formulas"

### Update Formula
Input: "update my [formula name] formula"
Example: "modify my Grower Diet, change corn to 30%"

### Delete Formula
Input: "delete my [formula name] formula"
Example: "remove my test formula"

## Response Format

Returns structured data with:
- Operation status
- Formula details (for list/create/update)
- Error messages for failures

## Example Conversation

User: "create my Custom Nursery formula"
Agent: "Formula 'Custom Nursery' created with 0 ingredients. Add ingredients using 'add ingredient'..."

User: "list my formulas"
Agent: "Found 3 private formulas: Custom Nursery, Test Diet 1, ..."
