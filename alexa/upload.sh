#!/bin/bash
echo "AWS Lambda Update"
zip -9r ZipFiles/upload.zip lambda_function.py passwd.txt requests/* requests-2.11.1.dist-info/*
aws lambda update-function-code --function-name arn:aws:lambda:us-east-1:834695880484:function:light --zip-file fileb://ZipFiles/upload.zip --region us-east-1
rm ZipFiles/upload.zip
echo "Done!!"
