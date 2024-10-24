# Org AWS config Rules

| :exclamation: Single Account Test          |
|:---------------------------|
| **In order to manually test a single rule in a single region follow AWS documentation https://docs.aws.amazon.com/config/latest/developerguide/evaluate-config_manage-rules.html. this is recommended before implementing the rule at Org Level.** |

## Cloudformation template.

To enable an AWS Config rule with auto-remediation, please follow the steps below:

> 1. Create a New YAML File:
    - copy [rule.yaml.template]() into a new YAML file. Use a filename that refers to the control ID.
> 2. Access AWS Config Console:
    - Sign in to the AWS Management Console and open the AWS Config console at [AWS Config Console](https://console.aws.amazon.com/config/).
> 3.Select the Appropriate Region:
    - Ensure that the region selector is set to a region that supports AWS Config rules. For a list of supported regions, refer to the AWS Config Regions and Endpoints in the Amazon Web Services General Reference.
> 4. Add a New Rule:
    - In the left navigation, choose `Rules`.
    - On the Rules page, click `Add rule`.
> 5. Specify Rule Type:
    - On the Specify rule type page, filter the list of managed rules by typing in the search field. For example, type EC2 to find rules that evaluate EC2 resource types or periodic for rules that are triggered periodically.
> 6. Configure the Rule:
    - On the Configure rule page, copy the Managed rule name (e.g., RDS_INSTANCE_PUBLIC_ACCESS_CHECK). You will need this to replace <REPLACE-CONFIG-RULE-SOURCE> in your new YAML file.
    - For Name, provide a unique name for the rule and replace it in the new YAML file on line [ConfigRuleName](https://gitlab.fortra.com/cloudops/awsadmin/security/aws-config/org-aws-config-rules/-/blob/main/CFN/rule.yaml.template?ref_type=heads#L18).
    - For Description, add a description for the rule.
    - Each rule has different properties and input parameters. To identify these, use the S3 template link, replace THE_RULE_IDENTIFIER with Managed rule name http://s3.amazonaws.com/aws-configservice-us-east-1/cloudformation-templates-for-managed-rules/THE_RULE_IDENTIFIER.template. For example: http://s3.amazonaws.com/aws-configservice-us-east-1/cloudformation-templates-for-managed-rules/RDS_INSTANCE_PUBLIC_ACCESS_CHECK.template. replace [ComplianceResourceTypes](https://gitlab.fortra.com/cloudops/awsadmin/security/aws-config/org-aws-config-rules/-/blob/main/CFN/rule.yaml.template?ref_type=heads#L18) with the required scope for the rule.

### Default Parameters:
| :exclamation: NOTE          |
|:---------------------------|
| **No changes are needed for these parameters.** |

```
          AccountId:
            type: String
            default: !Sub ${AWS::AccountId}
          Region:
            type: String
            default: !Sub ${AWS::Region}
          Partition:
            type: String
            default: "aws" < It may required to be change in the future if we are deployin on China or Gov regions.
          AutomationAssumeRole:
            type: String
            default: !Sub 'arn:aws:iam::${AWS::AccountId}:role/${AutomationRoleName}'
          GetTagsLambda:
            type: String
            default: !Sub "arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:FTA-GetTagsbyResource"
          GetInventoryLambda:
            type: String
            default: !Sub "arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:FTA-GetAccountInventory"
          ExclusionTable:
            type: String
            default: "arn:aws:dynamodb:us-east-1:412090077236:table/FTA-resource-tags-exclusion-5d9747"
          InventoryTable:
            type: String
            default: "arn:aws:dynamodb:us-east-1:412090077236:table/FTA-Account-Inventory-f74cd8"
          QuickSightS3:
            type: String
            default: "quick-sight-report-exclusion-622c56"
```

### Rule parameters
| :exclamation: NOTE          |
|:---------------------------|
| **Parameters such as GroupId or DBInstance depend on the type of rule you are deploying. These need to be added in multiple places.** |

### Auto Remediation

To enable auto-remediation, please follow the steps outlined below:

> 1. For every new auto-remediation action that will execute on a resource not covered by any previous rules, it is mandatory to update the auto-remediation role (FTA-ConfigAutoRemediation). This change must be made in the [iam.yaml](https://gitlab.fortra.com/cloudops/awsadmin/security/fortra_org_roles/-/blob/main/ORG_CFN/iam.yaml?ref_type=heads#L265)
> 2. Sign in to the AWS Management Console and open the AWS Config console at https://console.aws.amazon.com/systems-manager/.
3. Execute Automation:
    - In the left navigation menu, click on Automation under Change Management.
    - Click on Execute Automation.
> 4. Filter Automation Runbook:
    - In the Automation runbook search bar, filter by the document required for your Config Rule.
    - Copy the necessary content into the new YAML file under the [content](https://gitlab.fortra.com/cloudops/awsadmin/security/aws-config/org-aws-config-rules/-/blob/main/CFN/rule.yaml.template?ref_type=heads#L19) section.
> 5. Define Mandatory Actions:
    - Under the mainsteps block, include the following mandatory actions:
        - InvokeMyLambdaFunction: This Lambda function retrieves resource tags and returns either `Excluded` or `NotExcluded` as output.
        - LambdaOutputCheck: This Lambda function determines the next steps based on the input from `InvokeMyLambdaFunction`.
        - PublishExcludeLambda: This Lambda function publishes the resource information to the excluded folder in S3.
        - PublishRemediationLambda: This Lambda function publishes the resource information to the remediated folder in S3.

### specific parameters
| :exclamation: NOTE          |
|:---------------------------|
| **Parameters described below need to be updated based on each r** |

> 1. `AwsService` Needs to match the service portion of the resource ARN [ARN format](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference-arns.html)
> 2. `ResourceType` Needs to match the resource-type portion of the resource ARN, there are some resources that do not use resource-type, leave empty if not required
> 3. `ControlId` Needs to match the control that needs to be remediated
> 4. `ResourceId` ResourceId that is going to be remediated, this will depends of the rule we are implementing, it will change across the rules.
```
    AwsService:
        type: String
        default: 'ec2'
    ResourceType:
        type: String
        default: 'security-group'
    ControlId:
        type: String
        default: "EC2.14"
    ResourceId:
        type: String
        description: (Required) Security Group ID
        allowedPattern: ^([s][g]\-)([0-9a-f]){1,}$
```

### LambdaOutputCheck
| :exclamation: NOTE          |
|:---------------------------|
| **You must update the `NextSteps` and default behavior of this action as described below:** |

```
- name: LambdaOutputCheck
  action: aws:branch
  inputs:
    Choices:
    - NextStep: <Action when is resource is not excluded and needs to be remediated>
      Variable: "{{InvokeMyLambdaFunction.Payload}}"
      StringEquals: "NotExcluded"
    - NextStep: <Action when is resource is excluded>
      Variable: "{{InvokeMyLambdaFunction.Payload}}"
      StringEquals: "Excluded"
    Default:
      <Default action>
```

## Useful Documents

- [Implement AWS Config rule remediation with Systems Manager Change Manager](https://aws.amazon.com/blogs/mt/implement-aws-config-rule-remediation-with-systems-manager-change-manager/)
- [Creating AWS Config Managed Rules With AWS CloudFormation Templates](https://docs.aws.amazon.com/config/latest/developerguide/aws-config-managed-rules-cloudformation-templates.html)
- [Services that support the Resource Groups Tagging API](https://docs.aws.amazon.com/resourcegroupstagging/latest/APIReference/supported-services.html)