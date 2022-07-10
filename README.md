# tesco-product-scrape

This project contains source code and supporting files for an AWS-based serverless application that scrapes product information from Tesco's website that you can deploy with the SAM CLI. It includes the following files and folders:

- functions - Code for the application's Lambda functions to check the value of, buy, or sell shares of a stock.
- statemachines - Definition for the state machine that orchestrates the stock trading workflow.
- template.yaml - A template that defines the application's AWS resources.

This application creates a mock stock trading workflow which runs on a pre-defined schedule (note that the schedule is disabled by default to avoid incurring charges). It demonstrates the power of Step Functions to orchestrate Lambda functions and other AWS resources to form complex and robust workflows, coupled with event-driven development using Amazon EventBridge.

## Pre-requisites

1. An AWS account
2. SAM CLI - [Install the SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
3. Python 3 - [Install Python 3](https://www.python.org/downloads/)
4. Docker - [Install Docker community edition](https://hub.docker.com/search/?type=edition&offering=community)
5. A JSON file named `"cbpro-api-secret.json"` containing your Coinbase Pro API key details ([instructions here to create API key](https://help.coinbase.com/en/pro/other-topics/api/how-do-i-create-an-api-key-for-coinbase-pro)) with the following structure:

    ```yaml
    {
        "secret": PUT_SECRET_HERE
        "key": PUT_KEY_HERE
        "passphrase": PUT_PASSPHRASE_HERE
    }
    ```
6. A JSON file named `"kucoin-api-secret.json"` containing your KuCoin API key details ([instructions here to create API key](https://www.kucoin.com/support/360015102174-How-to-Create-an-API)) with the following structure:

    ```yaml
    {
        "secret": PUT_SECRET_HERE
        "key": PUT_KEY_HERE
        "passphrase": PUT_PASSPHRASE_HERE
    }
    ```


## Configurations

The `template.yaml` contains the following user-defined global environment variables:

- `COINBASE_SECRET_KEY` - The filename of the JSON file which contains your Coinbase Pro API key, the structure of which is defined in the pre-requisites section above, set to `"cbpro-api-secret.json"` by default.
- `KUCOIN_SECRET_KEY` - The filename of the JSON file which contains your KuCoin API key, the structure of which is defined in the pre-requisites section above, set to `"kucoin-api-secret.json"` by default.
- `MONTHLY_FREQ` - How many times to buy in a month, set to `2` by default.
- `MONTHLY_FUND` - How much in £ to invest per month, set to `400` by default
- `RATIO_BTC` - Proportion of MONTHLY_FUND to invest in Bitcoin (BTC), set to `0.425` by default.
- `RATIO_ETH` - Proportion of MONTHLY_FUND to invest in Ethereum (ETH), set to `0.425` by default.
- `RATIO_OPCT` - Proportion of (1 - RATIO_BTC - RATIO_ETH) * MONTHLY_FUND to invest in Opacity (OPCT), set to `0.1` by default.
- `RATIO_TRAC` - Proportion of (1 - RATIO_BTC - RATIO_ETH) * MONTHLY_FUND to invest in Origin Trail (TRAC), set to `0.9` by default.


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
aws cloudformation delete-stack --stack-name tmp
```
