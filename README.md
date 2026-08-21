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
```

### Database Configuration

Create a `.env` file in the project root with the MySQL connection settings:

```env
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=3306
```

Apply the database migrations:

```powershell
python manage.py migrate
```

Check the Django configuration:

```powershell
python manage.py check
```

## Import Product Data

The project includes the provided Excel dataset:

`data/Product List.xlsx`

Import the products with:

```powershell
python manage.py import_products
```

The provided dataset contains 4,999 products.

## Import Shopify Taxonomy

The Shopify taxonomy files are located in:

`data/shopify_taxonomy/`

Import the taxonomy with:

```powershell
python manage.py import_taxonomy
```

The provided taxonomy contains:

- 8,240 Shopify attributes
- 74,820 attribute values
- 14,606 Shopify categories

The taxonomy importer can be run repeatedly without creating duplicate records.

For a fresh taxonomy import:

```powershell
python manage.py import_taxonomy --clear
```

Use `--clear` only when you intentionally want to remove the existing taxonomy before importing it again.

## Batch Product Classification

Classify a limited number of products:

```powershell
python manage.py classify_products --limit 50
```

Process all currently unclassified products:

```powershell
python manage.py classify_products
```

The batch classifier:

- Processes products in ID order
- Skips products that already have a classification
- Saves results as products are processed
- Continues when an individual product fails
- Reports classified, manual-review, and failed products
- Preserves manual-review results
- Can be interrupted and resumed

Because already-classified products are excluded, running the command again resumes from the remaining products.

## Classification Approach

Products are matched against the Shopify taxonomy using an explainable scoring system.

The classifier considers:

- Product name
- Product sub-category
- Product category
- Bullets
- Set contents
- Materials
- Description

Product name and explicit product-type matches receive stronger weighting.

The classifier also penalizes unsupported or overly specific category qualifiers when the product data does not provide evidence for them.

The stored classification includes:

- Selected category
- Confidence score
- Explanation
- Alternative category candidates
- Matched product attributes

## Confidence and Manual Review

The classifier compares the highest-scoring category with the second-highest candidate to calculate confidence.

Results below the configured confidence threshold are assigned to:

`manual_review`

Higher-confidence results are treated as classified.

Manual-review results remain stored in the database for later review or approval.

## Dashboard

The dashboard is available at:

`/`

The dashboard provides an overview of products and their classification status.

Individual product details are available through the product detail page.

## API

The API is available under:

`/api/`

The project includes APIs for:

- Product classification
- Category search
- Manual category approval

## Testing

Run the complete test suite:

```powershell
python manage.py test
```

Run Django system checks:

```powershell
python manage.py check
```

The automated tests cover classification, API behavior, batch processing, failure handling, and taxonomy importing.

The taxonomy importer also has regression coverage to verify that it can be executed repeatedly without creating duplicate taxonomy records.

## Performance and Scalability

The application has been tested against the provided 4,999-product dataset.

Batch classification is resumable because already-classified products are excluded from later runs.

The batch command processes products incrementally rather than loading the entire dataset into memory.

The unclassified-product query uses the product/classification relationship and orders products by ID.

For larger datasets such as 10,000+ products, additional optimization could include:

- Database indexing
- Batch-size tuning
- Background job processing
- Parallel processing where appropriate
- Additional query optimization
- Classification throughput monitoring

## Dataset Verification

The provided dataset has been verified with:

- 4,999 products
- 4,999 product classifications
- 14,606 Shopify categories
- 8,240 Shopify attributes
- 74,820 Shopify attribute values

The full product dataset has been processed.

Uncertain classifications are preserved for manual review.

## Project Structure

```text
intellect-outsource-assignment/
├── config/
├── data/
│   ├── Product List.xlsx
│   └── shopify_taxonomy/
├── products/
│   ├── management/
│   │   └── commands/
│   ├── services/
│   │   └── classifier.py
│   ├── templates/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── tests.py
├── taxonomy/
│   ├── management/
│   │   └── commands/
│   ├── models.py
│   ├── views.py
│   └── tests.py
├── manage.py
├── README.md
└── .env
```

## Important Notes

The `.env` file contains local database credentials and should not be committed to version control.

The provided product and Shopify taxonomy data files are required for importing and classifying the dataset.

For production deployment, database credentials, secret keys, and other environment-specific settings should be supplied through environment variables.