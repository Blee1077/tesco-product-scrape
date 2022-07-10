# Tesco website product scraper
[![forthebadge](https://forthebadge.com/images/badges/made-with-python.svg)](https://forthebadge.com) [![forthebadge](https://forthebadge.com/images/badges/designed-in-etch-a-sketch.svg)](https://forthebadge.com)

:warning: This application requires a UK-based residential proxy as Tesco's website blocks access based on IP addresses :warning:

The purpose of this project is to create an AWS-based serverless application that scrapes product pricing and category details from Tesco's website. The core functionality is an AWS Step Function that runs AWS Lambda functions in a sequence and is scheduled to run on a user-defined frequency using an EventBridge rule, AWS SAM is used to create all the necessary AWS resources to get this application up and running. In the event that the state machine fails, an alarm will be sent to the email used to set up SNS notifications.

At its core, the application consists of seven Lambda functions, a Lambda layer containing commonly used functions across the functions, a Step Function which orchestrates the pipeline, and an AWS SAM template which creates and deploys all the AWS resources. These are contained in the following riles and folders:

- functions - Folder containing subfolders, which of which contains code for a Lambda function.
- statemachines - Definition for the state machine that orchestrates the product scraping pipeline.
- util_layer - Utility functions that are shared across Lambda functions.
- template.yaml - A template that defines the application's AWS resources.

## Pre-requisites

1. An AWS account
2. SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
3. Python 3 - [Install Python 3](https://www.python.org/downloads/)
4. Docker - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)
6. A JSON file named named `"sock5_proxy.json"` containing email details with the following structure:

    ```yaml
    {
        "username": "PUT_USERNAME_HERE"           # Username for proxy as string
        "password": "PUT_PASSWORD_HERE"           # Password for proxy as string
        "address": "PUT_IPv4_PROXY_ADDRESS_HERE"  # IPv4 proxy address as string
        "port": PUT_PROXY_SERVER_PORT_HERE        # Port number needed to communicate with proxy server as integer
        "expiry": "PUT_PROXY_EXPIRY_DATE_HERE"    # Expiry date of proxy in "YYYY-MM-DD" format as string
    }

## Configurations

The `template.yaml` contains the following user-defined global environment variables:

- `PROXY_DETAILS_KEY` - The filename of the JSON file which contains your Coinbase Pro API key, the structure of which is defined in the pre-requisites section above, set to `"sock5_proxy.json"` by default.
- `USER_AGENTS_KEY` - The filename of the pickle file which contains a list of user agents to use when making URL requests.


## Use the SAM CLI to build locally

The Serverless Application Model Command Line Interface (SAM CLI) is an extension of the AWS CLI that adds functionality for building and testing Lambda applications. It uses Docker to run your functions in an Amazon Linux environment that matches Lambda. It can also emulate your application's build environment and API.

Build this application with the `sam build --use-container` command. The `use-container` option makes it so that the build happens inside a Lambda-like container.

```bash
sam build --use-container
```

For each of the Lambda functions, the SAM CLI installs dependencies defined in `requirements.txt`, creates a deployment package, and saves it in the `.aws-sam/build` folder.

## Deploy the application

To deploy the application for the first time, run the following command in your shell after building:

```bash
sam deploy --guided
```

This command will package and deploy this application to AWS, with a series of prompts:

* **Stack Name**: The name of the stack to deploy to CloudFormation. This should be unique to your account and region, and a good starting point would be something matching this project's function.
* **AWS Region**: The AWS region you want to deploy this app to.
* **SNS Email Parameter**: The email address to send execution failure notifications.
* **Confirm changes before deploy**: If set to yes, any change sets will be shown to you before execution for manual review. If set to no, the AWS SAM CLI will automatically deploy application changes.
* **Allow SAM CLI IAM role creation**: Many AWS SAM templates, including this one, create AWS IAM roles required for the AWS Lambda function(s) included to access AWS services. By default, these are scoped down to minimum required permissions. To deploy an AWS CloudFormation stack which creates or modifies IAM roles, the `CAPABILITY_IAM` value for `capabilities` must be provided. If permission isn't provided through this prompt, to deploy this example you must explicitly pass `--capabilities CAPABILITY_IAM` to the `sam deploy` command.
* **Save arguments to samconfig.toml**: If set to yes, your choices will be saved to a configuration file inside the project, so that in the future you can just re-run `sam deploy` without parameters to deploy changes to this application.

You can find more information and examples about filtering Lambda function logs in the [SAM CLI Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-logging.html).

## Cleanup

To delete the sample application that you created, use the AWS CLI. Assuming you used your project name for the stack name, you can run the following:

```bash
aws cloudformation delete-stack --stack-name tesco-product-scrape
```
