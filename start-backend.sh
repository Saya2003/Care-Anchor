#!/bin/bash

# Navigate to backend directory and start the server
cd backend && uvicorn main:app --reload --port 8000
