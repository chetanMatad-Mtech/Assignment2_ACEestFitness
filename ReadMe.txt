FitNess Management System – Testing Guide

This document explains how to update and run the unit tests defined in
test_application.py.
The tests are executed both locally and automatically in the CI/CD
pipeline.

NOTE: MASTER Branch is used for deployment 
------------------------------------------------------------------------
-   application.py contains a basic python based brouser using Flask
    index.html contains title body and 2 url pages
    members.html and register.html
    members.html holds the objects for each of them 
    register.html gives pages to register
-   test_application.py – Contains Pytest-based unit tests for
    validating the core functionality of the Flask fitness management
    application.

------------------------------------------------------------------------

Running Tests Locally

1. Install dependencies
    pip install -r requirements.txt

2. Run application
   python application.py
   This opens the webbased in loop back address of http://127.0.0.1:5000

3. Run py test
    pytest -v

4. Run a specific test
    pytest -v test_application.py::test_example_feature

5.  Build the Docker image:
	This was tried in linux machine to use as 2 user 
        docker build -t aceest-fitness-app .
        If you face network bridge issue 
        sudo docker build --network=host -t aceest-fitness-app .

6.  Run tests inside the container:
        docker run --rm aceest-fitness-app pytest -v

------------------------------------------------------------------------

-   Tests in test_application.py are executed automatically on every
    push to GitHub via GitHub Actions.

-   The workflow file is located at:

        .github/workflows/CI_CDPipeline.yml

-   If tests fail, the pipeline will stop and prevent deployment.

------------------------------------------------------------------------

