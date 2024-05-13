pipeline {
    agent {
        ecs {
            inheritFrom 'terraform-inbound-agent'
        }
    }
    stages {
        stage('Template upload') {
            steps {
                script {
                    sh '''aws s3 cp CFN/ s3://fta-cloudformation-templates-us-east-1/aws-org-config-rules --recursive'''
                }
                sh 'echo CFN templates uploaded'
            }
        }
        stage('Update Stackset') {
            steps {
                script {
                    sh '''aws cloudformation update-stack-set --stack-set-name FTA-Org-AWS-Config-Rules \
                    --template-body file://CFN/base.yaml --capabilities CAPABILITY_NAMED_IAM \
                    --managed-execution Active=true --region us-east-1 \
                    --operation-preferences FailureTolerancePercentage=100,MaxConcurrentCount=30,RegionConcurrencyType=PARALLEL'''
                }
                sh 'echo stackset update is done'
            }
        }
    }
}
