#!/bin/bash
if [ "$1" = 'test' ]; 
then
    python -m pytest tests/; 
else
    python -m uvicorn invoice_utils.web:app --host '0.0.0.0' --port ${PORT};
fi