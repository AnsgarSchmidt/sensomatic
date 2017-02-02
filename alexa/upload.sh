#!/bin/bash
echo "AWS Lambda Update"
zip -9r ZipFiles/upload.zip passwd.txt lambda_function.py requests/* requests-2.11.1.dist-info/*
aws lambda update-function-code --function-name arn:aws:lambda:eu-west-1:834695880484:function:jarvistest --zip-file fileb://ZipFiles/upload.zip --region eu-west-1
rm ZipFiles/upload.zip
echo "Done!!"
