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
        stage('Terraform init') {
            steps {
                script {
                    sh "echo terraform init"
                    sh 'terraform init'
                }
                sh 'echo terraform init is done'
            }
        }
        stage('Terraform plan') {
            steps {
                script {
                    sh "echo starting terraform plan"
                    sh 'terraform plan'
                }
                sh 'echo terraform plan is done'
            }
        }
        stage('Terraform apply') {
            steps {
                script {
                    sh "echo terraform apply"
                    sh 'terraform apply --auto-approve'
                }
                sh 'echo terraform apply is done'
            }
        }
    }
}
