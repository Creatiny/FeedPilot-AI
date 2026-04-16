---
name: quote-generation
version: 1.7.0
description: Generate quotes for feed formulas with profit margin. North American customers - all responses in English.
triggers:
  - quote for
  - generate quote
  - quote customer
  - give quote
  - price quote
  - offer price
---

# Quote Generation Skill

Generate quotes for feed formulas with profit margin for North American customers.

## Capabilities

- Generate quotes for specific formulas and customers
- Support custom profit margins
- Include full ingredient breakdown
- Track price sources (public/private)
- Quote valid for 30 days

## Usage

### Generate Quote
Input: "quote for [Formula] to [Customer]"
Example: "quote for Nursery Diet 1 to Smith Farm"
Example: "quote for Grower Diet with 10% margin to Smith Farm"

### With Margin
Input: "quote for [Formula] to [Customer] with [X]% margin"
Example: "quote for Finisher Diet to Johnson Ranch with 15% margin"

### Parameters
- formula_name: Name of the feed formula
- customer_name: Name of the customer
- margin_percent: Optional profit margin (default: 0%)

## Response Format

Returns a complete quote including:
- Quote number and date
- Customer information
- Formula details
- Base cost per ton
- Margin amount and percentage
- Final quote price per ton
- Full ingredient breakdown
- Price source tracking
- 30-day validity note

## Example Conversation

User: "Quote for Nursery Diet 1 to Smith Farm with 10% margin"
Agent: "Quote #Q-20260416-001 generated for Smith Farm..."

## Error Handling

- Formula not found: "I couldn't find formula '[name]'"
- Customer not found: "I couldn't find customer '[name]'" (quote still generated)
- Invalid margin: "Margin must be between 0 and 100%"
