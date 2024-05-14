# Org AWS config Rules



## Config Rule

In order to enable AWS Config rule with autoremediation please follow below procedure:

- copy [rule.yaml.template]() in a new yaml file, use a file name that refers to the config rule.
- Sign in to the AWS Management Console and open the AWS Config console at https://console.aws.amazon.com/config/.
- In the AWS Management Console menu, verify that the region selector is set to a region that supports AWS Config rules. For the list of supported regions, see AWS Config Regions and Endpoints in the Amazon Web Services General Reference.
- In the left navigation, choose Rules.
- On the Rules page, choose Add rule.
- On the Specify rule type page, specify the rule type by completing the following steps:
    - Type in the search field to filter the list of managed rules by rule name, description, and label. For example, type EC2 to return rules that evaluate EC2 resource types or type periodic to return rules that are triggered periodically.

- On the Configure rule page, copy Managed rule name. For example RDS_INSTANCE_PUBLIC_ACCESS_CHECK you will need that to replace it in 
- For Name, use an unique name for the rule and replace it in the new yaml on line [ConfigRuleName](https://gitlab.fortra.com/cloudops/awsadmin/security/aws-config/org-aws-config-rules/-/blob/main/CFN/rule.yaml.template?ref_type=heads#L14).
- For Description, add a description for the rule.
- Each rule has different properties and input parameters in order to identify those use the S3 template link, replace THE_RULE_IDENTIFIER with Managed rule name http://s3.amazonaws.com/aws-configservice-us-east-1/cloudformation-templates-for-managed-rules/THE_RULE_IDENTIFIER.template. For example: http://s3.amazonaws.com/aws-configservice-us-east-1/cloudformation-templates-for-managed-rules/RDS_INSTANCE_PUBLIC_ACCESS_CHECK.template. replace [ComplianceResourceTypes](https://gitlab.fortra.com/cloudops/awsadmin/security/aws-config/org-aws-config-rules/-/blob/main/CFN/rule.yaml.template?ref_type=heads#L14) with the scope required for the rule.

#### Note  

| :exclamation: NOTE          |
|:---------------------------|
| **Any other parameter required for the rule needs to be added to the yaml file..** |

|-----------------------------------------|

### Auto Remediation

To enable autoremediation follow below procedure:

- For every new autoremediation action that will execute actions in a resource that is not in any other previous rule is mandatory to update the autoremediation role (FTA-ConfigAutoRemediation) that change needs to happen in [iam.yaml](https://gitlab.fortra.com/cloudops/awsadmin/security/fortra_org_roles/-/blob/main/ORG_CFN/iam.yaml?ref_type=heads#L265)
- Sign in to the AWS Management Console and open the AWS Config console at https://console.aws.amazon.com/systems-manager/.
- In the left navigation menu, click on Automation under Change management.
- Click on Execute automation.
- On the Automation runbook search bar filter by the document you need for your Config Rule.
- Copy the document name. For example AWSConfigRemediation-DisablePublicAccessToRDSInstance and replace it in [TargetId](https://gitlab.fortra.com/cloudops/awsadmin/security/aws-config/org-aws-config-rules/-/blob/main/CFN/rule.yaml.template?ref_type=heads#L37) in the yaml file.



## Useful Documents

- [Implement AWS Config rule remediation with Systems Manager Change Manager](https://aws.amazon.com/blogs/mt/implement-aws-config-rule-remediation-with-systems-manager-change-manager/)
