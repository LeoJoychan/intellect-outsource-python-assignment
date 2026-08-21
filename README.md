# Intellect Outsource - Shopify Product Classifier

A Django application for importing products, matching them against the Shopify product taxonomy, classifying products with confidence scores, and sending uncertain classifications to manual review.

## Features

- Product import from Excel
- Shopify taxonomy import
- Product classification against 14,000+ Shopify categories
- Explainable category scoring
- Confidence scoring
- Manual-review workflow
- Alternative category suggestions
- Product attribute matching
- Product dashboard
- Product detail page
- Classification API
- Category search API
- Manual category approval API
- Batch classification
- Resumable batch processing
- Failure handling for individual products
- Automated tests

## Requirements

- Python 3.13+
- Django 6.0.8
- MySQL
- Python virtual environment
- Product and Shopify taxonomy data files

## Setup

### Windows PowerShell

Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1