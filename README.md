# Inteligência Comercial — SESI + SENAI + SEBRAE

> Commercial intelligence platform that transforms company, CNAE and relationship data into market coverage, cross-sell and opportunity analysis.

**Portfolio focus:** Data Engineering · Market Intelligence · Commercial Analytics · Segmentation · Cross-sell · Decision Support

## Business Problem

Commercial teams need more than a list of companies. They need to understand:

- who belongs to the addressable market;
- which companies already have a relationship;
- where market penetration is low;
- which organizations may have cross-sell potential;
- how industrial classification and business rules affect the opportunity universe.

## Solution

The repository contains a data pipeline and Streamlit dashboard for constructing and analyzing a commercial master base across **SESI, SENAI and SEBRAE**.

`Raw / Reference Data → Standardization → CNPJ / CNAE Classification → Relationship Matching → Commercial Rules → Opportunity Base → Dashboard`

## Main Capabilities

- CNPJ normalization;
- industrial classification by CNAE;
- relationship flags for SESI/SENAI;
- SEBRAE eligibility and opportunity rules;
- commercial universe construction;
- penetration analysis;
- cross-sell analysis;
- audit and correction utilities.

## Data Engineering Principle

A key design concern in the project is distinguishing:

**raw source fields → validated business flags → commercial indicators**

This prevents historical or ambiguous fields from being interpreted as current relationship status and helps keep the commercial universe auditable.

## Technology Stack

Python · Pandas · Streamlit · Excel/CSV · Business Rules · CNAE Classification · Data Quality / Audit

## Repository Structure

The repository contains data-preparation scripts, classification utilities, commercial engines and the Streamlit application.

Sensitive production datasets should not be published in a public portfolio repository. Public versions should use synthetic, anonymized or aggregated data.

## Business Value

The analytical workflow supports questions such as:

- market universe sizing;
- relationship penetration;
- regional/sector segmentation;
- cross-sell opportunity identification;
- prioritization for commercial teams.

## Limitations

Business rules depend on the source data and organizational definitions. Production use requires governed source systems, documented rule ownership, refresh processes and validation with the commercial/business teams.

## Portfolio Perspective

**Company data → classification → relationship intelligence → opportunity detection → commercial action**

This project is a practical example of how data engineering and analytics become a commercial intelligence product.