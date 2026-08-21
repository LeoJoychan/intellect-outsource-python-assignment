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

## Candidate Questions

### 1. How are products automatically mapped to Shopify categories, attributes, and values?

Products are classified using an explainable scoring approach against the imported Shopify taxonomy.

The classifier uses available product fields such as name, product category, sub-category, description, bullets, set contents, and materials. Strong product-type matches receive higher scores, while unsupported or conflicting category qualifiers are penalized.

Once the best category is selected, the classifier checks the attributes and attribute values associated with that category against the product data.

### 2. What happens when a product has a title but no description or image?

The classifier continues using the remaining available product information, including the product name, category, sub-category, materials, bullets, and other populated fields.

Missing descriptions and images do not cause the product to fail classification.

If the available evidence is insufficient to reach the configured confidence threshold, the result is stored as `manual_review`.

### 3. How could product images improve classification?

Images can provide additional visual evidence when textual product data is incomplete.

In a production implementation, an image-capable model could be used to identify visual characteristics such as product type, shape, upholstery, color, or other visible attributes. The visual result could then be combined with the existing text-based classifier.

The current implementation stores product image URLs and safely handles missing or invalid images, but does not perform image/vision-based classification.

### 4. How would the system process more than 10,000 products?

The current batch command processes products incrementally and skips products that already have classifications, allowing interrupted processing to resume.

For larger production workloads, processing could be moved to background workers such as Celery with Redis. Multiple workers could process independent products concurrently, while database indexes, controlled batch sizes, retry handling, and throughput monitoring could improve performance.

The classifier itself is kept as a service so that the processing mechanism can be changed without rewriting the classification logic.

### 5. How is the Shopify taxonomy represented in the database?

Shopify categories are stored as `ShopifyCategory` records with their Shopify ID, name, full name, level, vertical, and parent category.

Categories have a self-referencing parent relationship to represent the taxonomy hierarchy.

Category-to-attribute relationships are represented using a many-to-many relationship between `ShopifyCategory` and `ShopifyAttribute`.

Attribute values are stored separately and reference their parent `ShopifyAttribute`.

### 6. How is the confidence score calculated?

The classifier ranks candidate categories using an explainable score based on matching product information.

The highest-scoring candidate is compared with the second-highest candidate. The resulting score separation is used to calculate the classification confidence.

The selected category, confidence, explanation, candidate scores, and matched attributes are stored with the classification.

### 7. What happens when confidence is too low?

Low-confidence classifications are assigned the `manual_review` status rather than being treated as reliable automatic classifications.

The system preserves the selected category, confidence, explanation, alternatives, and matched attributes so that a reviewer has enough information to make a decision.

A manual approval API allows the reviewer to select and approve a category.

### 8. How are broken or inaccessible image URLs handled?

Image URLs are stored as product data, but image loading is not required for the text-based classifier.

The product detail page handles missing images and displays the available URL information without allowing a broken image to prevent the page from loading.

### 9. How would the API and database interact?

The Django application uses the database as the persistent source of product, taxonomy, and classification data.

The classification API retrieves a product, runs the classifier, and returns the classification result.

The category search API searches the imported taxonomy.

The manual approval API updates the stored product classification with the approved category and status.

### 10. How would 10,000 products be processed if an external request took approximately two seconds?

A sequential implementation would take approximately 20,000 seconds, or about 5.6 hours, before considering overhead.

For production, products should therefore be processed asynchronously using a worker queue. Independent products can be processed concurrently while respecting the external service's rate limits.

Caching, batching where supported, retries with backoff, connection reuse, and storing results incrementally would further reduce unnecessary work and make failures recoverable.

### 11. How would processing resume if the job stopped after 6,000 products?

The batch classifier excludes products that already have a `ProductClassification`.

Because classifications are saved incrementally, successfully processed products remain complete in the database. Restarting the command therefore processes only products that do not yet have a classification.

Individual failures are caught and reported without stopping the remaining products.

### 12. Why were these technologies chosen?

Python and Django provide the application framework, ORM, management commands, templates, and API functionality.

MySQL provides persistent relational storage for products, classifications, and the Shopify taxonomy.

The classification logic is separated into a service class so it can be tested independently of the web interface and batch command.

### 13. What is the high-level architecture?

The application is organized into several layers:

- Django views and templates provide the web interface.
- Django APIs expose classification, category search, and approval operations.
- `ProductClassifier` contains the classification logic.
- Management commands handle product import, taxonomy import, and batch classification.
- The `products` application stores products and classifications.
- The `taxonomy` application stores Shopify categories, attributes, and attribute values.
- MySQL provides persistent storage.

This separation allows the same classification service to be used by the web interface, APIs, tests, and batch processing.

### 14. What is the estimated development effort?

A reasonable implementation estimate for a production-ready version is approximately:

| Task | Estimated effort |
|---|---:|
| Django project and database setup | 3–4 hours |
| Product import and validation | 3–4 hours |
| Shopify taxonomy import and relationships | 5–7 hours |
| Classification algorithm | 8–12 hours |
| Attribute/value matching | 4–6 hours |
| Confidence and manual-review workflow | 3–4 hours |
| Dashboard and product detail UI | 4–6 hours |
| API endpoints | 3–4 hours |
| Batch processing and failure handling | 4–6 hours |
| Automated tests | 5–7 hours |
| Documentation and deployment preparation | 2–3 hours |
| **Estimated total** | **44–63 hours** |

A production implementation with external AI/image services, asynchronous workers, monitoring, deployment, and additional performance testing would require additional time.

## Important Notes

The `.env` file contains local database credentials and should not be committed to version control.

The provided product and Shopify taxonomy data files are required for importing and classifying the dataset.

For production deployment, database credentials, secret keys, and other environment-specific settings should be supplied through environment variables.